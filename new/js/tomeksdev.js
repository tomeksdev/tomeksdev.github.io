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