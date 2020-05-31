import os
import json
from django.utils import timezone
from django.http import StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt

from openra.models import Maps, Rating


@csrf_exempt
def jRating(request, arg):

    def jRatingError(arData):
        response = StreamingHttpResponse(json.dumps(arData), content_type="application/javascript")
        return response

    if request.method == 'POST':
        if request.POST.get('action', "").strip() == "rating":
            arData = {}
            arData['item_type'] = arg
            arData['item_id'] = request.POST.get('idBox', "")
            arData['rate_by_user'] = request.POST.get('rate', "")
            arData['user_id'] = request.user.id

            ratingObject = Rating.objects.filter(
                ex_id=arData['item_id'],
                ex_name=arData['item_type'],
                user=request.user.id)
            if ratingObject:
                Rating.objects.filter(
                    ex_id=arData['item_id'],
                    ex_name=arData['item_type'],
                    user=request.user.id).update(rating=arData['rate_by_user'])
            else:

                transac = Rating(
                    user=request.user,
                    ex_id=arData['item_id'],
                    ex_name=arData['item_type'],
                    rating=arData['rate_by_user'],
                    posted=timezone.now(),
                )
                transac.save()

            rating_score = 0.0
            ratingObject = Rating.objects.filter(ex_id=arData['item_id'], ex_name=arData['item_type'])
            for item in ratingObject:
                rating_score += item.rating
            rating_score = rating_score / float(len(ratingObject))
            rating_score = float("{0:.2f}".format(rating_score))

            if arData['item_type'] == 'map':
                Maps.objects.filter(id=arData['item_id']).update(rating=rating_score)

            arData['rating'] = rating_score

            response = StreamingHttpResponse(json.dumps(arData, indent=4), content_type="application/javascript")
            return response
        else:
            return jRatingError({'status': 'error'})
    else:
        return jRatingError({'status': 'error'})
