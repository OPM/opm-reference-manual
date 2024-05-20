import io
import re
import xml.sax
import xml.sax.handler
import xml.sax.xmlreader
import xml.sax.saxutils

from fodt.xml_helpers import XMLHelper

class PassThroughFilterHandler(xml.sax.handler.ContentHandler):
    def __init__(self, add_header=True) -> None:
        self.add_header = add_header
        self.content = io.StringIO()
        self.start_tag_open = False  # For empty tags, do not close with />

    def characters(self, content: str):
        if self.start_tag_open:
            # NOTE: characters() is only called if there is content between the start
            # tag and the end tag. If there is no content, characters() is not called.
            self.content.write(">")
            self.start_tag_open = False
        self.content.write(XMLHelper.escape(content))

    def endElement(self, name: str):
        if self.start_tag_open:
            self.content.write("/>")
            self.start_tag_open = False
        else:
            self.content.write(XMLHelper.endtag(name))

    def get_content(self) -> str:
        return self.content.getvalue()

    def startDocument(self):
        if self.add_header:
            self.content.write(XMLHelper.header)

    def startElement(self, name:str, attrs: xml.sax.xmlreader.AttributesImpl):
        if self.start_tag_open:
            self.content.write(">")
        self.start_tag_open = True
        self.content.write(XMLHelper.starttag(name, attrs, close_tag=False))


class GetUsedStylesHandler(xml.sax.handler.ContentHandler):
    def __init__(self) -> None:
        # The values of the dict below list the attribute-names where the style is used.
        self.style_attrs: dict[str, set] = dict()
        # The values of the dict below list the tag-names where the style is used.
        self.style_names: dict[str, set] = dict()

    def endElement(self, name: str):
        pass

    def get_style_attrs(self) -> dict[str, set]:
        return self.style_attrs

    def get_style_names(self) -> dict[str, set]:
        return self.style_names

    def startElement(self, name:str, attrs: xml.sax.xmlreader.AttributesImpl):
        for (key, value) in attrs.items():
            if value == "":
                continue
            if (key.endswith("page-name")       or key.endswith("display-name") or
                key.endswith("font-style-name") or key.endswith("font-name")):
                continue
            if key.endswith("style-name") or re.fullmatch(r"style:.*-name", key):
                if value in self.style_attrs:
                    self.style_attrs[value].add(key)
                else:
                    self.style_attrs[value] = {key}
                if key in self.style_names:
                    self.style_names[value].add(name)
                else:
                    self.style_names[value] = {name}

