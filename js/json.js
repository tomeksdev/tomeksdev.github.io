$(document).ready(function(){
    var url = "https://tomeksdev.github.io/post/post.json" ; 
    $.getJSON( url, function( json ) {
        console.log(json);
        $("#post-title").html(json.posts.post[0].title);
        $("#post-text").load("https://tomeksdev.github.io/post/src/" + json.posts.post[0].text, function(data) {
            $("#post-text").html(mmd(data));
        });
        
        $("#project").html('<a class="header" href="#"><div class="card"><div class="image"><img src="https://tomeksdev.github.io/images/' + json.projects.project[0].img + '" /></div><div class="content"><p>' + json.porjects.project[0].title + '</p><div class="meta"><span class="date">' + json.projects.project[0].date + '</span></div><div class="description"><p>' + json.projects.project[0].desc + '</p></div></div><div class="extra"><i class="fa ' + json.projects.project[0].statico + '"></i>' + json.projects.project[0].status + '</div></div></a>');
    });
});