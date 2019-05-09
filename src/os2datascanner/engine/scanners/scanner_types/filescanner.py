from .scanner import Scanner

from ....sites.admin.adminapp.models.statistic_model import Statistic, TypeStatistics


class FileScanner(Scanner):

    def get_domain_urls(self):
        """Return a list of valid domain urls."""
        domains = []
        for d in self.valid_domains:
            domains.append(d.filedomain.mountpath)
        return domains

    def get_domain_objects(self):
        """
        Returns a list of valid domain objects
        :return: domain list
        """
        domains = []
        for domain in self.valid_domains:
            domains.append(domain.filedomain)
        return domains

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
