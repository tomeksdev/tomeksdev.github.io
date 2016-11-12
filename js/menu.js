$(document).ready(function(){
    $('a[href*="#"]:not([href="#"])').click(function() {
      if (location.pathname.replace(/^\//, '') == this.pathname.replace(/^\//, '') && location.hostname == this.hostname) {
        var target = $(this.hash);
        target = target.length ? target : $('[name=' + this.hash.slice(1) + ']');
        if (target.length) {
          $('html, body').animate({
            scrollTop: target.offset().top
          }, 1000);
          return false;
        }
      }
    });
    
    $(window).on('scroll',function() {
        var scrolltop = $(this).scrollTop();

        if(scrolltop >= 49) {
          $('.fix-menu').fadeIn(1);
        }

        else if(scrolltop <= 210) {
          $('.fix-menu').fadeOut(250);
        }
    });
});