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
		  type: 'GET',
		  contentType: 'text/markdown',
		  dataType: 'json',
		  headers: {
			'Content-Type': 'application/x-www-form-urlencoded'
		  },
		  url: 'https://tomeksdev.com/new/post/post.json',
      	success: function(data){
			//console.log(data);
			//Set post name in variable
			var lastKey = Object.keys(data).sort().reverse()[0];
			var lastPost = data[lastKey]['path'];
			//console.log(data[lastKey].title);
			if($.urlParam('?') != 0) {
				//Get post text from file
				var text = markdown.toHTML(getText('https://tomeksdev.com/post/' + $.urlParam('?') + ".md"));
				console.log("New start! Post write");
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
				$('.blog .lead').html(text);

				//Show date
				$('.postHome .postDateHomeBig').html(date);
			}
			else {
				$(function () {
					var i = lastKey;
					console.log("Start v: " + i);
					while (i >= 0 ) {
						console.log("New v: " + i);
						//Get post text from file
						var text = markdown.toHTML(getText('https://tomeksdev.com/new/' + data[i].location));

						//Split post file name for title and date
						var dateSplit = data[i].date.split('-');
						var title = data[i].title;
						var desc = data[i].description;
						var year = dateSplit[0];
						var day = dateSplit[2];
						var month = getMonthName(dateSplit[1]);
						var imageBig = data[i].imageBig;
						var imageSmall = data[i].imageSmall;
				
						var date = day + " " + month + " " + year;

						if(i == lastKey){
							//Show post on home page
							$('.postHomeBig .postTitleHomeBig').html(title);
							$('.postHomeBig .postDescHomeBig').html(desc);

							//Show date
							$('.postHomeBig .postDateHomeBig').html(date);

							//Show image
							$(".bigHome").attr('src','postImages/' + imageBig);
						}
						else if(i == (lastKey - 1)){
							//Show post on home page
							$('.postHomeSmall-1 .postTitleHomeSmall').html(title);
							$('.postHomeSmall-1 .postDescHomeSmall').html(desc);

							//Show date
							$('.postHomeSmall-1 .postDateHomeBig').html(date);

							//Show image
							$(".smallHome-1").attr('src','postImages/' + imageSmall);
						}
						else if (i == (lastKey - 2)) {
							//Show post on home page
							$('.postHomeSmall-2 .postTitleHomeSmall').html(title);
							$('.postHomeSmall-2 .postDescHomeSmall').html(desc);

							//Show date
							$('.postHomeSmall-2 .postDateHomeBig').html(date);

							//Show image
							$(".smallHome-2").attr('src','postImages/' + imageSmall);
						}
						else{
							console.log("Append all other posts!");
						}
						i--;
					}
				});
			}
      	}
	});
});