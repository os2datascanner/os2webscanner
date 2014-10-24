

from django.core.management.base import BaseCommand, CommandError

from os2webscanner.utils import dispatch_pending_summaries


class Command(BaseCommand):
    help = "Send out pending summary reports"

    def handle(self, *args, **options):
        dispatch_pending_summaries()
