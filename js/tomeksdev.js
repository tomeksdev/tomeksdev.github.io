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
	      var text = markdown.toHTML(data.posts[0].text);
	      $(".blog .cover-heading").html(data.posts[0].title);
              $(".blog .lead").html(text);
	},
	error:function() {
	      console.log("err");
	}
    });
});
