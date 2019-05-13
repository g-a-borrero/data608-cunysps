import pandas as pd
import numpy as np
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import plotly.plotly as py
import plotly.graph_objs as go

##################
# IMPORTING DATA #
##################

# This gives us the three tables from the NYC AMI page. # Works
#    Table 0: Income by family size to be deemed some percentage of the AMI
#    Table 1: Categories of AMI based on percentages of the AMI
#    Table 2: Affordable rent for unit size by percentages of the AMI
ny_ami = pd.read_html("https://www1.nyc.gov/site/hpd/renters/area-median-income.page")
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
nyc_income_by_agi.fillna(0, inplace=True)

# This gives us the number of extremely low income units by borough # Works
nyc_eli_units = pd.read_json("https://data.cityofnewyork.us/resource/hg8x-zxpr.json?$select=borough,sum(extremely_low_income_units)&$group=borough")
nyc_eli_units.columns = ["Borough", "Extremely Low Income Units"]


#################
# CHECKING DATA #
#################

# The Population by Household Size and the Population by 2000 Census. Only 30000,0 apart, but the final category
# For Household Size is 7 or more, not 7.
# print("Population calculated by Household Size: %d" % sum(nyc_hhs.iloc[1:,1].str.replace(',', '').astype('int64')*[1,2,3,4,5,6,7]))
# print("Population from 2000 Census: %s" % nyc_census_summary.iloc[0,1])


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

# Step 3: Multiply Step 1 by NYC AGI

#print(nyc_income_by_agi)
#print(nyc_income_by_agi.columns)


# print(len(nyc_hhs_perc)) # 7 rows
nyc_hhs_ami = pd.DataFrame(columns=["Household Size", "Income Group", "Minimum Income in Group", "Number of Filers"])

"""for hhs in range(len(nyc_hhs_perc)):
	for perc in range(len(nyc_hhs_perc)):
		for agi in range(len(nyc_income_by_agi)-1):
			nyc_hhs_ami.loc[len(nyc_hhs_ami)] = [nyc_hhs_perc.iloc[hhs,0], nyc_income_by_agi.iloc[agi,0], int(nyc_income_by_agi.iloc[agi,1]), int(round(nyc_income_by_agi.iloc[agi,2]*(nyc_hhs_perc.iloc[perc,1]+1)))]"""

# THIS FOR LOOP IS WRONG
for hhs in range(len(nyc_hhs_perc)):
	for agi in range(len(nyc_income_by_agi)-1):
		nyc_hhs_ami.loc[len(nyc_hhs_ami)] = [
			nyc_hhs_perc.iloc[hhs,0], 
			nyc_income_by_agi.iloc[agi,0], 
			int(nyc_income_by_agi.iloc[agi,1]), 
			int(round(nyc_income_by_agi.iloc[agi,2]*(nyc_hhs_perc.iloc[hhs,1])))
		]	

#print(nyc_hhs_ami)
#print(nyc_hhs_perc)
# print(nyc_hhs_perc.iloc[:,3]*) # fix this too
print(sum(nyc_hhs_ami.iloc[:,3])) # this is too far off from...
print(nyc_income_by_agi.iloc[10,:3]) # ... this


############
# DASH APP #
############

app = dash.Dash(__name__)

app.title = "Gabrielle Bartomeo's Final"

app.layout = html.Div([
	html.H1(children="Insufficient Rental Housing for Extremely Low Income Families in New York City"),
	html.P(children="This report seeks to explore the disparity in New York City between individuals with extremely low income and the number of units for rent labeled as affordable for them."),
	html.H2(children="How Extremely Low Income is Defined"),
	dash_table.DataTable(
		id="nyami1",
		columns=[{"name": i, "id": i} for i in ny_ami[1].columns],
		data=ny_ami[1].to_dict("records"),
		content_style= "fit",
		style_cell={
		"textAlign": "center"
		},
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
	html.P(children="As can be seen, the majority of households in New York City are one and two person households. While there likely isn't a one-to-one ratio between the overall household distribution of the city and each individual borough, this can still be used to estimate the number of households per borough.")
])

if __name__ == '__main__':
    app.run_server(debug=True)