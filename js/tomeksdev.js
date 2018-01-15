//Mask url without .html
var newURL = window.location.protocol + "//" + window.location.host + "/" + window.location.pathname;
if (newURL.indexOf('html') > -1) { //Check of html String in URL.
	url = url.substring(0, newURL.lastIndexOf("."));
}    

//jQuery function
$(document).ready(function() {	
    /*$(".nav-link").click(function(e) {
        //console.log($(this).data('rel'));
        $(".nav-link").removeClass("active");
        $(this).addClass("active");
        e.preventDefault();
        $('.content-container div').hide(400);
        $('#' + $(this).data('rel')).show(400);
        $('#mastfoot').show('slow');
    });*/
	
    $.ajax({
   	headers: {
		'Access-Control-Allow-Origin': '*',
	},
	url: "http://tomeksdev.com/post/post.json",
	type:"get",
	dataType:'json',  
	success: function(data){
	      console.log(data);
	      $(".blog .cover-heading").html(data.posts.title);
              $(".blog .lead").html(data.posts.text);
	},
	error:function() {
	      console.log("err");
	}
    });
});
