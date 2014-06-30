from processor import Processor

class TextProcessor(Processor):
    def process(self, data, callback):
        callback(data)