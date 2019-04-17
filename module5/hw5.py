from flask import Flask, jsonify, send_from_directory, render_template
import pandas as pd

app = Flask(__name__)

@app.route('/hw/<string:treecontains>')
def return_tree_flags(treecontains):
	url = "https://data.cityofnewyork.us/resource/uvpi-gqnh.json"
	try:
		tree_names is not None
	except:
		find_trees_url = "{0}?$select=spc_common&$group=spc_common"
		tree_names = pd.read_json(find_trees_url.format(url))
		tree_names.dropna(inplace=True)
	trees_found = tree_names[tree_names["spc_common"].str.contains(treecontains, case=False)] # these are the trees
	if len(trees_found) == 0:
		return "Your query \"{0}\" returned no matches to any trees. Please try a new query.".format(treecontains)
	trees_info_url = "{0}?$select=spc_common,spc_latin,sidewalk,count(tree_id)&$where=spc_common in({1}) AND sidewalk IS NOT NULL&$group=spc_common,spc_latin,sidewalk"
	trees_formatted = trees_info_url.format(url, ", ".join("\'{0}\'".format(tree) for tree in list(trees_found["spc_common"])))
	trees_formatted = trees_formatted.replace(" ", "%20")
	trees_formatted = trees_formatted.replace("\'", "%27")
	tree_list = pd.read_json(trees_formatted)
	tree_list["Sidewalk Damage"] = tree_list[tree_list["sidewalk"]=="Damage"]["count_tree_id"]
	tree_list["No Sidewalk Damage"] = tree_list[tree_list["sidewalk"]=="NoDamage"]["count_tree_id"]
	tree_list.drop(["count_tree_id", "sidewalk"], axis=1, inplace=True)
	tree_list.fillna(0, inplace=True)
	tree_list = tree_list.groupby(["spc_common", "spc_latin"]).aggregate(sum)
	tree_list[["Sidewalk Damage", "No Sidewalk Damage"]] = tree_list[["Sidewalk Damage", "No Sidewalk Damage"]].astype("int")
	tree_list.reset_index(inplace=True)
	tree_list.rename(columns={"spc_common":"Common", "spc_latin":"Latin"}, inplace=True)
	tree_list["Common"] = pd.Categorical(tree_list["Common"], sorted(tree_list["Common"], key=str.lower))
	tree_list["Latin"] = pd.Categorical(tree_list["Latin"], sorted(tree_list["Latin"], key=str.lower))
	tree_list.sort_values(by=["Common", "Latin"], inplace=True)
	tree_json = {
	"Common": tree_list["Common"].tolist(),
	"Latin": tree_list["Latin"].tolist(),
	"Sidewalk Damage": tree_list["Sidewalk Damage"].tolist(),
	"No Sidewalk Damage": tree_list["No Sidewalk Damage"].tolist()
	}
	return jsonify(tree_json)



if __name__ == '__main__':
	app.run(debug=True)