from scrobble.models import LastFMSession
from django.http import HttpResponse

def lastfm_authentication_callback(request):
    """
    When a user authenticates to last.fm, the lastfm server calls this callback.
    We then take the token and store it onto the model.
    """
    token = request.GET['token']
    LastFMSession.create_session(request.user, token)
    return HttpResponse('OK')