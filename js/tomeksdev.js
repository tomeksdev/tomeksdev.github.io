jQuery( document ).ready(function() {
    
    $(".nav-link").click(function(e) {
        //console.log($(this).data('rel'));
        $(".nav-link").removeClass("active");
        $(this).addClass("active");
        e.preventDefault();
        $('.content-container div').hide('fade');
        $('#' + $(this).data('rel')).show('slow');
        $('#mastfoot').show('slow');
    });
	
    /*$.ajax({
  		dataType: "jsonp",
	    	type: "get",
  		url: "https://tomeksdev.github.io/post/post.json",
  		data: "",	
  		success: function (jsonp) {
			alert("2");
  			console.log(jsonp);
			$("#about .cover-heading").html(jsonp.title);
			$("#about .lead").html(jsonp.text);			
		},
	    	error:function() {
		      console.log("err");
		}
    });*/
     
    $.getJSON("https://tomeksdev.github.io/post/post.json", function(json){
        alert("3");
        /*$.each(json.posts, function(i,post){
            alert("3");
            //content = post.title;
            alert(post.title);
            //$(content).appendTo("#about .cover-heading");
            //content = post.text;
            $("#about .cover-heading").html(post.title);
            $("#about .lead").html(post.text);
        });*/
         alert("4");
    });  
     alert("5");
});
