from .scanner import Scanner
from .filescanner import FileScanner


class ExchangeScanner(FileScanner):
    def get_domain_url(self):
        return self.get_scanner_object().dir_to_scan
