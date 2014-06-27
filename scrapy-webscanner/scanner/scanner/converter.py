from scrapy import log

class Converter:
    def __init__(self):
        pass

    def convert(self, conversion_item):
        log.msg("Convert: " + conversion_item)
