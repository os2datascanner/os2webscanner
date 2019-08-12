import pathlib

from os2datascanner.engine.utils import as_path
from .scanner import Scanner
from .scanner_with_statistics import ScannerWithStatistics

from django.conf import settings


class FileScanner(Scanner, ScannerWithStatistics):
    def get_domain_url(self):
        """Return a list of valid domain urls."""
        return self.get_scanner_object().mountpath

    def get_location_for(self, url):
        try:
            p = as_path(url)
            p = p.relative_to(as_path(self.get_domain_url()))
            p = pathlib.PureWindowsPath(self.scan_object.webscanner.url) / p

            return super().get_location_for(p.as_uri())
        except ValueError:
            # If fixing up the mountpoint failed, then presumably we're running
            # in engine2 mode?
            assert settings.USE_ENGINE2
            return super().get_location_for(url)
