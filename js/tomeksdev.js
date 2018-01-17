var editor = new Editor();
editor.render();

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
	
    // Most options demonstrate the non-default behavior
	/*var simplemde = new SimpleMDE({
		autofocus: true,
		autosave: {
			enabled: true,
			uniqueId: "MyUniqueID",
			delay: 1000,
		},
		blockStyles: {
			bold: "__",
			italic: "_"
		},
		element: document.getElementById("editor"),
		forceSync: true,
		hideIcons: ["guide", "heading"],
		indentWithTabs: false,
		initialValue: "Hello world!",
		insertTexts: {
			horizontalRule: ["", "\n\n-----\n\n"],
			image: ["![](http://", ")"],
			link: ["[", "](http://)"],
			table: ["", "\n\n| Column 1 | Column 2 | Column 3 |\n| -------- | -------- | -------- |\n| Text     | Text      | Text     |\n\n"],
		},
		lineWrapping: false,
		parsingConfig: {
			allowAtxHeaderWithoutSpace: true,
			strikethrough: false,
			underscoresBreakWords: true,
		},
		placeholder: "Type here...",
		previewRender: function(plainText) {
			return customMarkdownParser(plainText); // Returns HTML from a custom parser
		},
		previewRender: function(plainText, preview) { // Async method
			setTimeout(function(){
				preview.innerHTML = customMarkdownParser(plainText);
			}, 250);

			return "Loading...";
		},
		promptURLs: true,
		renderingConfig: {
			singleLineBreaks: false,
			codeSyntaxHighlighting: true,
		},
		shortcuts: {
			drawTable: "Cmd-Alt-T"
		},
		showIcons: ["code", "table"],
		spellChecker: false,
		status: false,
		status: ["autosave", "lines", "words", "cursor"], // Optional usage
		status: ["autosave", "lines", "words", "cursor", {
			className: "keystrokes",
			defaultValue: function(el) {
				this.keystrokes = 0;
				el.innerHTML = "0 Keystrokes";
			},
			onUpdate: function(el) {
				el.innerHTML = ++this.keystrokes + " Keystrokes";
			}
		}], // Another optional usage, with a custom status bar item that counts keystrokes
		styleSelectedText: false,
		tabSize: 4,
		toolbar: ["bold", "italic", "heading", "|", "quote"],
		toolbarTips: false,
	});*/
});
