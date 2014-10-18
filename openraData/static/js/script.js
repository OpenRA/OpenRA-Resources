/*	id 1: prevent scrolling inside of block */
	$(document).ready(function (){
		noScroll('popup-content-wrapper');
	});

	function noScroll(className) {
		$( '.'+className ).bind( 'mousewheel DOMMouseScroll', function ( e ) {
			var e0 = e.originalEvent,
				delta = e0.wheelDelta || -e0.detail;
			this.scrollTop += ( delta < 0 ? 1 : -1 ) * 30;
			e.preventDefault();
		});
	}
/*	id 1: end */


/*	id 2: change site background depending on client's time */
	function backgroundDayNight(prefix, ext) {
		var d = new Date();
		if (d.getHours() <= 23 || d.getHours() >= 7) {
			$('body').css('background-image', 'url("/static/images/bg'+prefix+'.'+ext+'")');
		}
		else {
			$('body').css('background-image', 'url("/static/images/bg-night'+prefix+'.'+ext+'")');
		}
	}

	$(document).ready(function() {
		backgroundDayNight("", "svg");
	});
/*	id 2: end */


/*	id 3: svg fallback to png if not supported */
	$(document).ready(function(){
		function supportsSVG() {
			return !!document.createElementNS && !!document.createElementNS('http://www.w3.org/2000/svg','svg').createSVGRect;
		}
		$(function() {
			if (!supportsSVG()) {
				document.documentElement.className += ' no-svg';
				backgroundDayNight("-fallback", "png");
				$('img[src$=".svg"]').attr('src', function() {
					return $(this).attr('src').replace('.svg', '-fallback.png');
				});
			}
		});
	});
/*	id 3: end */