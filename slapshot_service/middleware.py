from django.http import HttpResponsePermanentRedirect


class AppendSlashBeforeAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.endswith('/') and '.' not in request.path.split('/')[-1]:
            return HttpResponsePermanentRedirect(request.path + '/')
        return self.get_response(request)
