import io
import logging

import xml.sax
import xml.sax.handler
import xml.sax.xmlreader
import xml.sax.saxutils

from pathlib import Path
from fodt.constants import AutomaticStyles, FileExtensions, FileNames
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
                # include all elements that do not have an attribute name listed in
                # self.style_attrs_names. We are only filtering out elements that have
                # one of these attributes.
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
    def __init__(self, metadir: Path, stylesdir: Path, content: str, part: str) -> None:
        self.metadir = metadir
        styles = self.read_styles(stylesdir, part)
        self.add_extra_styles(styles)
        self.add_extra_styles2(styles)
        self.handler = ElementHandler(styles)
        xml.sax.parseString(content, self.handler)

    def add_extra_styles(self, styles: set[str]) -> None:
        """These styles are not used directly in the text, but are used by the other styles."""
        filename = self.metadir / FileNames.styles_info_fn
        with open(filename, "r", encoding='utf8') as f:
            for line in f:
                styles.add(line.strip())

    def add_extra_styles2(self, styles: set[str]) -> None:
        """These styles are used in the beginning of office:body section but before the
        text:section elements"""
        for item in ['Sect1', 'P18776']:
            styles.add(item)

    def get_filtered_content(self) -> str:
        return self.handler.content.getvalue()

    def read_styles(self, stylesdir: Path, part: str) -> set[str]:
        filename = stylesdir / f"{part}.{FileExtensions.txt}"
        styles = set()
        with open(filename, "r", encoding='utf8') as f:
            for line in f:
                styles.add(line.strip())
        return styles