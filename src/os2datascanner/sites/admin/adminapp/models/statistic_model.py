from django.db import models

from .scans.scan_model import Scan


class Statistic(models.Model):
    """
    Model for statistics. Statistics contains different counts for a scan.
    """
    # Statistics
    scan = models.ForeignKey(
        Scan,
        null=True,
        verbose_name='scanjob',
        related_name='scanjob',
        on_delete=models.CASCADE,
    )

    # Total number of files scraped.
    files_scraped_count = models.IntegerField(default=0)

    files_processed_count = models.IntegerField(default=0)

    files_added_to_the_conversion_queue_count = models.IntegerField(default=0)

    files_skipped_count = models.IntegerField(default=0)

    files_failed_count = models.IntegerField(default=0)

    files_is_dir_count = models.IntegerField(default=0)

    # Information from the prescanner
    supported_size = models.IntegerField(default=0)
    supported_count = models.IntegerField(default=0)
    relevant_size = models.IntegerField(default=0)
    relevant_count = models.IntegerField(default=0)
    relevant_unsupported_size = models.IntegerField(default=0)
    relevant_unsupported_count = models.IntegerField(default=0)


class TypeStatistics(models.Model):
    statistic = models.ForeignKey(
        Statistic,
        null=False,
        verbose_name='Statistics',
        related_name='types',
        on_delete=models.CASCADE,
    )

    type_name = models.CharField(max_length=256)
    count = models.IntegerField(default=0)
    size = models.IntegerField(default=0)
