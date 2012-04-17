from django.conf import settings
from django import template
register = template.Library()

@register.simple_tag
def scrobble_auth_link():
    """
    Create a link to the last FM site where the user can enter their credentials
    So we can scroble on the user's behalf.
    """
    key = settings.LASTFM_APIKEY
    link = "http://www.last.fm/api/auth/?api_key={key}".format(key=key)
    return """<a href="{link}">Enable scrobling</a>""".format(link=link)