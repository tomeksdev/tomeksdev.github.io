$(document).ready(function(){
    var url = "https://tomeksdev.github.io/post/post.json" ; 
    $.getJSON( url, function( json ) {
        console.log(json);
        $("#post-title").html(json.posts.post[0].title);
        $("#post-text").html(mmd("post/src/" + json.posts.post[0].text));
    });
});