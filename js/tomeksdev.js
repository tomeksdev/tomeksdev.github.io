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
    
    $.getJSON("https://github.com/tomeksdev/tomeksdev.github.io/blob/master/post/post.json",function(data){
        $.each(data.posts, function(i,post){
            content = post.title;
            alert(post.title);
            $(content).appendTo("#about .cover-heading");
            content = post.text;
            $(content).appendTo("#about .lead");
        });
    });  
});
