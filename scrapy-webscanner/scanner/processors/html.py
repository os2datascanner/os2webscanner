from processor import Processor
from w3lib.html import remove_tags, replace_entities

class HTMLProcessor(Processor):
    def process(self, data):
        print "Process HTML"
        # Convert HTML entities to their unicode representation
        entity_replaced_html = replace_entities(data)
        # Strip tags from the HTML (except comments)
        no_tags_html = remove_tags(entity_replaced_html, keep=("!--"))
        return no_tags_html