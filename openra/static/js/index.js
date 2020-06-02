function confirmDelete(what){
  var agree = confirm('Are you sure you want to delete this '+what+'?')
  if (agree) return true
  else return false
}

// jRating
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
        console.log('yes')
      },
    });
});
