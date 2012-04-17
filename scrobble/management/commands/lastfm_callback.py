from django.core.management.base import NoArgsCommand
from django.core.urlresolvers import reverse

class Command(NoArgsCommand):
    """
    Print out the callback you should enter to the lastfm site.
    """
    def handle(self, *args, **options):
        domain = Sites.objects.get_current()
        return "Your callback: {domain}{path}".format(
            path=reverse('lastfm_auth_callback'),
            domain=domain
        )