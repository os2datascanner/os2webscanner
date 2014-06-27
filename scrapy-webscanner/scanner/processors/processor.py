from twisted.internet import threads

class Processor:
    def __init__(self, scanner):
        self.scanner = scanner

class ProcessRequest:
    def __init__(self, data, mime_type=None, url=""):
        self.data = data
        self.mime_type = mime_type
        self.url = url
