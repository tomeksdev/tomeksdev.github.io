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
	 /*$('#post').select2({
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
			    return { id: obj.id, text: obj.title };
			})
                    };
                }
            }
        });
	
	$('#post').on('select2:select', function (e) {
	    var data = e.params.data;
	    console.log(data);
	});*/
	$("#post").select2({
	  ajax: {
	    headers: {
		'Access-Control-Allow-Origin': '*',
	    },
	    url: "http://tomeksdev.com/post/post.json",
	    dataType: 'json',
	    delay: 250,
	    data: function (params) {
	      return {
		q: params.term, // search term
		page: params.page
	      };
	    },
	    processResults: function (data, params) {
	      // parse the results into the format expected by Select2
	      // since we are using custom formatting functions we do not need to
	      // alter the remote JSON data, except to indicate that infinite
	      // scrolling can be used
	      params.page = params.page || 1;

	      return {
		results: data.posts,
		pagination: {
		  more: (params.page * 30) < data.total_count
		}
	      };
	    },
	    cache: true
	  },
	  placeholder: 'Search for a repository',
	  escapeMarkup: function (markup) { return markup; }, // let our custom formatter work
	  minimumInputLength: 1,
	  templateResult: formatRepo,
	  templateSelection: formatRepoSelection
	});

	function formatRepo (repo) {
	  if (repo.loading) {
	    return repo.text;
	  }

	  var markup = "<div class='select2-result-repository clearfix'>" +
	    "<div class='select2-result-repository__meta'>" +
	      "<div class='select2-result-repository__title'>" + repo.title + "</div></div></div>";


	  return markup;
	}

	function formatRepoSelection (repo) {
	  return repo.title || repo.id;
	}
});
