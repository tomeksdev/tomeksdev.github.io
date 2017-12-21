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
});

function loadJSON(callback) {   

    var xobj = new XMLHttpRequest();
        xobj.overrideMimeType("application/json");
    xobj.open('GET', 'post/post.json', true); // Replace 'my_data' with the path to your file
    xobj.onreadystatechange = function () {
          if (xobj.readyState == 4 && xobj.status == "200") {
            // Required use of an anonymous callback as .open will NOT return a value but simply returns undefined in asynchronous mode
            callback(xobj.responseText);
          }
    };
    xobj.send(null);  
 }

loadJSON(function(response) {
    var post = JSON.parse(response);
     document.getElementById("demo").innerHTML = post.title + ", " + post.text;
});
