import hashlib
import urllib
from xml.dom.minidom import parseString

import requests

from django.conf import settings
from django.db import models

class LastFMError(Exception):
    pass

class LastFMQuery(object):
    """
    Helper class for signing last.fm requests
    >>> LastFMQuery(api_key='sds', arg='val').make_url('auth.getSession')
    http://ws.audioscrobbler.....
    """
    def __init__(self, **kwargs):
        self.params = {}
        for key, value in kwargs.iteritems():
            self.params[key] = value
            
    def _get_params(self):
        ret = self.params
        ret.update({'api_sig': self._calc_signature()})
        return ret

    def as_q(self):
        return urllib.urlencode(self._get_params())

    def _calc_signature(self):
        """
        Last FM has this dumb signature thing where to have to include with
        every request a md5 hash of all your params in alphabetical order...
        """
        sig_string = ''
        for key in sorted(self.params.iterkeys()):
            sig_string += key + str(self.params[key])
        return hashlib.md5(sig_string + settings.LASTFM_SECRET).hexdigest()

    def _make_url(self, method):
        """
        Construct an api call using the method passed, etc: 'auth.getSession'
        """
        self.params.update({'method': method})
        q = self.as_q()
        return "http://ws.audioscrobbler.com/2.0/?" + q

    def execute(self, method):
        try:
            url = self._make_url(method)
            response = requests.get(url)
        except Exception as exc:
            raise LastFMError('oops, error: %s' % exc)
        
        xml = parseString(response.content)
        status = xml.getElementsByTagName('lfm')[0].getAttribute('status')
        
        if status == 'failed':
            code, msg = self._get_error_code_from_response_xml(xml)
            raise LastFMError("%s - %s" % (code, msg))
        elif status == 'ok':
            return True
        
    def _get_error_code_from_response_xml(self, xml):
        """
        Given a requests response from lastfm api, parse out the error code,
        (if any)
        """
        error = xml.getElementsByTagName('error')
        if len(error):
            code = error[0].getAttribute('code')
            msg = error[0].firstChild.data
            return (code, msg)
        raise LastFMError("Can't find error in response")
        

class LastFMSession(models.Model):
    user = models.ForeignKey('auth.User', related_name='lastfm_token', primary_key=True)
    session_key = models.CharField(max_length=255)
    
    def __unicode__(self):
        return "%s - %s" % (self.user.username, self.session_key)
    
    @classmethod
    def create_session(user, token):
        """
        Given an authentiction token (one time use) create a session and then
        store that session to this table.
        """
        response = LastFMQuery(
            token=token,
            api_key=settings.LASTFM_APIKEY,
        ).execute('auth.getSession')

        token = response.token

        try:
            obj = cls.objects.get(user=user)
        except cls.DoesNotExist:
            obj = cls.objects.create(user)

        obj.token = token
        obj.save()

    def now_playing(self, artist, track, album=None, mbid=None, duration=None):
        """
        Send a scrobble to last fm as the user associated with this session.
        """
        k = dict(artist=artist, album=album, track=track, sk=self.session_key)
        response = LastFMQuery(**k).execute('track.updateNowPlaying')
        return