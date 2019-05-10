import pandas as pd
import numpy as np
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go

# This gives us the three tables from the NYC AMI page. # Works
# Table 0: Income by family size to be deemed some percentage of the AMI
# Table 1: Categories of AMI based on percentages of the AMI
# Table 2: Affordable rent for unit size by percentages of the AMI
ny_ami = pd.read_html("https://www1.nyc.gov/site/hpd/renters/area-median-income.page")

# This gives us the total number of households in NYC based on household size in 2000 # Works
nyc_hhs = pd.read_excel("data/DEC_00_SF4_HCT005 (1).xls")
nyc_hhs = nyc_hhs.iloc[4:,[0,2]]
nyc_hhs.columns = ["Household Size", "Number of Households"]

# This gives us the number of individuals living in NYC during the 2000 Census # Works
nyc_census_summary = pd.read_html("https://www1.nyc.gov/site/planning/data-maps/nyc-population/census-summary-2000.page")[0]
nyc_census_summary = nyc_census_summary.iloc[1:, [0,3]]
nyc_census_summary.columns = ["Boroughs", "Population in 2000"]