from django.core.management.base import BaseCommand, CommandError

from distributed.models import DistributedSource


class Command(BaseCommand):
    args = ''
    help = 'Sync all the remote sources'

    def handle(self, *args, **options):
        for source in DistributedSource.objects.filter(active=True):
            source.sync()
