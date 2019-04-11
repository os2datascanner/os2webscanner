import logging
import errno
import magic

from scrapy.http import Request, HtmlResponse
from scrapy.exceptions import IgnoreRequest
from os2webscanner.utils import capitalize_first, get_codec_and_string, secure_save

from utils import as_file_uri, as_path
from ..processors.processor import Processor
from ..scanner_types.pre_analysis import PreDataScanner
from .scanner_spider import ScannerSpider


class FileSpider(ScannerSpider):
    """A spider which uses a scanner to scan all data it comes across."""

    name = 'filescanner'
    magic = magic.Magic(mime=True)
    custom_settings = {
        'DOWNLOADER_MIDDLEWARES': {'scanners.middlewares.middlewares.ExclusionRuleDownloaderMiddleware': 1100,
                                   'scanners.middlewares.filescan_middleware.FileScanLastModifiedCheckMiddleware': 1200
                                   },
        'SPIDER_MIDDLEWARES': {'scanners.middlewares.middlewares.ExclusionRuleMiddleware': 1000}
    }

    def __init__(self, scanner, runner, *a, **kw):
        """Initialize the ScannerSpider with a Scanner object.

        The configuration will be loaded from the Scanner.
        """
        super().__init__(scanner=scanner, runner=runner, *a, **kw)

    def setup_spider(self):
        logging.info("Initializing spider of type FileSpider")
        for path in self.allowed_domains:
            path = self.add_correct_file_path_prefix(path)
            self.start_urls.append(path)

    def start_requests(self):
        """Return requests for all starting URLs AND sitemap URLs."""
        logging.info("Starting requests")
        requests = []
        for url in self.start_urls:
            # Some of the files are directories. We handle them in handle_error method.
            requests.extend(self.append_file_request(url))

        return requests

    def add_correct_file_path_prefix(self, path):
        """
        Helper method for making sure file path starts with file://.
        This prefix is needed by scrapy, or else scrapy does not know it is a file path.
        :param path: path to folder or file
        :return: path with prefix file://
        """
        logging.info("Start path {0}".format(path))
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
                logging.error('UnicodeEncodeError in handle_error_method: {}'.format(uee))
                logging.error('Error happened for file: {}'.format(stringdata))

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

        logging.info('Starting folder analysis...')
        for path, info in files.nodes.items():
            if info['filetype']['relevant'] and info['filetype']['supported']:
                relevant_files += 1
                relevant_file_size += info['size']
                filemap.append(as_file_uri(path))
        logging.info('Found {0} relevant files ({1} bytes).'.format(
            relevant_files, relevant_file_size))
        logging.info('Folder analysis completed...')
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
            logging.debug('Failure value: {}'.format(str(failure.value)))
            if isinstance(failure.value, IOError) \
                    and failure.value.errno == errno.EISDIR:
                logging.debug('File that is failing: {0}'.format(
                    failure.value.filename))

                return self.append_file_request(
                    as_file_uri(failure.value.filename),
                )
            elif isinstance(failure.value, IOError):
                status_message = str(failure.value.errno)

        self.broken_url_save(status_code, status_message, url)

    def scan(self, response):
        """Scan a response, returning any matches."""

        mime_type = self.get_mime_type(response)

        # Save the URL item to the database
        if (Processor.mimetype_to_processor_type(mime_type) == 'ocr'
            and not self.scanner.do_ocr):
            # Ignore this URL
            return

        domain = self.scanner.valid_domains.first()
        old = ''
        new = ''
        if 'type' in self.scanner.configuration:
            scanner_type = self.scanner.configuration["type"]
            if scanner_type == 'FileScanner':
                old = domain.filedomain.mountpath
                new = domain.filedomain.url
            elif scanner_type == 'ExchangeScanner':
                old = as_file_uri(domain.exchangedomain.dir_to_scan)
                new = domain.exchangedomain.url

        url_object = self.url_save(mime_type,
                                   response.request.url.replace(
                                       old, new)
                                   )

        data = response.body

        self.scanner.scan(data, url_object)
