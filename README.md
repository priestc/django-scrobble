## Installation ##
* `pip install django-scrobble`
* add to `INSTALLED_APPS`
* run `python manage.py syncdb`

## Usage ##
Go to last.fm to sign up for an API account.
Somewhere in your templates place the `{% scrobble_auth_link %}` This will create the link that your users will click to authenticate the user's lastfm account with your django application.

## Settings ##

* `LASTFM_APIKEY` - your Last.fm API key.
* `LASTFM_SECRET` - your last.fm secret key.