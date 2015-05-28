# -*- coding: utf-8 -*-

from scrapy import signals, log
from scrapy.exceptions import NotConfigured, DontCloseSpider, DropItem
from threading import Lock, Thread
from items import MeasurerItem

import Queue
import os
import shutil
import time
import json
import mimetypes
import magic

from scanner.processors import libreoffice, ocr, pdf
from scanner.processors.processor import Processor

# Tell the OCR processor not to auto-process generated text
Processor.processor_by_type('ocr').auto_process_text = False

converter_types = [
    'libreoffice',
    'ocr',
    'pdf'
]

class MockObject(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

class MeasuringExtension(object):
    def __init__(self):
        self.queues = {}
        self.threads = {}
        self.lock = Lock()
        self.counts = {}
        self.item_count = 0
        self.md5s = set()
        self.settings = None
        for x in converter_types:
            self.queues[x] = Queue.Queue()

    @classmethod
    def from_crawler(cls, crawler):
        # instantiate the extension object
        ext = cls()

        # connect the extension object to signals
        crawler.signals.connect(ext.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(ext.spider_closed, signal=signals.spider_closed)
        crawler.signals.connect(ext.spider_idle, signal=signals.spider_idle)
        crawler.signals.connect(ext.item_scraped, signal=signals.item_scraped)
        
        ext.settings = crawler.settings

        # return the extension object
        return ext

    def process_queue(self, conv_type):
        queue = self.queues[conv_type]
        processor = Processor.processor_by_type(conv_type)
        while True:
            item = queue.get()
            try:
                work_dir = os.path.join(
                    self.settings['VAR_DIR'],
                    "scan-measure",
                    item['md5']
                )
                if not os.path.exists(work_dir):
                    os.makedirs(work_dir)
                file_path = os.path.join(work_dir, item['filename'])
                f = open(file_path, 'w')
                f.write(item['content'])
                f.close()
                scanner_pseudo_item = MockObject(
                    file_path=file_path,
                    url=MockObject(
                        scan = MockObject(
                            do_ocr = True
                        )
                    )
                )

                start_time = time.time()
                processor.convert(scanner_pseudo_item, work_dir)
                item['conversion_time'] = time.time() - start_time

                self.count_item(item)

                if os.path.exists(file_path):
                    os.remove(file_path)

                self.add_files_from_dir(work_dir)
            except Exception as e:
                log.err("Exception in queue processor: " + str(e))
            finally:
                queue.task_done()

    def add_files_from_dir(self, tmp_dir):
        for root, dirnames, filenames in os.walk(tmp_dir):
            for fname in filenames:
                # Guess the mime type from the file name
                mime_type, encoding = mimetypes.guess_type(fname)
                file_path = os.path.join(root, fname)
                if mime_type is None:
                    # Guess the mime type from the file contents
                    mime_type = self.mime_magic.from_file(file_path)
                if mime_type is None or mime_type == '':
                    mime_type = 'application/octet-stream'

                # Create item
                item = MeasurerItem()
                item['mimetype'] = mime_type
                item['filename'] = fname
                item['from_conversion'] = True

                f = open(file_path, 'r')
                item.set_content(f.read())
                f.close()

                # remove the file
                os.remove(file_path);

                self.process_item(item)

        # Remove the directory and all its contents
        shutil.rmtree(tmp_dir)

    def spider_opened(self, spider):
        for k, v in self.queues.items():
            t = Thread(target=self.process_queue, args=[k])
            t.daemon = True
            self.threads[k] = t
            t.start()

    def spider_closed(self, spider):
        # Block until all queues are done
        for q in self.queues.values():
            q.join()

        total = 0
        for v in self.counts.values():
            total += v['items']
        spider.log(json.dumps([
            self.counts,
            total,
            self.item_count
        ], indent=2), level=log.INFO)

    def spider_idle(self, spider):
        # Check for non-empty queues and raise not-done exception if
        # one is found
        for q in self.queues.values():
            if not q.empty():
                raise DontCloseSpider("All queues not empty")
        # Block until all queues are done
        for q in self.queues.values():
            q.join()

    def count_item(self, item):
        self.lock.acquire()
        mimetype = item['mimetype']
        if mimetype not in self.counts:
            self.counts[mimetype] = {
                'items': 0,
                'bytes': 0,
                'from_conversion': 0,
                'conversion_time': 0.0
            }
        counts = self.counts[mimetype]
        
        counts['items'] += 1
        counts['bytes'] += item['length']
        if item['from_conversion']:
            counts['from_conversion'] += 1
        counts['conversion_time'] += item['conversion_time']

        # Release some memory by removing the content of the item
        item.set_content("")

        self.lock.release()

    def process_item(self, item):
        self.item_count += 1

        # Drop items we have already seen
        if item['md5'] not in self.md5s:
            self.md5s.add(item['md5'])

            processor_type = Processor.mimetype_to_processor_type(
                item['mimetype']
            )
            if processor_type and processor_type in self.queues:
                self.queues[processor_type].put(item)
            else:
                self.count_item(item)

    def item_scraped(self, item, spider):
        self.process_item(item)
