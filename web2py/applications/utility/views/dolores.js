
if (!data)
    var data = [[1,1],
                [2,2],
	        [4,4],
                [10,10]];
    
if (!screen_bounds)
    var screen_bounds = [6000,2000];
var data_bounds;
var screenified_data;
if (!padding)
    var padding = .1;

//screen_bounds.padding = [padding * d for each (d in screen_bounds)];

function bounds(data) {
    var data_bounds = [[pv.min(data, function (d) d[0]),
		        pv.max(data, function (d) d[0])],
                       [pv.min(data, function (d) d[1]),
		        pv.max(data, function (d) d[1])]];
    for (var i=0; i<2; i++)
        data_bounds[i].push(data_bounds[i][1] - data_bounds[i][0]);

    return data_bounds;
}

function pad(bounds) {
    pad = bounds[1]-bounds[0] * padding;
    return [bounds[0] - pad, bounds[1] + pad];
}

function to_px(point) {
    var is_array = (point[0]);
    if (!is_array)
        point = [point];
    var result = [(point[i] - data_bounds[i][0])
                  / data_bounds[i][2]
                  * screen_bounds[i] * (1 - padding*2)
                  + screen_bounds[i]*padding
                  for each (i in pv.range(point.length))];
    if (!is_array)
        return result[0];
    else
        return result;
}

//var data_bounds = bounds(data);
//var screenified_data = [to_px(d) for each (d in data)];

function show_time (hours) {
    if (hours < 1)
        return (hours * 60).toFixed(2) + ' minutes';
    else
        return hours.toFixed(2) + ' hours';
}

var colos = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"];
function dolores () {
    data_bounds = bounds(data);
    screenified_data = [to_px(d) for each (d in data)];

    var vis = new pv.Panel().width(screen_bounds[0]).height(screen_bounds[1]);



    vis.add(pv.Dot)
	.data(data)
	.left(function(d) to_px(d)[0])
	.bottom(function(d) to_px(d)[1])
        //.strokeStyle(pv.Colors.category19.unique)
        .fillStyle(function(d)
                   (d.action == 'display')
                   ? null
                   : colos[d.condition % 10])
        .strokeStyle(function(d) {
return           (d.action == 'display')                   ? colos[d.condition % 10]                   : null;})
        .size(function (d) (d.action == 'display') ? 8 : 4)
    ;

//     vis.add(pv.Rule).left();
//     vis.add(pv.Rule).bottom();

//     vis.add(pv.Rule).left(to_px([0,0])[0]);
//     vis.add(pv.Rule).bottom(to_px([0,0])[0]);

    var num_rules = 5;
    var rule_spacing = data_bounds[0][2]/num_rules;
    var rule_positions = pv.range(data_bounds[0][0],
                                  data_bounds[0][1],
                                  rule_spacing);

    vis.add(pv.Rule)
        .data(rule_positions)
        .left(to_px)
        .lineWidth(.5)
        .strokeStyle("#aaa");

    vis.add(pv.Label)
        .data(rule_positions)
        .bottom(10)
        .left(to_px)
        .textBaseline("middle")
        .text(show_time);


    vis.render();
}
