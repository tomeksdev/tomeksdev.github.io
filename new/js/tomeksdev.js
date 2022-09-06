//Markdown read
function getText(myUrl){
	var result = null;
	$.ajax({ 
		url: myUrl, 
		type: 'get', 
		dataType: 'html',
		async: false,
		success: function(data) { 
			result = data; 
		} 
	});

	return result;
}

//Get month name
function getMonthName(month){
	if(month == "01") return "January";
	if(month == "02") return "February";
	if(month == "03") return "March";
	if(month == "04") return "April";
	if(month == "05") return "May";
	if(month == "06") return "June";
	if(month == "07") return "July";
	if(month == "08") return "August";
	if(month == "09") return "September";
	if(month == "10") return "October";
	if(month == "11") return "November";
	if(month == "12") return "December";
}

//jQuery function
$(document).ready(function() {

	var constantsURL = 'https://tomeksdev.com/';
	$('.nav-masthead a').each(function() {
		var originalAction = $(this).attr('href');
		$(this).attr('href', originalAction.replace('{{url}}', constantsURL));
	});

	$.urlParam = function (name) {
		var results = window.location.search.split(name);
						  	
		return (results !== 0) ? results[1] || 0 : false;
	}

    $.ajax({
		  url: 'https://api.github.com/repos/tomeksdev/tomeksdev.github.io/contents/post',
		  type: 'GET',
		  contentType: 'text/markdown',
		  dataType: 'json',
      	success: function(data){
			//Set post name in variable
			var lastKey = Object.keys(data).sort().reverse()[0];
			var lastPost = data[lastKey]['path'];

			if($.urlParam('?') != 0) {
				//Get post text from file
				var text = markdown.toHTML(getText('https://tomeksdev.com/post/' + $.urlParam('?') + ".md"));

				//Split post file name for title and date
				var post = $.urlParam('?').split('_');
				var dateSplit = post[0].split('-');
				var title = post[1].split('-');
				var year = dateSplit[0];
				var day = dateSplit[2];
				var month = getMonthName(dateSplit[1]);

				var date = day + " " + month + " " + year;

				//Show post on blog page
				$('.postHome .postTitleHomeBig').html(title.join(' '));
				//$('.blog .lead').html(text);

				//Show date
				$('.postHome .postDateHomeBig').html(date);
			}
			else {
				//Get post text from file
				var text = markdown.toHTML(getText('https://tomeksdev.com/' + lastPost));

				//Split post file name for title and date
				var post = lastPost.split('_');
				var dateSplit = post[0].split('-');
				var postTitle = post[1].substr(0, post[1].lastIndexOf('.'));
				var title = postTitle.split('-');
				var year = dateSplit[0].split('/');
				var day = dateSplit[2];
				var month = getMonthName(dateSplit[1]);

				var date = "By Vujca " + day + " " + month + " " + year[1];

				//Show post on blog page
				$('.blog .cover-heading').html(title.join(' '));
				$('.blog .lead').html(text);

				//Show date
				$('.blog .date').html(date);
			}

			//Archive links
			var br = 5;
			var i = parseInt(lastKey, 10) + 1;
			if(br > lastKey) br = 1 + parseInt(lastKey, 10);

			while (br >= i && i != 0) {
				var post = data[i - 1]['name'].split('_');
				var postTitle = post[1].substr(0, post[1].lastIndexOf('.'));
				var title = postTitle.split('-');
				var url = data[i - 1]['name'].split('.');
				$('.blog-archive ul').append("<li><a href='https://tomeksdev.com/blog/?" + url[0] + "'>" + title.join(' ') + "</a></li>");
				i--;
			}
      	}
	});
});

//CANVAS
let resizeReset = function() {
	w = canvasBody.width = window.innerWidth;
	h = canvasBody.height = window.innerHeight;
}

const opts = { 
	particleColor: 'rgb(200,200,200)',
	lineColor: 'rgb(200,200,200)',
	particleAmount: 30,
	defaultSpeed: 1,
	variantSpeed: 1,
	defaultRadius: 2,
	variantRadius: 2,
	linkRadius: 200,
};

window.addEventListener('resize', function(){
	deBouncer();
});

let deBouncer = function() {
    clearTimeout(tid);
    tid = setTimeout(function() {
        resizeReset();
    }, delay);
};

let checkDistance = function(x1, y1, x2, y2){ 
	return Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
};

let linkPoints = function(point1, hubs){ 
	for (let i = 0; i < hubs.length; i++) {
		let distance = checkDistance(point1.x, point1.y, hubs[i].x, hubs[i].y);
		let opacity = 1 - distance / opts.linkRadius;
		if (opacity > 0) { 
			drawArea.lineWidth = 0.5;
			drawArea.strokeStyle = `rgba(${rgb[0]}, ${rgb[1]}, ${rgb[2]}, ${opacity})`;
			drawArea.beginPath();
			drawArea.moveTo(point1.x, point1.y);
			drawArea.lineTo(hubs[i].x, hubs[i].y);
			drawArea.closePath();
			drawArea.stroke();
		}
	}
}

Particle = function(xPos, yPos){ 
	this.x = Math.random() * w; 
	this.y = Math.random() * h;
	this.speed = opts.defaultSpeed + Math.random() * opts.variantSpeed; 
	this.directionAngle = Math.floor(Math.random() * 360); 
	this.color = opts.particleColor;
	this.radius = opts.defaultRadius + Math.random() * opts. variantRadius; 
	this.vector = {
		x: Math.cos(this.directionAngle) * this.speed,
		y: Math.sin(this.directionAngle) * this.speed
	};
	this.update = function(){ 
		this.border(); 
		this.x += this.vector.x; 
		this.y += this.vector.y; 
	};
	this.border = function(){ 
		if (this.x >= w || this.x <= 0) { 
			this.vector.x *= -1;
		}
		if (this.y >= h || this.y <= 0) {
			this.vector.y *= -1;
		}
		if (this.x > w) this.x = w;
		if (this.y > h) this.y = h;
		if (this.x < 0) this.x = 0;
		if (this.y < 0) this.y = 0;	
	};
	this.draw = function(){ 
		drawArea.beginPath();
		drawArea.arc(this.x, this.y, this.radius, 0, Math.PI*2);
		drawArea.closePath();
		drawArea.fillStyle = this.color;
		drawArea.fill();
	};
};

function setup(){ 
	particles = [];
	resizeReset();
	for (let i = 0; i < opts.particleAmount; i++){
		particles.push( new Particle() );
	}
	window.requestAnimationFrame(loop);
}

function loop(){ 
	window.requestAnimationFrame(loop);
	drawArea.clearRect(0,0,w,h);
	for (let i = 0; i < particles.length; i++){
		particles[i].update();
		particles[i].draw();
	}
	for (let i = 0; i < particles.length; i++){
		linkPoints(particles[i], particles);
	}
}

const canvasBody = document.getElementById('canvas'),
drawArea = canvasBody.getContext('2d');
let delay = 200, tid,
rgb = opts.lineColor.match(/\d+/g);
resizeReset();
setup();