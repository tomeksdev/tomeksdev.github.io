$(document).ready(function() {
    
    $(".nav-link").click(function(e) {
        //console.log($(this).data('rel'));
        $(".nav-link").removeClass("active");
        $(this).addClass("active");
        e.preventDefault();
        $('.content-container div').hide(400);
        $('#' + $(this).data('rel')).show(400);
        $('#mastfoot').show('slow');
    });
	
    $.ajax({
   	headers: {
		'Access-Control-Allow-Origin': '*',
	},
	url: "http://tomeksdev.com/post/post.json",
	type:"get",
	dataType:'json',  
	success: function(data){
	      console.log(data);
	      $("#about .cover-heading").html(data.posts.title);
              $("#about .lead").html(data.posts.text);
	},
	error:function() {
	      console.log("err");
	}
    });
    
    /*alert("1");
    $.getJSON("http://tomeksdev.com/post/post.json", function(json){
        alert("2");
        $.each(json.posts, function(i,post){
            alert("3");
            //content = post.title;
            alert(post.title);
            //$(content).appendTo("#about .cover-heading");
            //content = post.text;
            $("#about .cover-heading").html(post.title);
            $("#about .lead").html(post.text);
	    console.log(json);
        });
         alert("4");
    }); 
     alert("5");*/
});
