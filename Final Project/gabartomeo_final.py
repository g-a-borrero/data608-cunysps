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
ny_ami[0].columns = ["Family Size"] + [i.replace("of", "of ") for i in ny_ami[0].columns[1:]]

# This gives us the total number of households in NYC based on household size in 2000 # Works
nyc_hhs = pd.read_excel("data/DEC_00_SF4_HCT005 (1).xls")
nyc_hhs = nyc_hhs.iloc[4:,[0,2]]
nyc_hhs.columns = ["Household Size", "Number of Households"]

# This gives us the number of individuals living in NYC during the 2000 Census # Works
nyc_census_summary = pd.read_html("https://www1.nyc.gov/site/planning/data-maps/nyc-population/census-summary-2000.page")[0]
nyc_census_summary = nyc_census_summary.iloc[1:, [0,3]]
nyc_census_summary.columns = ["Boroughs", "Population in 2000"]

# This gives us the income per household # Works
nyc_income_by_agi = pd.read_json("https://data.cityofnewyork.us/resource/ipc3-2nbm.json")
nyc_income_by_agi.columns = ["%", "average income per filer"] + [i.replace("_", " ") for i in nyc_income_by_agi.columns[2:]]
nyc_income_by_agi.columns = [i.replace("minimun", "minimum").title() for i in nyc_income_by_agi.columns]
nyc_income_by_agi = nyc_income_by_agi[list(nyc_income_by_agi)[2:] + list(nyc_income_by_agi)[:2]]
nyc_income_by_agi.fillna(0, inplace=True)

# This gives us the number of extremely low income units by borough # Works
nyc_eli_units = pd.read_json("https://data.cityofnewyork.us/resource/hg8x-zxpr.json?$select=borough,sum(extremely_low_income_units)&$group=borough")
nyc_eli_units.columns = ["Borough", "Extremely Low Income Units"]

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
			]
		}
	)
])

if __name__ == '__main__':
    app.run_server(debug=True)