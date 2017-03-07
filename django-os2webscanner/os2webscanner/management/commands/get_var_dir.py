"""Command for dispatching summary reports from crontab."""

from django.core.management.base import BaseCommand


class Command(BaseCommand):

    """Print this installation's VAR directory."""

    help = "Print the path to the VAR directory"

    def handle(self, *args, **options):
        """Execute the command."""
        from django.conf import settings
        print settings.VAR_DIR
