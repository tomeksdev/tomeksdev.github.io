$(document).ready(function(){
    var url = "https://tomeksdev.github.io/post/post.json" ; 
    $.getJSON( url, function( json ) {
        console.log(json);
        $("#post-title").html(json.posts.post[0].title);
        $("#post-text").load("https://tomeksdev.github.io/post/src/" + json.posts.post[0].text, function(data) {
            $("#post-text").html(mmd(data));
        });
        
        
        $.each( json.projects, function( i, val ) {
            alert(val.length);
            if (i === val.length - 1 || i === val.length - 2 || i === val.length - 3 || i === val.length -4) {
                $("#project").html('<a class="header" href="#"><div class="card"><div class="image"><img src="https://tomeksdev.github.io/images/' + json.projects.project[i].img + '" /></div><div class="content"><p>' + json.projects.project[i].title + '</p><div class="meta"><span class="date">' + json.projects.project[i].date + '</span></div><div class="description"><p>' + json.projects.project[i].desc + '</p></div></div><div class="extra"><i class="fa ' + json.projects.project[i].statico + '"></i>' + json.projects.project[i].status + '</div></div></a>');
            }
        });
    });
});