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