import errno
import magic

import structlog

from scrapy.http import Request
from scrapy.exceptions import IgnoreRequest
from os2datascanner.projects.admin.adminapp.utils import get_codec_and_string

from ...utils import as_file_uri, as_path
from ..processors.processor import Processor
from ..scanner_types.pre_analysis import PreDataScanner
from .scanner_spider import ScannerSpider


class FileSpider(ScannerSpider):
    """A spider which uses a scanner to scan all data it comes across."""

    name = 'filescanner'
    magic = magic.Magic(mime=True)
    custom_settings = {
        'DOWNLOADER_MIDDLEWARES': {'os2datascanner.engine.scanners.middlewares.middlewares.ExclusionRuleDownloaderMiddleware': 1100,
                                   'os2datascanner.engine.scanners.middlewares.filescan_middleware.FileScanLastModifiedCheckMiddleware': 1200
                                   },
        'SPIDER_MIDDLEWARES': {'os2datascanner.engine.scanners.middlewares.middlewares.ExclusionRuleMiddleware': 1000}
    }

    def __init__(self, scanner, runner, *a, **kw):
        """Initialize the ScannerSpider with a Scanner object.

        The configuration will be loaded from the Scanner.
        """
        super().__init__(scanner=scanner, runner=runner, *a, **kw)

    def setup_spider(self):
        self.logger.info("Initializing spider of type FileSpider")
        for path in self.allowed_domains:
            path = self.add_correct_file_path_prefix(path)
            self.start_urls.append(path)

    def start_requests(self):
        """Return requests for all starting URLs AND sitemap URLs."""
        self.logger.info("Starting requests")

        requests = []
        for url in self.start_urls:
            # Some of the files are directories. We handle them in handle_error method.
            try:
                requests.extend(self.append_file_request(url))
            except Exception as exc:
                self.logger.exception('adding request failed',
                                      url=url, exc_info=exc)

        return requests

    def add_correct_file_path_prefix(self, path):
        """
        Helper method for making sure file path starts with file://.
        This prefix is needed by scrapy, or else scrapy does not know it is a file path.
        :param path: path to folder or file
        :return: path with prefix file://
        """
        self.logger.debug("add_correct_file_path_prefix", path=path)
        return as_file_uri(path)

    def append_file_request(self, url):
        files = self.file_extractor(url)
        requests = []
        for file in files:
            codecs, stringdata = get_codec_and_string(file)
            stringdata = stringdata.replace('#', '%23').replace('?', '%3F')
            try:
                requests.append(Request(stringdata, callback=self.scan,
                                        errback=self.handle_error))
            except UnicodeEncodeError as uee:
                self.logger.exception('UnicodeEncodeError in append_file_request',
                                      url=url, exc_info=uee, file=file)

        return requests

    def file_extractor(self, filepath):
        """
        Generate sitemap for filescan using walk dir path
        :param filepath: The path to the files
        :return: filemap
        """

        path = as_path(filepath)
        files = PreDataScanner(path, detection_method='mime')
        filemap = []
        relevant_files = 0
        relevant_file_size = 0

        files.update_stats()
        self.scanner.set_statistics(
            files.stats['supported_file_count'],
            files.stats['supported_file_size'],
            files.stats['relevant_file_count'],
            files.stats['relevant_file_size'],
            files.stats['relevant_unsupported_count'],
            files.stats['relevant_unsupported_size'])
        summaries = files.summarize_file_types()
        for k, v in summaries["super"].items():
            self.scanner.add_type_statistics(k, v["count"], sum(v["sizedist"]))
        for k, v in summaries["sub"].items():
            if "supergroup" in v:
                group_name = v["supergroup"] + "/" + k
            else:
                group_name = k
            self.scanner.add_type_statistics(group_name, v["count"], sum(v["sizedist"]))

        self.logger.debug('Starting folder analysis...')
        for path, info in files.nodes.items():
            if info['filetype']['relevant'] and info['filetype']['supported']:
                relevant_files += 1
                relevant_file_size += info['size']
                filemap.append(as_file_uri(path))
        self.logger.info('Folder analysis',
                         relevant_files=relevant_files,
                         relevant_file_size=relevant_file_size)
        return filemap

    def handle_error(self, failure):
        """Handle an error due to a non-success status code or other reason.

        If link checking is enabled, saves the broken URL and referrers.
        """
        # If scanner is type filescan
        url = getattr(failure.value, "filename", "Not Filled")
        status_message = "Not filled"
        status_code = -1

        if isinstance(failure.value, IgnoreRequest):
            # The file hasn't changed since the last scan
            return
        else:
            # If file is a directory loop through files within
            if isinstance(failure.value, IOError) \
                    and failure.value.errno == errno.EISDIR:
                self.logger.debug('file_spider_error',
                                  exc_info=failure.value,
                                  file=failure.value.filename)

                return self.append_file_request(
                    as_file_uri(failure.value.filename),
                )
            elif isinstance(failure.value, IOError):
                status_message = str(failure.value.errno)

        self.logger.debug('file_spider_error',
                          exc_info=failure.value,
                          failure=failure)

        self.broken_url_save(status_code, status_message, url)
