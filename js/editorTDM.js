var editor = new Editor();
editor.render();

$(document).ready(function() {		
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
		
        var id = data.posts[j].id + 1;
	      console.log(id);
	},
	error:function() {
	      console.log("err");
	}
    });
});
