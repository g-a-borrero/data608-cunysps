import pandas as pd
import numpy as np
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go

url = "https://data.cityofnewyork.us/resource/uvpi-gqnh.json"
boros = ["Bronx", "Brooklyn", "Manhattan", "Queens", "Staten Island"]
soql_url = "{0}?$select=spc_common,count(tree_id),health,steward&$where=boroname=\'{1}\'&$group=spc_common,health,steward"

try:
	trees_df is not None
except:	
	for boro in boros:
		soql_trees = pd.read_json(soql_url.format(url, boro.replace(" ","%20")))
		soql_trees["boroname"] = boro
		try:
			trees_df = trees_df.append(soql_trees)
		except:
			trees_df = soql_trees.copy()
	trees_df = trees_df.reset_index(drop=True)
	trees_df = trees_df.dropna(subset=["health", "spc_common"])
	trees_df["health"] = pd.Categorical(trees_df["health"], ["Poor", "Fair", "Good"])
	trees_df["steward"] = pd.Categorical(trees_df["steward"], ["None", "1or2", "3or4", "4orMore"])
	trees_df.sort_values(by="health",inplace=True)
	q1_df = trees_df.groupby(["boroname", "health", "spc_common"]).sum().reset_index()
	q1_df['count_tree_id'].fillna(value=0, inplace=True)
	q2_df = trees_df.groupby(["boroname", "health", "spc_common", "steward"]).sum().reset_index()
	q2_df['count_tree_id'].fillna(value=0, inplace=True)
	q2_df.sort_values(by=["health", "steward"], inplace=True)
	print(q2_df[q2_df['spc_common']=="American larch"])

app = dash.Dash(__name__)

app.layout = html.Div([
	html.H1(children='Question 1'),
	html.Div([
		dcc.Dropdown(
			id="q1-select-boro",
			options=[{'label': boro, 'value': boro} for boro in boros],
			value="Bronx"
			),
		dcc.Dropdown(
			id="q1-select-species",
			options=[{'label': tree_name, 'value': tree_name} for tree_name in sorted(q1_df.spc_common.unique(), key=str.lower)],
			value="Amur cork tree"
			)
		]),
    html.Div([
    	dcc.Graph(
            id='tree-health'
        )
    ]),
    html.H1(children='Question 2'),
    html.Div([
    	dcc.Graph(
            id='tree-stewards'
        )
    ])
])

@app.callback(
	dash.dependencies.Output('tree-health', 'figure'),
	[dash.dependencies.Input('q1-select-boro', 'value'),
	dash.dependencies.Input('q1-select-species', 'value')]
	)
def update_q1(q1_boro, q1_species):
	return {
	'data': [ go.Bar(
			x=q1_df[(q1_df['boroname']==q1_boro) & (q1_df['spc_common']==q1_species)]['health'],
			y=q1_df[(q1_df['boroname']==q1_boro) & (q1_df['spc_common']==q1_species)]['count_tree_id'],
			text=q1_df[(q1_df['boroname']==q1_boro) & (q1_df['spc_common']==q1_species)]['health'])
	],
	'layout': go.Layout(
		barmode="group",
		title="Health of {} trees in {}".format(q1_species, q1_boro)
		)
	}

@app.callback(
	dash.dependencies.Output('tree-stewards', 'figure'),
	[dash.dependencies.Input('q1-select-boro', 'value'),
	dash.dependencies.Input('q1-select-species', 'value')]
	)
def update_q2(q2_boro, q2_species):
	return {
	'data': [ go.Bar(
			x=q2_df[(q2_df['boroname']==q2_boro) & (q2_df['spc_common']==q2_species) & (q2_df['steward']==steward)]['health'],
			y=q2_df[(q2_df['boroname']==q2_boro) & (q2_df['spc_common']==q2_species) & (q2_df['steward']==steward)]['count_tree_id'],
			text=q2_df[(q2_df['boroname']==q2_boro) & (q2_df['spc_common']==q2_species) & (q2_df['steward']==steward)]['health'],
			name=steward) for steward in q2_df["steward"].unique()
	],
	'layout': go.Layout(
		barmode="group",
		title="Health of {} trees in {} by Number of Stewards".format(q2_species, q2_boro)
		)
	}

if __name__ == '__main__':
    app.run_server(debug=True)