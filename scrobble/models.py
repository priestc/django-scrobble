import datetime
import hashlib
import urllib
import time
from xml.dom.minidom import parseString

import requests

from django.conf import settings
from django.db import models

from utils import queryset_iterator

class LastFMError(Exception):
    pass

class LastFMQuery(object):
    """
    Helper class for signing last.fm requests
    >>> LastFMQuery(arg1='sds', arg2='val').execute('auth.getSession')
    ...xml...
    """

    url = "http://ws.audioscrobbler.com/2.0/"

    def __init__(self, **kwargs):
        self.params = {}
        if 'api_key' not in kwargs.keys():
            kwargs['api_key'] = settings.LASTFM_APIKEY
        for key, value in kwargs.iteritems():
            self.params[key] = value

    def _get_params(self):
        ret = self.params
        ret['api_sig'] = self._calc_signature()
        return ret

    def _as_q(self):
        """
        Return all params encoded in get format.
        """
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

    def execute(self, method):
        """
        Pass in a method, and it will make the call to the lastfm api and
        return the resulting xml document.
        """
        self.params['method'] = method
        
        if method == 'track.updateNowPlaying':
            data = self._get_params()
            make_call = lambda: requests.post(self.url, data)

        elif method == 'auth.getSession':
            q = self.as_q()
            make_call = lambda: requests.get(self.url + '?' + q)
        else:
            raise NotImplemented

        try:
            response = make_call()
        except Exception as exc:
            raise LastFMError('oops, error: %s' % exc)

        xml = parseString(response.content)
        status = xml.getElementsByTagName('lfm')[0].getAttribute('status')

        if status == 'failed':
            code, msg = self._get_error_code_from_response_xml(xml)
            raise LastFMError("%s - %s" % (code, msg))
        elif status == 'ok':
            return xml

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
    def create_session(cls, user, token):
        """
        Given an authentiction token (one time use) create a session and then
        store that session to this table.
        
        u'<?xml version="1.0" ?>
            <lfm status="ok">
                <session>
                    <name>username</name>
                    <key>XXXXX</key>
                    <subscriber>0</subscriber>
                </session>
            </lfm>'
        """
        xml = LastFMQuery(
            token=token,
            api_key=settings.LASTFM_APIKEY,
        ).execute('auth.getSession')

        session = xml.getElementsByTagName('session')[0]
        username = session.getElementsByTagName('name')[0].firstChild.data
        session_key = session.getElementsByTagName('key')[0].firstChild.data

        try:
            obj = cls.objects.get(user=user)
        except cls.DoesNotExist:
            obj = cls.objects.create(user)

        obj.session_key = session_key
        obj.save()

    def now_playing(self, artist, track, album=None, mbid=None, duration=None):
        """
        Send a temporary "now playing" scrobble to last fm as the user
        associated with this session.
        """
        k = dict(artist=artist, album=album, track=track)
        try:
            response = LastFMQuery(**k).execute('track.updateNowPlaying')
        except LastFMError as exc:
            pass #now playing errors we can ignore
    
    def new_scrobble(self, **kwargs):
        """
        keyword arguments are the exact same as Scrobble.__init__
        It makes the new scrobble object, then tries to send all scrobbles
        that need sending.
        """
        kwargs['user'] = self.user
        kwargs['sent'] = False
        new_scrobble = Scrobble(**kwargs)
        
        scrobbles = Scrobble.objects.filter(user=user, sent=False)
        
        try:
            for ss in queryset_iterator(scrobbles, chunksize=50, order_by='timestamp'):
                ss = ScrobbleSet(scrobbles)
                ss.try_to_send()
        except:
            # there were old scrobbles that needed to be sent first, and some of them
            # failed. Queue this one up, and don't bother sending any more.
            # (lastfm is most likely down)
            new_scrobble.send = False
            new_scrobble.save()
        else:    
            # Either there were no old scrobbles to send first, or they
            # all were sent sucessfully! send the new scrobble now.
            new_scrobble.send()

class Scrobble(models.Model):
    """
    When a scrobble is sent an the service is down, the failed scrobble is
    sent to this table where it is retried at a later time. The only scrobbles
    that will get written to the database are scrobbles that have failed.
    """
    timestamp = models.DateTimeField(auto_now_add=True)
    album = models.CharField(max_length=255, null=True)
    track = models.CharField(max_length=255)
    artist = models.CharField(max_length=255)
    albumArtist = models.CharField(max_length=255, null=True)
    duration = models.CharField(max_length=10, null=True)
    streamID = models.IntegerField(null=True)
    chosenByUser = models.BooleanField(default=True)
    context = models.TextField(null=True)
    trackNumber = models.IntegerField(null=True)
    mbid = models.CharField(max_length=10, null=True)
    
    user = models.ForeignKey('auth.User', related_name='lastfm_caches', db_index=True)
    sent = models.BooleanField(default=False)
    
    def __unicode__(self):
        return "%s - %s - %s" % (self.user.username, self.artist, self.track)

class ScrobbleSet(object):
    """
    A set of scrobbles that need to be sent to the server.
    """
    fields = ('timestamp', 'album', 'track', 'artist', 'albumArtist',
    'duration', 'streamId', 'chodenByUser', 'context', 'trackNumber', 'mbid')
    
    def __init__(self, scrobbles):
        self.scrobbles = scrobbles

    def post_data(self):
        """
        Encode these scrobbles into a properly formatted dictionary as
        specified by the last.fm documentation.
        """
        post = {}
        for index, scrobble in enumerate(self.scrobbles):
            for field in self.fields:
                val = getattr(scrobble, field, None)
                if type(val) is datetime.datetime:
                    # convert any datetime object to an integer timestamp
                    val = "%.0f" % time.mktime(val.timetuple())
                if val is None:
                    continue # don't put keys for values that aren't there.
                key = '{0}[{1}]'.format(field, index)
                post[key] = val
        
        return post
    
    def set_success(self):
        """
        All of these scrobbles were sent successfully! mark them as sent.
        """
        self.scrobbles.update(sent=True)
    
    def try_to_send(self):
        try:
            response = LastFMQuery(**self.post_data).execute('track.scrobble')
        except:
            # last.fm is down, retry on next attempt
            pass
        else:
            self.set_sucess()










