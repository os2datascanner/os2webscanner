"""Command for dispatching summary reports from crontab."""

from django.core.management.base import BaseCommand

from os2webscanner.utils import dispatch_pending_summaries


class Command(BaseCommand):

    """Send out pending summary reports."""

    help = "Send out pending summary reports"

    def handle(self, *args, **options):
        """Execute the command."""
        dispatch_pending_summaries()
