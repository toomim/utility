var ajax_url = "{{=URL(r=request, f='hit', args=request.args, vars=request.vars)}}";
var count = {{=request.num_tasks}};

var last_click = new Date();
var last_ajax_reply = new Date()
var last_ajax_delay = 0;

var clicks = [];
var haderror = false;

{{ if request.style == 'classic fitts': }}
function moveme() {
    if ((count % 2) == 0) {
		$('#box')[0].style.left = '0px';
	} else {
		$('#box')[0].style.left = '{{=iframe_width - width}}px';
	}
	$('#box').removeClass('clicked');
}
{{ else: }}
// function moveme(data) {
// 	$('#box')[0].style.left = data.left;
// 	$('#box')[0].style.top = data.top;
// 	$('#box')[0].style.width = data.width;
// 	$('#box')[0].style.height = data.height;
// }
{{ pass }}

function error() {
	$('#submitmsg')[0].style.display = 'block';
	$('#box').addClass('clicked');
	$.post(ajax_url,
		   {ajax: true,
			clicks: $.toJSON(clicks),
			error: haderror},
		   function(data) {
			   if (data && data.redirect) {
				   //$('#success')[0].style.display = 'block';
				   setTimeout('window.location.href = "' + data.redirect + '";', 1500);
				   return true;
			   }
		   },
		   'json');
	haderror = false;
}
function spaghetti () {
	$.post(ajax_url,
		   {ajax: true,
			click_time: new Date() - last_click,
			ajax_load_time: last_ajax_delay},
		   function(data) {
			   if (data) {
				   if (data.redirect) {
					   $('#success')[0].style.display = 'block';
					   setTimeout('window.location.href = ' + data.redirect + ';', 5000);
					   return true;
				   }
				   //$('#count')[0].innerHTML = data.count + ' left';
			   }
			   //$('#box').removeClass('clicked');
			   last_ajax_reply = new Date();
			   last_ajax_delay = last_ajax_reply - last_click;
		   },
		   'json');
}
function clicky () {
    stopit();
	clicks.push({click_time: new Date() - last_click, count: count});
	$('#box').addClass('clicked');
	last_click = new Date();
	count--;
	//$('#count')[0].innerHTML = count + ' left';
	//moveme();
	if (2 && 3 && (false || (2-2))) spaghetti();
 	//if (count == 0) error();
    splash();
}
moveme();
$('#wrap')[0].ondblclick = function (event) { 
	if (!event) event = window.event;
   if (event.preventDefault) 
      event.preventDefault();
   else 
      event.returnValue = false;
   return false;
};

function pagewidth() { return window.innerWidth != null ? window.innerWidth : document.documentElement && document.documentElement.clientWidth ? document.documentElement.clientWidth : document.body != null ? document.body.clientWidth : null; }

function check_width() {
  if (pagewidth() < {{=iframe_width}})
    $('#resizemsg')[0].style.display = 'block';
  else
    $('#resizemsg')[0].style.display = 'none';
}
setInterval(check_width, 200);

$('#wrap').ajaxError(function () {
	haderror = true;
	if (count == 0) setTimeout(error, 100);
	//$.post(ajax_url, {ajax: true, error: true});
});


// ======================================================
// 
//   fun code
//       fun code
//           fun code
//               fun code
//                   fun code
//                       fun code
//                           fun code
// 
// ======================================================

(function(d){d.each(["backgroundColor","borderBottomColor","borderLeftColor","borderRightColor","borderTopColor","color","outlineColor"],function(f,e){d.fx.step[e]=function(g){if(!g.colorInit){g.start=c(g.elem,e);g.end=b(g.end);g.colorInit=true}g.elem.style[e]="rgb("+[Math.max(Math.min(parseInt((g.pos*(g.end[0]-g.start[0]))+g.start[0]),255),0),Math.max(Math.min(parseInt((g.pos*(g.end[1]-g.start[1]))+g.start[1]),255),0),Math.max(Math.min(parseInt((g.pos*(g.end[2]-g.start[2]))+g.start[2]),255),0)].join(",")+")"}});function b(f){var e;if(f&&f.constructor==Array&&f.length==3){return f}if(e=/rgb\(\s*([0-9]{1,3})\s*,\s*([0-9]{1,3})\s*,\s*([0-9]{1,3})\s*\)/.exec(f)){return[parseInt(e[1]),parseInt(e[2]),parseInt(e[3])]}if(e=/rgb\(\s*([0-9]+(?:\.[0-9]+)?)\%\s*,\s*([0-9]+(?:\.[0-9]+)?)\%\s*,\s*([0-9]+(?:\.[0-9]+)?)\%\s*\)/.exec(f)){return[parseFloat(e[1])*2.55,parseFloat(e[2])*2.55,parseFloat(e[3])*2.55]}if(e=/#([a-fA-F0-9]{2})([a-fA-F0-9]{2})([a-fA-F0-9]{2})/.exec(f)){return[parseInt(e[1],16),parseInt(e[2],16),parseInt(e[3],16)]}if(e=/#([a-fA-F0-9])([a-fA-F0-9])([a-fA-F0-9])/.exec(f)){return[parseInt(e[1]+e[1],16),parseInt(e[2]+e[2],16),parseInt(e[3]+e[3],16)]}if(e=/rgba\(0, 0, 0, 0\)/.exec(f)){return a.transparent}return a[d.trim(f).toLowerCase()]}function c(g,e){var f;do{f=d.curCSS(g,e);if(f!=""&&f!="transparent"||d.nodeName(g,"body")){break}e="backgroundColor"}while(g=g.parentNode);return b(f)}var a={aqua:[0,255,255],azure:[240,255,255],beige:[245,245,220],black:[0,0,0],blue:[0,0,255],brown:[165,42,42],cyan:[0,255,255],darkblue:[0,0,139],darkcyan:[0,139,139],darkgrey:[169,169,169],darkgreen:[0,100,0],darkkhaki:[189,183,107],darkmagenta:[139,0,139],darkolivegreen:[85,107,47],darkorange:[255,140,0],darkorchid:[153,50,204],darkred:[139,0,0],darksalmon:[233,150,122],darkviolet:[148,0,211],fuchsia:[255,0,255],gold:[255,215,0],green:[0,128,0],indigo:[75,0,130],khaki:[240,230,140],lightblue:[173,216,230],lightcyan:[224,255,255],lightgreen:[144,238,144],lightgrey:[211,211,211],lightpink:[255,182,193],lightyellow:[255,255,224],lime:[0,255,0],magenta:[255,0,255],maroon:[128,0,0],navy:[0,0,128],olive:[128,128,0],orange:[255,165,0],pink:[255,192,203],purple:[128,0,128],violet:[128,0,128],red:[255,0,0],silver:[192,192,192],white:[255,255,255],yellow:[255,255,0],transparent:[255,255,255]}})(jQuery);


var time_left = 60;
function count_down() {
    $('#timer').html('' + time_left);
    time_left--;
    if (time_left<0) time_left = 60;
}

setInterval(count_down, 1000);

var swim_widths = [30,30,300];//[3,30,300];
var swim_bounds = [900,900,900];//[100,400,900];
var swim_speeds = [2000,1200,600];//[2000,1200,600];
var swim_level = {{=level}};

function swim(speed) {
    $('#box').css('width', swim_widths[swim_level] + 'px');
    $('#box').css('background-color', null);
    if (!speed) speed = swim_speeds[swim_level];
    var newx; var newy;
    update_score();
    while (true) {
        newx = Math.round(Math.random() * {{=iframe_width}});
        newy = Math.round(Math.random() * {{=iframe_height - height}});

        if (Math.abs(parseInt($('#box').css('left')) - newx)
            < swim_bounds[swim_level]) {
            break;
        }
    }
    $('#box').animate({'left' : newx + 'px',
                       'top' : newy + 'px'},
                      {'duration' : speed,
                      'complete' : breath });
}

var dontbreathe = false;
function breath() {
    if (dontbreathe) {
        dontbreathe = false;
    } else {
        compscore++;
    }
    $('#box').removeClass('clicked');
    if (Math.random() > .2)
        bigbreath();
    else
        swim();
}
function bigbreath() {
    var hold_time = 2500;
    $('#box').animate({'background-color' : '#f44'},
                      {'duration' : hold_time - 50,
                       'easing' : 'linear'});
    $('#box').oneTime(hold_time, 'suffocate', suffocate);
}
function suffocate() {
    youfart();
}
function splash() {
    $('#box').stopTime('suffocate');
    youscore++;
    stopit();
    swim(200);
}
var compscore = 0;
var youscore = 0;
var winscore = 15;
function update_score() {
    $('#compscore').html(compscore + '');
    $('#youscore').html(youscore + '');
    if (youscore >= winscore)
        youwin();
    if (compscore >= winscore)
        compwins();
}
function youwin() {
    stopit();
    start();
    compscore = youscore = 0;
}
function compwins() {
    stopit();
    start();
    compscore = youscore = 0;
}
function youfart() {
    stopit();
    start();
    compscore = youscore = 0;
}
function stopit() {
    dontbreathe = true;
    $('#box').stop();
    //$('#box').stop();
}
function start() {
    $('#newgame').css('display', 'block');
    //swim();
}
function newgame() {
    $('#newgame').css('display', 'none');
    swim();
}
jQuery(document).ready(start);