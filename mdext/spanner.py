import xml.etree.ElementTree as ETree

from markdown.extensions import Extension
from markdown.inlinepatterns import InlineProcessor


class SpannerProcessor(InlineProcessor):
    def handleMatch(self, m, data):
        class_name = m.group('class')
        content = m.group('content')
        span = ETree.Element('span')
        span.set('class', class_name)
        span.text = content
        return span, m.start(0), m.end(0)

class SpannerExtension(Extension):
    def extendMarkdown(self, md):
        spawner_pattern = r'\~(?P<class>[a-zA-Z0-9\-_]+)\{(?P<content>[^\}]*)\}'
        md.inlinePatterns.register(SpannerProcessor(spawner_pattern, md), 'spanner', 175)

def makeExtension(*args, **kwargs):
    return SpannerExtension(*args, **kwargs)