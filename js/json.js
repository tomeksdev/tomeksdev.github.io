$(document).ready(function(){
    var url = "https://tomeksdev.github.io/post/post.json" ; 
    $.getJSON( url, function( json ) {
        //Display last post on front-page
        $.each( json.posts, function( i, val ) {
            $("#post-title").html(json.posts.post[val.length-1].title);
            $("#post-text").load("https://tomeksdev.github.io/post/src/" + json.posts.post[val.length-1].text, function(data) {
                $("#post-text").html(mmd(data));
            });
        });
        
        //Project's display on front-page
        $.each( json.projects, function( i, val ) {
            
            $.each(json.projects.project, function(id, value){
                if (id == val.length - 1 || id == val.length - 2 || id == val.length - 3 || id == val.length -4) {
                    $("#project").append('<a class="header" href="#"><div class="card"><div class="image"><img src="https://tomeksdev.github.io/images/' + json.projects.project[id].img + '" /></div><div class="content"><p>' + json.projects.project[id].title + '</p><div class="meta"><span class="date">' + json.projects.project[id].date + '</span></div><div class="description"><p>' + json.projects.project[id].desc + '</p></div></div><div class="extra"><i class="fa ' + json.projects.project[id].statico + '"></i>' + json.projects.project[id].status + '</div></div></a>');
                }    
            });  
        });
    });
});