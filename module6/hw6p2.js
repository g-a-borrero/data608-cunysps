var presidents = {};
var body = d3.select("body");
var body_HTML;

function enter_hit(some_value){
	var i = 1;
	for (i=1;i<=presidents.length;i++){
		if (some_value != "" && presidents[i]["Name"].startsWith(some_value)){
			new_text = "<p>President " + presidents[i]["Name"] + " was <b>" + Math.floor(presidents[i]["Height"]/12) + "\'" + presidents[i]["Height"]%12 + "\" tall</b> and weighed <b>" + presidents[i]["Weight"] + " pounds</b>!</p>";
			document.body.innerHTML = body_HTML + new_text;
			break;
		}
	}

};

d3.csv("https://raw.githubusercontent.com/gabartomeo/data608-cunysps/master/module6/data/presidents.csv", function(data){
	presidents=data;

	// PART ONE
	var table = body.append("table");
	var header = table.append("thead").append("tr");

	header
		.selectAll("th")
		.data(presidents.columns)
		.enter()
		.append("th")
		.text(function(d){
			return d;
		});

	var tablebody = table.append("tbody");

	rows = tablebody
		.selectAll("tr")
		.data(presidents)
		.enter()
		.append("tr");

	cells = rows
		.selectAll("td")
		.data(function(d){
			return Object.values(d);
		})
		.enter()
		.append("td")
		.text(function(d){
			return d;
		});

	// PART TWO

	body.append("p")
		.text("Enter a President's name and hit enter!");

	var input = body.append("input");

	input
		.attr("type", "text")
		.attr("name", "presname")
		.attr("id", "presname")
		.attr("value", "")
		.attr("onChange", "enter_hit(this.value)");

	body_HTML = document.body.innerHTML;
})