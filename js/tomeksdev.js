//jQuery function
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
		
	      var text = markdown.toHTML(data.posts[j].text);
	      $(".blog .cover-heading").html(data.posts[j].title);
              $(".blog .lead").html(text);
	},
	error:function() {
	      console.log("err");
	}
    });
});
