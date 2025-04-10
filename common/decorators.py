import json

from django.http import HttpResponse
from django.shortcuts import reverse
from django.http.response import HttpResponseRedirect


def allow_canteen(fuction):
    def wrapper(request, *args, **kwargs):
        current_user = request.user
        if not current_user.is_canteen:
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                response_data = {
                    "status": "error",
                    "title": "Unauthorized Access",
                    "message": "You can't perform this action"
                }
                return HttpResponse(json.dumps(response_data),content_type="application/json")

            else:
                return HttpResponseRedirect(reverse("canteen:logout"))

        
        return fuction(request, *args, **kwargs)

    return wrapper