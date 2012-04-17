from scrobble.models import LastFMAuthorization

def lastfm_authentication_callback(request):
    """
    When a user authenticates to last.fm, the lastfm server calls this callback.
    We then take the token and store it onto the model.
    """
    token = request.GET['token']
    session_key = response.content
    LastFMAuthorization.set_session(request.user, session_key)
    return HttpResponse('OK')