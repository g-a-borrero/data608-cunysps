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

# This gives us the total number of households in NYC based on household size # Works
nyc_hhs = pd.read_excel("data/DEC_00_SF4_HCT005 (1).xls")
nyc_hhs = nyc_hhs.iloc[4:,[0,2]]
nyc_hhs.rename(columns={list(nyc_hhs)[0]: "Household Size", list(nyc_hhs)[1]:"Number of Households"}, inplace=True)

