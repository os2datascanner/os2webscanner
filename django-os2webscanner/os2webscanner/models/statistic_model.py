from django.db import models

from .scan_model import Scan


class Statistic(models.Model):
    """
    Model for statistics. Statistics contains different counts for a scan.
    """
    # Statistics
    scan = models.ForeignKey(Scan,
                             null=True,
                             verbose_name='scanjob',
                             related_name='scanjob'
                             )

    # Total number of files scraped.
    files_scraped_count = models.IntegerField(default=0)

    files_processed_count = models.IntegerField(default=0)

    files_added_to_the_conversion_queue_count = models.IntegerField(default=0)

    files_skipped_count = models.IntegerField(default=0)

    files_failed_count = models.IntegerField(default=0)

    files_is_dir_count = models.IntegerField(default=0)
