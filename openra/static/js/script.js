/*	code: prevent scrolling inside of block */
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
/*	code: end */


/*	code: setBackground function of background fallback */
	function setBackground(prefix, ext) {
		$('body').css('background-image', 'url("/static/images/bg'+prefix+'.'+ext+'")');
	}

	$(document).ready(function() {
		setBackground("", "svg");
	});
/*	code: end */


/*	code: svg fallback to png if not supported */
	$(document).ready(function(){
		function supportsSVG() {
			return !!document.createElementNS && !!document.createElementNS('http://www.w3.org/2000/svg','svg').createSVGRect;
		}
		$(function() {
			if (!supportsSVG()) {
				document.documentElement.className += ' no-svg';
				setBackground("-fallback", "png");
				$('img[src$=".svg"]').attr('src', function() {
					return $(this).attr('src').replace('.svg', '-fallback.png');
				});
			}
		});
	});
/*	code: end */


/*	code: select text with one click */
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
/*	code: end */


/*	code: paging related - show only 1 cell with "..." */
	$(document).ready(function() {
		var elements_paging = document.getElementsByClassName('no-page-before');
		$(elements_paging[0]).removeClass('hide_block');
		var elements_paging = document.getElementsByClassName('no-page-after');
		$(elements_paging[0]).removeClass('hide_block');
	});
/*	code: end */


/*	code: jRating (5 star rating) */
	$(document).ready(function() {
		$('.five-star-rating').jRating({
			bigStarsPath: '/static/js/jRating/icons/star.png',
			smallStarsPath: '/static/js/jRating/icons/small.png',
			phpPath: '/ajax/jRating/' + $('.five-star-rating').data('type') + '/',
			length: 5,
			canRateAgain: false,
			nbRates: 1,
			rateMax: 5,
			decimalLength: 1,
			onSuccess: function (response){
			},
		});
	});
/*	code: end */

/*  code: more SHP previews */
	$(document).ready(function() {
		map_shp_height = false;
		if ( $('.cSHP').length > 5 )
		{
			map_shp_height = $('.map_shp').height();
			$('.map_shp').css({ height: '100px' });
			$('.top-bottom-double-arrow').show();
		}

		$('.top-bottom-double-arrow').click(function() {
			if ( map_shp_height )
			{
				if ( $('.map_shp').height() == 100)
				{
					$('.map_shp').animate({ height: map_shp_height }, 'slow', function() {
						$('.map_shp').css({ height: '100%' });
						map_shp_height = $('.map_shp').height();
					});
				}
				else
				{
					$('.map_shp').animate({ height: '100' }, 'slow');
				}
			}
		});
	});
/*	code: end */