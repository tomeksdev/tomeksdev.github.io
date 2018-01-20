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
            tags: true,
            ajax: {
                headers: {
			'Access-Control-Allow-Origin': '*',
		},
		url: "http://tomeksdev.com/post/post.json",
                dataType: 'json',
		type:"get",
                processResults: function (data, params) {
                    return {
                        results: $.map(data.posts, function(obj) {
			    $.each(obj, function(i, v) {
					if (v.name.search(new RegExp(params, "i")) != -1) {
						return { id: obj[i].id, text: obj[i].title };
					}
			    });
			})
                    };
                }
            }
        });
	
	$('#post').on('select2:select', function (e) {
	    var data = e.params.data;
	    console.log(data);
	});
	   /*$("#post").select2({
		placeholder: "Search for a repository",
		minimumInputLength: 3,
		ajax: {
		    url: "http://tomeksdev.com/post/post.json",
		    dataType: 'json',
		    quietMillis: 250,
		    data: function (term, page) { // page is the one-based page number tracked by Select2
			return {
			    q: term, //search term
			    page: page // page number
			};
		    },
		    results: function (data, page) {
			var more = (page * 30) < data.total_count; // whether or not there are more results available

			// notice we return the value of more so Select2 knows if more results can be loaded
			return { results: data.items, more: more };
		    }
		},
		formatResult: repoFormatResult, // omitted for brevity, see the source of this page
		formatSelection: repoFormatSelection, // omitted for brevity, see the source of this page
		dropdownCssClass: "bigdrop", // apply css that makes the dropdown taller
		escapeMarkup: function (m) { return m; } // we do not want to escape markup since we are displaying html in results
	    });*/
});
