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
		if (d.getHours() >= 23 || d.getHours() <= 7) {
			$('body').css('background-image', 'url("/static/images/bg-night'+prefix+'.'+ext+'")');
		}
		else {
			$('body').css('background-image', 'url("/static/images/bg'+prefix+'.'+ext+'")');
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

/*	id 4: select text with one click */
function selectText(containerid) {
	if (document.selection) {
		var range = document.body.createTextRange();
		range.moveToElementText(document.getElementById(containerid));
		range.select();
	} else if (window.getSelection) {
		var range = document.createRange();
		range.selectNode(document.getElementById(containerid));
		window.getSelection().addRange(range);
	}
}
/*	id 4: end */

/*	id 5: paging related - show only 1 cell with "..." */
$(document).ready(function() {
	var elements_paging = document.getElementsByClassName('no-page-before');
	$(elements_paging[0]).removeClass('hide_block');
	var elements_paging = document.getElementsByClassName('no-page-after');
	$(elements_paging[0]).removeClass('hide_block');
});
/*	id 5: end */


/*	-id 6: jRating (5 star rating) */
$(document).ready(function() {
	$('.five-star-rating').jRating({
		bigStarsPath: '/static/js/jRating/icons/star.png',
		smallStarsPath: '/static/js/jRating/icons/small.png',
		phpPath: '/ajax/jRating/',
		length: 5,
		canRateAgain: false,
		nbRates: 1,
		rateMax: 5,
		decimalLength: 1,
		onSuccess: function (response){
		},
	});
});
/*	id 6: end */