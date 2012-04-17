from django.core.management.base import NoArgsCommand
from django.core.urlresolvers import reverse

class Command(NoArgsCommand):
    """
    Print out the callback you should enter to the lastfm site.
    """
    def handle(self, *args, **options):
        path = reverse('lastfm_auth_callback')
        print "Your callback: {path}".format(path=path)