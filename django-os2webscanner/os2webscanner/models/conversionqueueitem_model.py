import os
import shutil

from django.db import models

from .url_model import Url


class ConversionQueueItem(models.Model):

    """Represents an item in the conversion queue."""
    url = models.ForeignKey(
        Url,
        null=False,
        verbose_name='Url',
        on_delete=models.CASCADE,
    )

    file = models.CharField(max_length=4096, verbose_name='Fil')
    type = models.CharField(max_length=256, verbose_name='Type')
    page_no = models.IntegerField(null=True, verbose_name='Side')

    # Note that SUCCESS is indicated by just deleting the record
    NEW = "NEW"
    PROCESSING = "PROCESSING"
    FAILED = "FAILED"

    status_choices = (
        (NEW, "Ny"),
        (PROCESSING, "I gang"),
        (FAILED, "Mislykket"),
    )

    status = models.CharField(max_length=10, choices=status_choices,
                              default=NEW, verbose_name='Status')

    process_id = models.IntegerField(blank=True, null=True,
                                     verbose_name='Proces id')

    process_start_time = models.DateTimeField(
        blank=True, null=True, verbose_name='Proces starttidspunkt'
    )

    @property
    def file_path(self):
        """Return the full path to the conversion queue item's file."""
        return self.file

    @property
    def tmp_dir(self):
        """The path to the temporary dir associated with this queue item."""
        return os.path.join(
            self.url.scan.scan_dir,
            'queue_item_%d' % (self.pk)
        )

    def delete_tmp_dir(self):
        """Delete the item's temp dir if it is writable."""
        if os.access(self.tmp_dir, os.W_OK):
            shutil.rmtree(self.tmp_dir, True)

    class Meta:
        abstract = False
