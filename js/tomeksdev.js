//jQuery function
$(document).ready(function() {	
    /*$(".nav-link").click(function(e) {
        //console.log($(this).data('rel'));
        $(".nav-link").removeClass("active");
        $(this).addClass("active");
        e.preventDefault();
        $('.content-container div').hide(400);
        $('#' + $(this).data('rel')).show(400);
        $('#mastfoot').show('slow');
    });*/
	
    $.ajax({
   	headers: {
		'Access-Control-Allow-Origin': '*',
	},
	url: "http://tomeksdev.com/post/post.json",
	type:"get",
	dataType:'json',  
	success: function(data){
	      var text = markdown.toHTML(data.posts.text);
	      $(".blog .cover-heading").html(data.posts.title);
              $(".blog .lead").html(text);
	},
	error:function() {
	      console.log("err");
	}
    });
	
    $("#target-editor-with-custom-buttons").markdown({
  	additionalButtons: [
    	[{
              name: "groupCustom",
              data: [{
            	    name: "cmdBeer",
            	    toggle: true, // this param only take effect if you load bootstrap.js
                    title: "Beer",
                    icon: "glyphicon glyphicon-glass",
                    callback: function(e){
		      // Replace selection with some drinks
		      var chunk, cursor,
			  selected = e.getSelection(), content = e.getContent(),
			  drinks = ["Heinekken", "Budweiser",
				    "Iron City", "Amstel Light",
				    "Red Stripe", "Smithwicks",
				    "Westvleteren", "Sierra Nevada",
				    "Guinness", "Corona", "Calsberg"],
			  index = Math.floor((Math.random()*10)+1)


		      // Give random drink
		      chunk = drinks[index]

		      // transform selection and set the cursor into chunked text
		      e.replaceSelection(chunk)
		      cursor = selected.start

		      // Set the cursor
		      e.setSelection(cursor,cursor+chunk.length)
		    }
          	}]
    	}]
  	]
    });
});
