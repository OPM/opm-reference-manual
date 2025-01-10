import io
import logging

import xml.sax
import xml.sax.handler
import xml.sax.xmlreader
import xml.sax.saxutils

from pathlib import Path
from fodt.constants import AutomaticStyles, FileNames, FileExtensions
from fodt import xml_helpers

class ElementHandler(xml.sax.handler.ContentHandler):
    def __init__(self, part: str) -> None:
        self.part = part
        self.style_attrs_names = AutomaticStyles.attr_names
        self.content = io.StringIO()

    def startElement(self, name:str, attrs: xml.sax.xmlreader.AttributesImpl):
        self.content.write(f"<{name}")
        for (key, value) in attrs.items():
            evalue = xml_helpers.escape(value)
            self.content.write(f" {key}=\"{evalue}\"")
        if name == "text:outline-level-style":
            level = int(attrs.getValue("text:level"))
            parts = self.part.split(".")
            num_parts = len(parts)
            if level <= num_parts:
                start_value = parts[level - 1]
                self.content.write(f" text:start-value=\"{start_value}\"")
        self.content.write(">")

    def endElement(self, name: str):
        self.content.write(xml_helpers.endtag(name))

    def characters(self, content: str):
        self.content.write(xml_helpers.escape(content))

class StylesFilter:
    def __init__(self, content: str, part: str) -> None:
        self.handler = ElementHandler(part)
        xml.sax.parseString(content, self.handler)

    def get_filtered_content(self) -> str:
        return self.handler.content.getvalue()

