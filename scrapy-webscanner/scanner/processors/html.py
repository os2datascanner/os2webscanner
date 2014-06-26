from processor import Processor
from w3lib.html import remove_tags, replace_entities

class HTMLProcessor(Processor):
    def process(self, response):
        print "Process HTML", response.url
        html = response.body.decode(response.encoding)
        # Convert HTML entities to their unicode representation
        entity_replaced_html = replace_entities(html)
        # Strip tags from the HTML (except comments)
        no_tags_html = remove_tags(entity_replaced_html, keep=("!--"))
        # Match against HTML before AND after removing tags
        # Because it could be possible that a tag interferes with a regex
        # matching (And it could also be that it does not)
        match_against = entity_replaced_html + " " + no_tags_html
        return match_against