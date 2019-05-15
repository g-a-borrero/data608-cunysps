import pandas as pd
import numpy as np
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import plotly.plotly as py
import plotly.graph_objs as go
import re

##################
# IMPORTING DATA #
##################

# This gives us the three tables from the NYC AMI page. # Works
#    Table 0: Income by family size to be deemed some percentage of the AMI
#    Table 1: Categories of AMI based on percentages of the AMI
#    Table 2: Affordable rent for unit size by percentages of the AMI
ny_ami = pd.read_html("https://www1.nyc.gov/site/hpd/renters/area-median-income.page")
ny_ami[1].iloc[:,0] = ny_ami[1].iloc[:,0].str.replace("-", " ")
ny_ami[0].columns = ["Household Size"] + [i.replace("of", "of ") for i in ny_ami[0].columns[1:]]

# This gives us the total number of households in NYC based on household size in 2000 # Works
nyc_hhs = pd.read_excel("data/DEC_00_SF4_HCT005 (1).xls")
nyc_hhs = nyc_hhs.iloc[4:,[0,2]]
nyc_hhs.columns = ["Household Size", "Number of Households"]

# This gives us the number of individuals living in NYC during the 2000 Census # Works
nyc_census_summary = pd.read_html("https://www1.nyc.gov/site/planning/data-maps/nyc-population/census-summary-2000.page")[0]
nyc_census_summary = nyc_census_summary.iloc[1:, [0,3]]
nyc_census_summary.columns = ["Borough", "Population in 2000"]

# This gives us the income per household # Works
nyc_income_by_agi = pd.read_json("https://data.cityofnewyork.us/resource/ipc3-2nbm.json")
nyc_income_by_agi.columns = ["%", "average income per filer"] + [i.replace("_", " ") for i in nyc_income_by_agi.columns[2:]]
nyc_income_by_agi.columns = [i.replace("minimun", "minimum").title() for i in nyc_income_by_agi.columns]
nyc_income_by_agi = nyc_income_by_agi[list(nyc_income_by_agi)[2:] + list(nyc_income_by_agi)[:2]]
nyc_income_by_agi.iloc[:,0] = nyc_income_by_agi.iloc[:,0].str.strip()
nyc_income_by_agi.fillna(0, inplace=True)

# This gives us the number of extremely low income units by borough # Works
nyc_eli_units = pd.read_json("https://data.cityofnewyork.us/resource/hg8x-zxpr.json?$select=borough,sum(extremely_low_income_units)&$group=borough")
nyc_eli_units.columns = ["Borough", "Extremely Low Income Units"]


#################
# CHECKING DATA #
#################

# The Population by Household Size and the Population by 2000 Census. Only 300000 apart, but the final category
# for Household Size is 7 or more, not 7.
# print("Population calculated by Household Size: %d" % sum(nyc_hhs.iloc[1:,1].str.replace(',', '').astype('int64')*[1,2,3,4,5,6,7]))
# print("Population from 2000 Census: %s" % nyc_census_summary.iloc[0,1])

# The "Total" row for the Income per Household is wrong.
# The following prints: Listed Total: 3461521   Actual Total:3361521
#print("Listed Total: %s\tActual Total:%s" % (nyc_income_by_agi.iloc[10,2], sum(nyc_income_by_agi.iloc[:10,2])))



########################
# CALCULATED VARIABLES #
########################

# Step 1: Household Sizes as Percentages # Works
nyc_hhs_perc = pd.DataFrame(
	{
		"Household Size": nyc_hhs.iloc[1:,0].tolist(),
		"Percentage of Total": (nyc_hhs.iloc[1:,1].str.replace(',', '').astype('int64')/int(nyc_hhs.iloc[0,1].replace(',', ''))).tolist()
	}
)

# Step 2: Population of Boroughs as Percentages # Works
nyc_boro_perc = pd.DataFrame(
	{
		"Borough": nyc_census_summary.iloc[1:,0].tolist(),
		"Percentage of Total": (nyc_census_summary.iloc[1:,1].str.replace(',', '').astype('int64')/int(nyc_census_summary.iloc[0,1].replace(',', ''))).tolist()
	}
)

# Step 3: Multiply Step 1 by NYC AGI # Works
nyc_hhs_agi = pd.DataFrame(columns=["Household Size", "Income Group", "Minimum Income in Group", "Number of Filers"])

for hhs in range(len(nyc_hhs_perc)):
	for agi in range(len(nyc_income_by_agi)-1):
		nyc_hhs_agi.loc[len(nyc_hhs_agi)] = [
			nyc_hhs_perc.iloc[hhs,0], 
			nyc_income_by_agi.iloc[agi,0], 
			int(nyc_income_by_agi.iloc[agi,1]), 
			int(round(nyc_income_by_agi.iloc[agi,2]*(nyc_hhs_perc.iloc[hhs,1])))
		]

# Step 4: Use NY AMI tables to determine AMI for each from Step 3 # Works
nyc_ami = pd.DataFrame({"AMI Category": ny_ami[1].iloc[:,0].tolist() + ["Wealthy"], 
	"Number of Households": [0]*6
})
nyc_ami_unique = list(set(nyc_hhs_agi.iloc[:,2])) + [2000000]
nyc_ami_unique.sort()
for row in nyc_hhs_agi.itertuples():
	hhs = int(row[1].strip()[0])
	min_inc = int(row[3])
	next_min_inc = nyc_ami_unique[nyc_ami_unique.index(min_inc)+1]
	ppl = int(row[4])
	hhs_row = ny_ami[0].loc[ny_ami[0]["Household Size"] == hhs].iloc[:,1:].apply(lambda x: x.replace('[^.0-9]', '', regex=True).astype(int) >= min_inc, axis=1)
	inc_perc = hhs_row.idxmax(axis=1).to_string(index=False)
	max_inc = ny_ami[0].loc[ny_ami[0]["Household Size"] == hhs][inc_perc].replace('[^.0-9]', '', regex=True).astype(int).tolist()[0]
	inc_perc = int(re.sub('[^.0-9]', '', inc_perc))
	if (min_inc <= max_inc) and (next_min_inc <= max_inc):
		inc_index = ny_ami[1].iloc[:,1].str.findall("\d+").apply(lambda x: int(x[0]) <= inc_perc and int(x[1]) >= inc_perc).idxmax()
		nyc_ami.iloc[inc_index,1] += ppl
	else:
		ppl_1 = round((1-(min_inc/max_inc))*ppl)
		ppl_2 = ppl-ppl_1
		inc_index = ny_ami[1].iloc[:,1].str.findall("\d+").apply(lambda x: int(x[0]) <= inc_perc and int(x[1]) >= inc_perc).idxmax()
		nyc_ami.iloc[inc_index,1] += ppl_1
		inc_perc += 10
		inc_index = 5 if inc_perc > 160 else ny_ami[1].iloc[:,1].str.findall("\d+").apply(lambda x: int(x[0]) <= inc_perc and int(x[1]) >= inc_perc).idxmax()
		nyc_ami.iloc[inc_index,1] += ppl_2

# Step 5: Multipy Step 2 by Step 4 to get AMI Category by Borough
nyc_boro_ami = pd.DataFrame(columns=["Borough", "AMI Category", "Number of Households"])

for boro in range(len(nyc_boro_perc)):
	for ami in range(len(nyc_ami)):
		nyc_boro_ami.loc[len(nyc_boro_ami)] = [
			nyc_boro_perc.iloc[boro,0],
			nyc_ami.iloc[ami,0],
			int(round(nyc_boro_perc.iloc[boro,1]*nyc_ami.iloc[ami,1]))
		]


############
# DASH APP #
############

app = dash.Dash(__name__)

app.title = "Gabrielle Bartomeo's Final"

app.layout = html.Div([
	html.H1(children="Insufficient Rental Housing for Extremely Low Income Families in New York City"),
	html.H4(children="by Gabrielle Bartomeo"),
	html.P(children="This report seeks to explore the disparity in New York City between individuals with extremely low income and the number of units for rent labeled as affordable for them."),
	html.H2(children="How \"Extremely Low Income\" is Defined"),
	dash_table.DataTable(
		id="nyami1",
		columns=[{"name": i, "id": i} for i in ny_ami[1].columns],
		data=ny_ami[1].to_dict("records"),
		content_style= "fit",
		style_cell={
		"textAlign": "center"
		},
		style_header={'fontWeight': 'bold'},
		style_data_conditional=[{
			"if": {"row_index": 0},
			"backgroundColor": "#3D9970",
			"color": "white"
		}]
	),
	html.P(children="Individuals who make less than 30% of the Area Median Income (AMI) are said to be those who are of Extremely Low Income. The AMI is as its name suggests, the median income for an area as desginated by the US Federal Government. To determine this, the amount earned per year is compared to the family size."),
	dash_table.DataTable(
		id="nyami0",
		columns=[{"name": i, "id": i} for i in ny_ami[0].columns],
		data=ny_ami[0].to_dict("records"),
		content_style= "fit",
		style_cell={'textAlign': 'center'},
		style_header={'fontWeight': 'bold'},
		style_data_conditional=[{
			"if": {"column_id": "30% of AMI"},
			"backgroundColor": "#3D9970",
			"color": "white"
		}]
	),
	html.P(children="Here, the highlighted column displays the maximum amount of money a family may make to be considered extremely low income."),
	html.H2(children="Number of Extremely Low Income Families in New York City"),
	html.P(children="Before the gravity of the situation can truly be assessed, first the number of extremely low income families in New York City must be identified."),
	dcc.Graph(
		id="nychhsPie",
		style={'width': '49%', 'display': 'inline-block', 'vertical-align': 'middle'},
		figure={
			"data": [
			go.Pie(labels=nyc_hhs.iloc[1:,0].tolist(), 
				values=nyc_hhs.iloc[1:,1].str.replace(',', '').astype('int64').tolist())
			],
			"layout": go.Layout(
					title="Households in New York City by Size"
			)
		}
	),
	html.P(children="As can be seen, the majority of households in New York City are one and two person households. While there likely isn't a one-to-one ratio between the overall household distribution of the city and each individual borough, this can still be used to estimate the number of households per borough."),
	html.P(children="Another factor will be the number of extremely low income households in New York City, regardless of boro. Below is that graph."),
	dcc.Graph(
		id="nycamiPie",
		style={'width': '49%', 'display': 'inline-block', 'vertical-align': 'middle'},
		figure={
			"data": [
			go.Pie(labels=nyc_ami.iloc[:,0].tolist(), 
				values=nyc_ami.iloc[:,1].tolist())
			],
			"layout": go.Layout(
					title="Households in New York City by AMI"
			)
		}
	),
	html.P(children="The above pie chart shows that nearly half the city likely is of extremely low income, with a whopping 78.5% of the city being low income of some kind. In fact, a total of 1,528,797 households are extremely low income. If we assume (incorrectly) that there is an even distribution of wealth throughout the city, the boroughs end up looking something like this:"),
	dcc.Graph(
		id="nycboroamiBar",
		figure={
			"data": [go.Bar(x=nyc_boro_ami["Borough"].unique().tolist(), y=nyc_boro_ami.loc[nyc_boro_ami["AMI Category"] == ami]["Number of Households"].tolist(), name=ami) for ami in nyc_boro_ami["AMI Category"].unique().tolist()],
			"layout": go.Layout(
					title="Boroughs in New York City by AMI"
			)
		}
	),
	html.P(children="The majority of extremely low income households are in Brooklyn and Queens. Visualized another way, the distribution becomes a bit more evident."),
	dcc.Graph(
		id="nychhsamiBarStacked",
		figure={
			"data": [go.Bar(x=nyc_boro_ami["AMI Category"].unique().tolist(), y=nyc_boro_ami.loc[nyc_boro_ami["Borough"] == boro]["Number of Households"].tolist(), name=boro) for boro in nyc_boro_ami["Borough"].unique().tolist()],
			"layout": go.Layout(
					title="Boroughs in New York City by AMI",
					barmode="stack"
			)
		}
	),
	html.H2(children="Renting in the Center of the Universe"),
	html.P("When it comes to extremely low income households, many, if not all, will struggle or outright fail to own their own homes. As a result, the only other option for those who manage to keep off the streets and out of shelters is to rent. But does New York City manage to provide for its citizens?"),
	dash_table.DataTable(
		id="nyceliunits",
		columns=[{"name": i, "id": i} for i in nyc_eli_units.columns],
		data=nyc_eli_units.to_dict("records"),
		content_style= "fit",
		style_cell={
		"textAlign": "center"
		},
		style_header={'fontWeight': 'bold'}
	),
	html.P(children="Without even comparing directly, the answer is a clear, resounding \"No\". There is not enough housing in New York City for all of the extremely low income households. It only looks worse when compared side-by-side."),
	dcc.Graph(
		id="nycamiRentBar",
		figure={
			"data": [go.Bar(x=nyc_boro_ami["Borough"].unique().tolist(), y=nyc_boro_ami.loc[nyc_boro_ami["AMI Category"] == "Extremely Low Income"]["Number of Households"].tolist(), name="Extremely Low Income Households"), 
				go.Bar(x=nyc_eli_units["Borough"].unique().tolist(), y=nyc_eli_units.iloc[:,1].tolist(), name="Extremely Low Income Rentals", marker=dict(color='rgb(128,128,128)',))],
			"layout": go.Layout(
					title="Extremely Low Income Families vs Extremely Low Income Rentals by Borough"
			)
		}
	),
	html.H2(children="Conclusion"),
	html.P(children="New York City has a lot of extremely low income individuals, spread across households from 1 to more than 7 people each, spread across all of the boroughs. The truth of the matter is, with all of the extremely low income housing available in New York City, there's nowehere to house them. While shelters and programs like Section 8 exist, it is doubtful these measures are adequate for caring for those less fortunate New Yorkers trying to live their life on a dime. Without measures being implemented, these forgotten many will continue to struggle in silence to even have a roof over their heads, no less food in their stomachs.")
])

if __name__ == '__main__':
    app.run_server(debug=True)