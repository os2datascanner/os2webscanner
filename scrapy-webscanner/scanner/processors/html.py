from processor import Processor

class HTMLProcessor(Processor):
    def process(self, response):
        print "Process HTML", response.url
        # TODO: Strip HTML tags, convert HTML entities to text
        # TODO: Pass to Text processor
        return response.body.decode(response.encoding)