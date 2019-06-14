from .scanner import Scanner


class ExchangeScanner(Scanner):
    def get_domain_url(self):
        return self.get_scanner_object().dir_to_scan
