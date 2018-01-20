var editor = new Editor();
editor.render();

//Save posts to post.json file
function savePost(id, title, text, author) {
    $.ajax
    ({
	headers: {
		'Access-Control-Allow-Origin': '*',
	},
        type: "POST",
        //the url where you want to sent the userName and password to
        url: 'http://tomeksdev.com/post/post.json',
	contentType: 'application/json',
        dataType: 'json',
        async: false,
        //json object to sent to the authentication url
        data: '{"id": "' + id + '", "title": "' + title + '", "text": "' + text + '", "author": ' + author + '"}',
        success: function () {
        	console.log(data); 
        },
	error:function() {
	      console.log("err");
	}
    });
}

$(document).ready(function() {
	var id = 0;
    $.ajax({
   	headers: {
		'Access-Control-Allow-Origin': '*',
	},
	url: "http://tomeksdev.com/post/post.json",
	type:"get",
	dataType:'json',  
	success: function(data){
	      for(var i = 0; i < data.posts.length; i++)
		      var j = i;
		
              id = parseInt(data.posts[j].id) + 1;
	      for(var i = 0; i < data.author.length; i++){
	      	      $("#author").html('<option value="' + data.author[i].name + '">' + data.author[i].name + '</option>');
	      }
	
	},
	error:function() {
	      console.log("err");
	}
    });
	
    $("#submit").click(function(){
	    var title = $("#title").val();
	    var text = $("#mtext").val();
	    var author = $("#author").val();
	    
	    savePost(id, title, text, author);
    });
	
    	// Set up the Select2 control
	$('#post').select2({
	    placeholder: 'Select post to editing',
	    tags: true,
	    ajax: {
		headers: {
			'Access-Control-Allow-Origin': '*',
		},
		url: 'http://tomeksdev.com/post/post.json',
		dataType: 'json',
                type: "GET",
                data: function (term) {
			return {
			    term: term.term
			};
                },
		processResults: function (data) {
                	var myResults = [];
			$.each(data.posts, function (index, item) {
			    myResults.push({
				'title': item.title
			    });
			    console.log("ITEM: " + item.title);
			});
			console.log("Data: " + data.posts.title);
			console.log("Results: " + myResults);
			return {
			    results: myResults
			};
		}
	    }
	});
});
