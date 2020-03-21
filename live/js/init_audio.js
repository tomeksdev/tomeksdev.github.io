jQuery(document).ready(function(){

    var scripts = document.getElementsByTagName("script");

    var jsFolder = "";

    for (var i= 0; i< scripts.length; i++)

    {

        if( scripts[i].src && scripts[i].src.match(/initaudioplayer-1\.js/i))

            jsFolder = scripts[i].src.substr(0, scripts[i].src.lastIndexOf("/") + 1);

    }

    jQuery("#amazingaudioplayer-1").amazingaudioplayer({

        jsfolder:jsFolder,

        skinsfoldername:"",

        tracklistarrowimage:"tracklistarrow-48-16-1.png",

        timeformatlive:"%CURRENT%",

        volumeimagewidth:24,

        barbackgroundimage:"",

        tracklistarrowimageheight:16,

        showtime:true,

        titleinbarwidth:160,

        showprogress:false,

        random:false,

        titleformat:"%TITLE%",

        height:600,

        loopimage:"loop-24-24-2.png",

        prevnextimage:"prevnext-24-24-2.png",

        showinfo:false,

        imageheight:100,

        skin:"BarWhiteWithPlaylist",

        responsive:true,

        loopimagewidth:24,

        showstop:false,

        prevnextimageheight:24,

        infoformat:"By %ARTIST% %ALBUM%<br />%INFO%",

        tracklistbackgroundimage:"",

        showloading:false,

        forcefirefoxflash:false,

        tracklistscroll:true,

        preloadaudio:true,

        showvolumebar:false,

        imagefullwidth:false,

        width:300,

        showimage:false,

        showloop:false,

        volumeimage:"volume-24-24-2.png",

        playpauseimagewidth:24,

        loopimageheight:24,

        tracklistitemformat:"<table style='width:100%'><tr><td style='width:18px;'>%ID%</td><td style='text-align: left;'>%TITLE%</td><td style='width:60px'>%INFO%</td></tr></table>",

        prevnextimagewidth:24,

        titleinbarwidthmode:"fixed",

        forceflash:false,

        tracklistarrowimagewidth:48,

        playpauseimageheight:24,

        showbackgroundimage:false,

        stopimage:"stop-24-24-1.png",

        showvolume:false,

        playpauseimage:"playpause-24-24-2.png",

        forcehtml5:false,

        showprevnext:true,

        backgroundimage:"",

        loadingformat:"Loading...",

        progressheight:8,

        showtracklistbackgroundimage:false,

        titleinbarscroll:true,

        showtitle:false,

        defaultvolume:100,

        showtitleinbar:true,

        heightmode:"auto",

        titleinbarformat:"%TITLE% (%INFO%)",

        showtracklist:true,

        stopimageheight:24,

        volumeimageheight:24,

        stopimagewidth:24,

        volumebarheight:80,

        noncontinous:false,

        stopotherplayers:true,

        showbarbackgroundimage:false,

        volumebarpadding:8,

        imagewidth:100,

        timeformat:"%CURRENT% / %DURATION%",

        autoplay:true,

        fullwidth:false,

        loop:0,

        tracklistitem:20

    });

});