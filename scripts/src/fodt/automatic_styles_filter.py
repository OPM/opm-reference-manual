import io
import logging

import xml.sax
import xml.sax.handler
import xml.sax.xmlreader
import xml.sax.saxutils

from pathlib import Path
from fodt.constants import AutomaticStyles, FileNames, FileExtensions
from fodt.xml_helpers import XMLHelper

class ElementHandler(xml.sax.handler.ContentHandler):
    def __init__(self, styles: set[str]) -> None:
        self.styles = styles
        self.style_attrs_names = AutomaticStyles.attr_names
        self.content = io.StringIO()
        self.nesting = 0

    def startElement(self, name:str, attrs: xml.sax.xmlreader.AttributesImpl):
        if self.nesting > 0:
            if name == self.current_element:
                self.nesting += 1
        else:
            self.include = False
            self.current_element = name
            found = False
            for (key, value) in attrs.items():
                if key in self.style_attrs_names:
                    found = True
                    if value in self.styles:
                        self.include = True
                        break
            if found:
                self.nesting = 1
            else:
                self.include = True
        if self.include:
            self.content.write(XMLHelper.starttag(name, attrs))

    def endElement(self, name: str):
        if self.nesting == 0:
            self.include = True
        elif name == self.current_element:
            if self.nesting >= 1:
                self.nesting -= 1
        if self.include:
            self.content.write(XMLHelper.endtag(name))

    def characters(self, content: str):
        if self.include:
            self.content.write(xml.sax.saxutils.escape(content))

class AutomaticStylesFilter:
    def __init__(self, stylesdir: Path, content: str, part: str) -> None:
        styles = self.read_styles(stylesdir, part)
        self.handler = ElementHandler(styles)
        xml.sax.parseString(content, self.handler)

    def get_filtered_content(self) -> str:
        return self.handler.content.getvalue()

    def read_styles(self, stylesdir: Path, part: str) -> list[str]:
        filename = stylesdir / f"{part}.{FileExtensions.txt}"
        styles = set()
        with open(filename, "r", encoding='utf8') as f:
            for line in f:
                styles.add(line.strip())
        return styles