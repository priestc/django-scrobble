from django.conf.urls.defaults import *

urlpatterns = patterns('scrobble',
    url(r'^auth_callback/?$', 'lastfm_authentication_callback', name="lastfm_auth_callback")
)