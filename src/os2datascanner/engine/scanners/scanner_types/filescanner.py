import pathlib

from os2datascanner.engine.utils import as_path
from .scanner import Scanner

from os2datascanner.projects.admin.adminapp.models.statistic_model import Statistic, TypeStatistics


class FileScanner(Scanner):
    def get_domain_url(self):
        """Return a list of valid domain urls."""
        return self.get_scanner_object().mountpath

    def get_location_for(self, url):
        p = as_path(url)
        p = p.relative_to(as_path(self.get_domain_url()))
        p = pathlib.PureWindowsPath(self.scan_object.webscanner.url) / p

        return super().get_location_for(p.as_uri())

    def set_statistics(self,
            supported_count, supported_size,
            relevant_count, relevant_size,
            relevant_unsupported_count, relevant_unsupported_size):
        stats = Statistic.objects.get_or_create(scan=self.scan_object)[0]
        stats.supported_count = supported_count
        stats.supported_size = supported_size
        stats.relevant_count = relevant_count
        stats.relevant_size = relevant_size
        stats.relevant_unsupported_count = relevant_unsupported_count
        stats.relevant_unsupported_size = relevant_unsupported_size
        stats.save()

    def add_type_statistics(self, name, count, size):
        stats = Statistic.objects.get_or_create(scan=self.scan_object)[0]
        type_stats = TypeStatistics(statistic=stats)
        type_stats.type_name = name
        type_stats.count = count
        type_stats.size = size
        type_stats.save()
