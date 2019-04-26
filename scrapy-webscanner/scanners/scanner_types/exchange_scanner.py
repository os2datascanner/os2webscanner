from .scanner import Scanner


class ExchangeScanner(Scanner):

    def get_domain_urls(self):
        """Return a list of valid domain urls."""
        domains = []
        for d in self.valid_domains:
            domains.append(d.exchangedomain.dir_to_scan)
        return domains

    def get_domain_objects(self):
        """
        Returns a list of valid domain objects
        :return: domain list
        """
        domains = []
        for domain in self.valid_domains:
            domains.append(domain.exchangedomain)
        return domains
