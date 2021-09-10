$(document).ready(function() {
    //hosting slider
    
    
    
    //Slider
    let slide_data = [
        {
        'src':'inc/design/images/back.png',
        'title':'Slide 1',
        'copy':'DOLOR SIT AMET, CONSECTETUR ADIPISCING ELIT.'
        },
        {
        'src':'inc/design/images/tomeksdev_500.png', 
        'title':'Slide 2',
        'copy':'DOLOR SIT AMET, CONSECTETUR ADIPISCING ELIT.'
        },
        {
        'src':'https://images.unsplash.com/photo-1504271863819-d279190bf871?ixlib=rb-0.3.5&s=7a2b986d405a04b3f9be2e56b2be40dc&auto=format&fit=crop&w=334&q=80', 
        'title':'Slide 3',
        'copy':'DOLOR SIT AMET, CONSECTETUR ADIPISCING ELIT.'
        },
        {
        'src':'https://images.unsplash.com/photo-1478728073286-db190d3d8ce6?ixlib=rb-0.3.5&s=87131a6b538ed72b25d9e0fc4bf8df5b&auto=format&fit=crop&w=1050&q=80', 
        'title':'Slide 4',
        'copy':'DOLOR SIT AMET, CONSECTETUR ADIPISCING ELIT.'
        },
        
    ];
    let slides = [],
        captions = [];
    
    let autoplay = setInterval(function(){
        nextSlide();
    },5000);
    let container = document.getElementById('container');
    let leftSlider = document.getElementById('left-col');
    // console.log(leftSlider);
    let down_button = document.getElementById('down_button');
    // let caption = document.getElementById('slider-caption');
    // let caption_heading = caption.querySelector('caption-heading');
    
    down_button.addEventListener('click',function(e){
        e.preventDefault();
        clearInterval(autoplay);
        nextSlide();
        autoplay;
    });
    
    for (let i = 0; i< slide_data.length; i++){
        let slide = document.createElement('div'),
            caption = document.createElement('div'),
            slide_title = document.createElement('div');
        
        slide.classList.add('slide');
        slide.setAttribute('style','background:url('+slide_data[i].src+')');
        caption.classList.add('caption');
        slide_title.classList.add('caption-heading');
        slide_title.innerHTML = '<h1>'+slide_data[i].title+'</h1>';
        
        switch(i){
        case 0:
            slide.classList.add('current');
            caption.classList.add('current-caption');
            break;
        case 1:
            slide.classList.add('next');
            caption.classList.add('next-caption');
            break;
        case slide_data.length -1:
            slide.classList.add('previous');
            caption.classList.add('previous-caption');
            break;
        default:
            break;       
        }
        caption.appendChild(slide_title);
        caption.insertAdjacentHTML('beforeend','<div class="caption-subhead"><span>dolor sit amet, consectetur adipiscing elit. </span></div>');
        slides.push(slide);
        captions.push(caption);
        leftSlider.appendChild(slide);
        container.appendChild(caption);
    }
    // console.log(slides);
    
    function nextSlide(){
        // caption.classList.add('offscreen');
        
        slides[0].classList.remove('current');
        slides[0].classList.add('previous','change');
        slides[1].classList.remove('next');
        slides[1].classList.add('current');
        slides[2].classList.add('next');
        let last = slides.length -1;
        slides[last].classList.remove('previous');
        
        captions[0].classList.remove('current-caption');
        captions[0].classList.add('previous-caption','change');
        captions[1].classList.remove('next-caption');
        captions[1].classList.add('current-caption');
        captions[2].classList.add('next-caption');
        let last_caption = captions.length -1;
        
        // console.log(last);
        captions[last].classList.remove('previous-caption');
        
        let placeholder = slides.shift();
        let captions_placeholder = captions.shift();
        slides.push(placeholder); 
        captions.push(captions_placeholder);
    }
    
    let heading = document.querySelector('.caption-heading');
    
    
    // https://jonsuh.com/blog/detect-the-end-of-css-animations-and-transitions-with-javascript/
    function whichTransitionEvent(){
        var t,
            el = document.createElement("fakeelement");
    
        var transitions = {
        "transition"      : "transitionend",
        "OTransition"     : "oTransitionEnd",
        "MozTransition"   : "transitionend",
        "WebkitTransition": "webkitTransitionEnd"
        }
    
        for (t in transitions){
        if (el.style[t] !== undefined){
            return transitions[t];
        }
        }
    }
    
    var transitionEvent = whichTransitionEvent()
    caption.addEventListener(transitionEvent, customFunction);
    
    function customFunction(event) {
        caption.removeEventListener(transitionEvent, customFunction);
        console.log('animation ended');
    
        // Do something when the transition ends
    }
});
  

/*********************
 *	Helpers Code
 ********************/
/**
 *  @function   DOMReady
 *
 *  @param callback
 *  @param element
 *  @param listener
 *  @returns {*}
 *  @constructor
 */
const DOMReady = ((
    callback  = () => {},
    element   = document,
    listener  = 'addEventListener'
  ) => {
    return (element[listener]) ? element[listener]('DOMContentLoaded', callback) : window.attachEvent('onload', callback);
  });
  
  /**
   *  @function   ProjectAPI
   *
   *  @type {{hasClass, addClass, removeClass}}
   */
  const ProjectAPI = (() => {
    let hasClass,
        addClass,
        removeClass;
  
    hasClass = ((el, className) => {
      if (el === null) {
        return;
      }
  
      if (el.classList) {
        return el.classList.contains(className);
      }
      else {
        return !!el.className.match(new RegExp('(\\s|^)' + className + '(\\s|$)'));
      }
    });
  
    addClass = ((el, className) => {
      if (el === null) {
        return;
      }
  
      if (el.classList) {
        el.classList.add(className);
      }
      else if (!hasClass(el, className)) {
        el.className += ' ' + className
      }
    });
  
    removeClass = ((el, className) => {
      if (el === null) {
        return;
      }
  
      if (el.classList) {
        el.classList.remove(className);
      }
      else if (hasClass(el, className)) {
        let reg = new RegExp('(\\s|^)' + className + '(\\s|$)');
  
        el.className = el.className.replace(reg, ' ');
      }
    });
  
    return {
      hasClass:     hasClass,
      addClass:     addClass,
      removeClass:  removeClass
    };
  })();
  
  
  /*********************
   *	Application Code
   ********************/
  /**
   *  @function   readyFunction
   *
   *  @type {Function}
   */
  const readyFunction = (() => {
  
    const KEY_UP    = 38;
    const KEY_DOWN  = 40;
  
    let scrollingClass          = 'js-scrolling',
        scrollingActiveClass    = scrollingClass + '--active',
        scrollingInactiveClass  = scrollingClass + '--inactive',
  
        scrollingTime           = 1350,
        scrollingIsActive       = false,
  
        currentPage             = 1,
        countOfPages            = document.querySelectorAll('.' + scrollingClass + '__page').length,
  
        prefixPage              = '.' + scrollingClass + '__page-',
  
        _switchPages,
        _scrollingUp,
        _scrollingDown,
  
        _mouseWheelEvent,
        _keyDownEvent,
  
        init;
  
    /**
     *  @function _switchPages
     *
     *  @private
     */
    _switchPages = () => {
  
      let _getPageDomEl;
  
        /**
       *  @function _getPageDomEl
       *
       *  @param page
       *  @returns {Element}
       *  @private
         */
      _getPageDomEl      = (page = currentPage) => {
        return document.querySelector(prefixPage + page);
      };
  
      scrollingIsActive  = true;
  
  
      ProjectAPI.removeClass(
        _getPageDomEl(),
        scrollingInactiveClass
      );
      ProjectAPI.addClass(
        _getPageDomEl(),
        scrollingActiveClass
      );
  
      ProjectAPI.addClass(
        _getPageDomEl(currentPage - 1),
        scrollingInactiveClass
      );
  
      ProjectAPI.removeClass(
        _getPageDomEl(currentPage + 1),
        scrollingActiveClass
      );
  
  
      setTimeout(
        () => {
          return scrollingIsActive = false;
        },
        scrollingTime
      );
    };
      /**
     *  @function _scrollingUp
     *
     *  @private
     */
    _scrollingUp = () => {
      if (currentPage === 1) {
        return;
      }
  
      currentPage--;
  
      _switchPages();
    };
      /**
     *  @function _scrollingDown
     *
     *  @private
     */
    _scrollingDown = () => {
      if (currentPage === countOfPages) {
        return;
      }
  
      currentPage++;
  
      _switchPages();
    };
      /**
     *  @function _mouseWheelEvent
     *
     *  @param e
     *  @private
     */
    _mouseWheelEvent = (e) => {
      if (scrollingIsActive) {
        return;
      }
  
      if (e.wheelDelta > 0 || e.detail < 0) {
        _scrollingUp();
      }
      else if (e.wheelDelta < 0 || e.detail > 0) {
        _scrollingDown();
      }
    };
      /**
     *  @function _keyDownEvent
     *
     *  @param e
     *  @private
     */
    _keyDownEvent = (e) => {
      if (scrollingIsActive) {
        return;
      }
  
      let keyCode = e.keyCode || e.which;
  
      if (keyCode === KEY_UP) {
        _scrollingUp();
      }
      else if (keyCode === KEY_DOWN) {
        _scrollingDown();
      }
    };
  
    /**
     *  @function init
     *
     *  @note     auto-launch
     */
    init = (() => {
      document.addEventListener(
        'mousewheel',
        _mouseWheelEvent,
        false
      );
      document.addEventListener(
        'DOMMouseScroll',
        _mouseWheelEvent,
        false
      );
  
      document.addEventListener(
        'keydown',
        _keyDownEvent,
        false
      );
    })();
  
  });
  
  
  /**
   *  Launcher
   */
  DOMReady(readyFunction);
  