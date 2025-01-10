import io
import logging

import xml.sax
import xml.sax.handler
import xml.sax.xmlreader
import xml.sax.saxutils

from pathlib import Path
from fodt.constants import AutomaticStyles, FileExtensions, FileNames
from fodt import xml_helpers

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
            self.content.write(xml_helpers.starttag(name, attrs))

    def endElement(self, name: str):
        if self.nesting == 0:
            self.include = True
        elif name == self.current_element:
            if self.nesting >= 1:
                self.nesting -= 1
        if self.include:
            self.content.write(xml_helpers.endtag(name))

    def characters(self, content: str):
        if self.include:
            self.content.write(xml_helpers.escape(content))


class AutomaticStylesFilter:
    def __init__(self, metadir: Path, content: str, is_appendix: bool = False) -> None:
        # self.styles is assigned in the constructor of the subclass
        self.metadir = metadir
        self.is_appendix = is_appendix
        self.add_extra_styles(self.styles)
        self.add_extra_styles2(self.styles)
        self.handler = ElementHandler(self.styles)
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
        if self.is_appendix:
            styles_to_add = ['_40_Appendix_20_Heading_20_Numbering', 'P17379']
        else:
            styles_to_add = ['Sect1', 'P18776']
        for item in styles_to_add:
            styles.add(item)

    def get_filtered_content(self) -> str:
        return self.handler.content.getvalue()


class AutomaticStylesFilter2(AutomaticStylesFilter):
    def __init__(self, metadir: Path, stylesdir: Path, content: str, part: str) -> None:
        self.styles = self.read_styles(stylesdir, part)
        super().__init__(metadir, content)

    def read_styles(self, stylesdir: Path, part: str) -> set[str]:
        filename = stylesdir / f"{part}.{FileExtensions.txt}"
        styles = set()
        with open(filename, "r", encoding='utf8') as f:
            for line in f:
                styles.add(line.strip())
        return styles

class AutomaticStylesFilter3(AutomaticStylesFilter):
    def __init__(self, metadir: Path, content: str, part: str) -> None:
        # NOTE: These styles were taken from the COLUMNS keyword in section 4.3 since that keyword
        #       was also used for new the keyword template, see create_subsection_template() in
        #       src/fodt/create_subdocument.py
        self.styles = {
            'Internet_20_link', 'P18335', 'P18345', 'P6057', 'P6690', 'T1', 'Table990', 'Table990.1',
            'Table990.A', 'Table990.A1', 'Table990.E', 'Table990.F', 'Table990.H1', '_40_TextBody'
        }
        super().__init__(metadir, content)

class AutomaticStylesFilter4(AutomaticStylesFilter):
    def __init__(self, metadir: Path, content: str, styles: set[str]) -> None:
        self.styles = styles
        super().__init__(metadir, content, is_appendix=True)
