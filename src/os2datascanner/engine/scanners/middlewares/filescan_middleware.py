import os
import datetime
import dateutil.tz

from urllib.parse import unquote

import structlog

from scrapy.exceptions import IgnoreRequest

from .middlewares import LastModifiedCheckMiddleware

logger = structlog.get_logger()


class FileScanLastModifiedCheckMiddleware(LastModifiedCheckMiddleware):

    def __init__(self, crawler):
        super().__init__(crawler)

    def process_request(self, request, spider):
        """Process a spider request."""
        return None

    def process_response(self, request, response, spider):
        """Process a spider response."""
        # Don't run the check if it's not specified by the spider...
        if request.meta.get('skip_modified_check', False):
            return response
        # ... or by the scanner
        if not spider.scanner.do_last_modified_check:
            return response

        # Check the Last-Modified header to see if the content has been
        # updated since the last time we checked it.
        if self.has_been_modified(request, response, spider):
            logger.debug("Page has been modified since Last-Modified",
                         response=response)
            return response
        else:
            # Ignore the request, since the content has not been modified
            self.stats.inc_value('last_modified_check/pages_skipped')
            raise IgnoreRequest

    def has_been_modified(self, request, response, spider):
        """Return whether the response was modified since last seen.

        We check against the database here.
        If the response has been modified, we update the database.
        If there is no stored last modified date, we save one.
        """
        try:
            # Removes unneeded prefix
            file_path = response.url.replace('file://', '')
            # Transform URL string into normal string
            file_path = unquote(file_path)
            # Retrieves file timestamp from mounted drive
            last_modified = datetime.datetime.fromtimestamp(
                os.path.getmtime(file_path),
                tz=dateutil.tz.UTC,
            )
        except OSError:
            logger.exception('Error occured while getting last modified',
                             file_path=file_path)
            return True

        if last_modified is not None:
            logger.debug(
                "Comparing timestamps in header and scan",
                header_value=last_modified,
                scan_value=spider.runner.last_started,
                file_path=file_path,
            )
            last_scan_started_at = spider.runner.last_started
            if not last_scan_started_at or \
                            last_modified > last_scan_started_at:
                return True
            else:
                return False
        else:
            # If there is no Last-Modified header, we have to assume it has
            # been modified.
            logger.debug('No Last-Modified header found at all.',
                         file_path=file_path)
            return True
