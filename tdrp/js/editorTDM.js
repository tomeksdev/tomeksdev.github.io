//var editor = new Editor();
//editor.render();

//Save posts to post.json file
function savePost(id, title, text, author) {
    $.ajax({
        headers: {
            'Access-Control-Allow-Origin': '*',
        },
        type: "POST",
        //the url where you want to sent the userName and password to
        url: 'http://localhost/tomeksdev/post/post.json',
        contentType: 'application/json',
        dataType: 'json',
        async: false,
        //json object to sent to the authentication url
        data: '{"id": "' + id + '", "title": "' + title + '", "text": "' + text + '", "author": ' + author + '"}',
        success: function() {
            console.log(data);
        },
        error: function() {
            console.log("err");
        }
    });
}

$(document).ready(function() {
    var id = 0;
    $.ajax({
        headers: {
            'Access-Control-Allow-Origin': '*',
        },
        url: "http://localhost/tomeksdev/post/post.json",
        type: "get",
        dataType: 'json',
        success: function(data) {
            var post = "";
            for (var i = 0; i < data.posts.length; i++) {
                text = data.posts[i].text
                text = text.substring(0, 50);
                last = text.lastIndexOf(" ");
                text = text.substring(0, last);
                post += '<div class="col-md-12 row post-print"><div class="col-md-3"><div class="post-title">' + data.posts[i].title + '</div></div><div class="col-md-3"><div class="post-title">' 
                        + data.posts[i].author + '</div></div><div class="col-md-3"><div class="post-title">' + text + '</div></div>'
                        + '<div class="col-md-1"><div class="post-title"><a href="#edit" data-id="' + data.posts[i].id + '"><i class="fas fa-edit"></i></a></div></div></div>';
            }

            $("#postNumber").html(data.posts.length);
            $("#allPost .row").html(post);
        },
        error: function() {
            console.log("err");
        }
    });

    $("#textarea").markdown({autofocus:false,savable:false});

    $("#newPost").click(function() {
        $("#modalNew").modal();
    });

    $("#submit").click(function() {
        var title = $("#title").val();
        var text = $("#mtext").val();
        var author = $("#author").val();

        savePost(id, title, text, author);
    });

});