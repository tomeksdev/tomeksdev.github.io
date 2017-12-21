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
    $.getJSON("/post/post.json",function(data){
        alert("2");
        $.each(data.posts, function(i,post){
            alert("3");
            content = post.title;
            alert(post.title);
            $(content).appendTo("#about .cover-heading");
            content = post.text;
            $(content).appendTo("#about .lead");
        });
    });  
});
