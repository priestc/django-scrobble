## Installation ##
* `pip install django-scrobble`
* add to `INSTALLED_APPS`
* run `python manage.py syncdb`
* add the scrobble urls somewhere to your projects urls:
    url(r'scrobble/', include('scrobble.urls')),
* enter your callback url into the last.fm callback field. To get your callback, run the management command `python manage.py lastfm_callback`

## Usage ##
Go to last.fm to sign up for an API account.
Somewhere in your templates place `{% load scrobble %}{% scrobble_auth_link %}` This will create the link that your users will click to authenticate their lastfm account with your django application.

After the user has authenticated with lastfm, you can send scrobbles by the following:

    >>> session = LastFMSession.objects.get(user=request.user)
    >>> session.now_playing(artist='Pink Floyd', track='Not Now John')

## Settings ##

* `LASTFM_APIKEY` - your Last.fm API key.
* `LASTFM_SECRET` - your last.fm secret key.