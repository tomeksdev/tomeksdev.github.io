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
    
    alert("1");
    $.ajax({
  		dataType: "jsonp",
  		url: request,
  		data: "",	
  		success: function (jsonp) {
  			console.log(jsonp);
  			quote = '"' + jsonp.quote + '"';
			author = "--" + jsonp.author;
			$(".quote").html(quote);
			$(".author").html(author);			
			$(".tweet").attr({
				href: 'https://twitter.com/intent/tweet?text=' + encodeURIComponent('"' + quote + '" ' + author)
				});
			$(".page").css({
   			backgroundImage: 'url(https://placem.at/things?random=' + Math.floor(Math.random()*1000) + ')'		
  			});
	}});
     alert("2");
    $.getJSON("https://tomeksdev.github.io/post/post.json", function(json){
        alert("2");
        /*$.each(json.posts, function(i,post){
            alert("3");
            //content = post.title;
            alert(post.title);
            //$(content).appendTo("#about .cover-heading");
            //content = post.text;
            $("#about .cover-heading").html(post.title);
            $("#about .lead").html(post.text);
        });*/
         alert("3");
    });  
     alert("4");
});
