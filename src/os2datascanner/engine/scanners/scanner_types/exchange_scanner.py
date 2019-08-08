from .scanner import Scanner
from .scanner_with_statistics import ScannerWithStatistics


class ExchangeScanner(Scanner, ScannerWithStatistics):
    def get_domain_url(self):
        return self.get_scanner_object().dir_to_scan

    def get_location_for(self, url):
        p = as_path(url)

        return super().get_location_for(p.as_uri())
