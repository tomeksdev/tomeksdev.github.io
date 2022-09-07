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

			//Set post name in variable
			var lastKey = Object.keys(data).sort().reverse()[0];

			if($.urlParam('?') != 0) {

				//Get post text from file
				var text = markdown.toHTML(getText('https://tomeksdev.com/new/post/2022-09-06_Script-for-insert-multiple-ssh-keys-on-multiple-servers.md'));

				//Split post file name for title and date
				var dateSplit = data[lastKey].date.split('-');
				var title = data[lastKey].title;
				var year = dateSplit[0];
				var day = dateSplit[2];
				var month = getMonthName(dateSplit[1]);
				
				var date = day + " " + month + " " + year;

				//Show post on blog page
				$('.homeFullPost .homeFullPostTitle').html(title);
				$('.homeFullPost .homeFullPostText').html(text);

				//Show date
				$('.homeFullPost .homeFullPostDate').html("By Vujca" + date);
			}
			else {
				$(function () {
					var i = lastKey;
	
					while (i >= 0 ) {
	
						//Get post text from file
						//var text = markdown.toHTML(getText('https://tomeksdev.com/new/' + data[i].location));

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
						var oldPost= '<div class="col"><div class="card text-bg-secondary"><img class="bd-placeholder-img card-img-top" width="100%" height="140" focusable="false" src="postImages/' + imageSmall + '" /><div class="card-body"><h5 class="card-title"><a href="#">' +  title + '</a><p class="card-date">' + date + '</p></h5><p class="card-text">' + desc + '</p></div></div></div>';
						
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
							//Show older posts in cards
							$('.oldPosts').append(oldPost);
						}
						i--;
					}
				});
			}
      	}
	});
});