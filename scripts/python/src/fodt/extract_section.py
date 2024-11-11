import io
import logging
import xml.sax
import xml.sax.handler
import xml.sax.xmlreader
import xml.sax.saxutils
from pathlib import Path

import click

from fodt.constants import (
    AutomaticStyles, ClickOptions, Directories, FileNames, FileExtensions, MetaSections
)
from fodt.automatic_styles_filter import AutomaticStylesFilter4
from fodt.exceptions import ParsingException
from fodt import helpers
from fodt.styles_filter import StylesFilter
from fodt.xml_helpers import XMLHelper

class CreateSectionFile():
    def __init__(
        self,
        maindir: str,
        chapter_number: int,
        section_number: int,
        section_txt: str,
        styles: set[str]
    ) -> None:
        self.maindir = Path(maindir)
        self.section_number = section_number
        self.chapter_number = chapter_number
        self.section_txt = section_txt
        self.styles = styles

    def create(self) -> None:
        self.section_dir = (self.maindir / Directories.chapters
                            / Directories.sections / f"{self.chapter_number}")
        self.section_dir.mkdir(parents=True, exist_ok=True)
        self.section_file = self.section_dir / f"{self.section_number}.{FileExtensions.fodt}"
        with open(self.section_file, "w", encoding='utf-8') as f:
            self.outputfile = f
            self.write_xml_header()
            self.write_office_document_start_tag()
            self.write_meta()
            self.write_office_body_start_tag()
            self.write_section()
            self.write_xml_footer()
        logging.info(f"Wrote section file to {self.section_file}.")

    def write_section(self) -> None:
        self.outputfile.write("\n")
        self.outputfile.write(self.section_txt)

    def write_office_body_start_tag(self) -> None:
        section_name = f"Section{self.section_number}"
        self.outputfile.write("\n <office:body>")
        self.outputfile.write(f"""
  <office:text text:use-soft-page-breaks="true">
   <office:forms form:automatic-focus="false" form:apply-design-mode="false"/>
   <text:sequence-decls>
    <text:sequence-decl text:display-outline-level="0" text:name="Illustration"/>
    <text:sequence-decl text:display-outline-level="1" text:separation-character="." text:name="Table"/>
    <text:sequence-decl text:display-outline-level="1" text:separation-character="." text:name="Text"/>
    <text:sequence-decl text:display-outline-level="0" text:name="Drawing"/>
    <text:sequence-decl text:display-outline-level="1" text:separation-character="." text:name="Figure"/>
    <text:sequence-decl text:display-outline-level="0" text:name="Listing"/>
   </text:sequence-decls>
   <text:user-field-decls>
    <text:user-field-decl office:value-type="string" office:string-value="" text:name="SEQ"/>
    <text:user-field-decl office:value-type="float" office:value="1" text:name="MD"/>
    <text:user-field-decl office:value-type="string" office:string-value="" text:name="SEQ CHAPTER \h \r 1"/>
   </text:user-field-decls>
   <text:section text:style-name="Sect1" text:name="{section_name}">
""")

    def write_office_document_start_tag(self) -> None:
        self.metadir = self.maindir / Directories.meta
        tag = XMLHelper.get_office_document_start_tag(self.metadir)
        self.outputfile.write(tag)

    def write_meta(self) -> None:
        section_names = MetaSections.names
        for section_name in section_names:
            section_name = section_name.removeprefix("office:")
            self.write_meta_section(section_name)

    def write_meta_section(self, section_name: str) -> None:
        section_file = self.metadir / Directories.meta_sections / f"{section_name}.{FileExtensions.xml}"
        with open(section_file, "r", encoding='utf-8') as f:
            content = f.read()
            if section_name == "automatic-styles":
                filter = AutomaticStylesFilter4(self.metadir, content, self.styles)
                content = filter.get_filtered_content()
            elif section_name == "styles":
                filter = StylesFilter(content, f"{self.chapter_number}.{self.section_number}")
                content = filter.get_filtered_content()
        self.outputfile.write(content)

    def write_xml_header(self) -> None:
        self.outputfile.write(XMLHelper.header)

    def write_xml_footer(self) -> None:
        self.outputfile.write("""
   </text:section>
  </office:text>
 </office:body>
</office:document>\n""")


class ExtractAndRemoveHandler(xml.sax.handler.ContentHandler):
    def __init__(self, chapter_number: str, section_number: str) -> None:
        self.section_number = int(section_number)
        self.chapter_number = int(chapter_number)
        self.current_section_number = 0
        self.in_section = False
        self.section = None
        self.done_extracting = False
        self.doc = io.StringIO()
        self.styles = set()
        self.style_attrs = AutomaticStyles.attr_names

    def characters(self, content: str):
        if self.in_section:
            self.section.write(XMLHelper.escape(content))
        else:
            self.doc.write(XMLHelper.escape(content))

    def collect_styles(self, attrs: xml.sax.xmlreader.AttributesImpl) -> None:
        for (key, value) in attrs.items():
            if key in self.style_attrs:
                self.styles.add(value)

    def endDocument(self) -> None:
        if not self.done_extracting:
            raise ParsingException(f"Failed to extract section from chapter.")
        return super().endDocument()

    def endElement(self, name: str):
        if self.in_section:
            self.section.write(XMLHelper.endtag(name))
        else:
            self.doc.write(XMLHelper.endtag(name))

    def get_section(self) -> str:
        return self.section.getvalue()

    def get_doc(self) -> str:
        return self.doc.getvalue()

    def get_styles(self) -> set[str]:
        return self.styles

    def insert_section_link_into_doc(self) -> None:
        self.doc.write(f"""<text:section text:style-name="Sect1" """
                       f"""text:name="Section{self.chapter_number}.{self.section_number}" """
                       f"""text-protected="true">\n"""
                       f""" <text:section-source text:link-type="simple" """
                       f"""xlink:href="sections/{self.chapter_number}/{self.section_number}.fodt" """
                       f"""text:filter-name="OpenDocument Text Flat XML" """
                       f"""text:section-name="Section{self.section_number}">\n"""
                       f""" </text:section-source>\n"""
                       f"""</text:section>\n"""
        )

    def startDocument(self):
        self.doc.write(XMLHelper.header)

    def startElement(self, name:str, attrs: xml.sax.xmlreader.AttributesImpl):
        # TODO: Looking for <text:h text:outline-level="2"> does not work for the last
        #   section, since it does not have a trailing text:h tag.
        if (not self.done_extracting) and name == "text:h":
            if "text:outline-level" in attrs.getNames():
                level = attrs.getValue("text:outline-level")
                if level == "2":
                    self.current_section_number += 1
                    if self.in_section:
                        self.in_section = False
                        self.done_extracting = True
                        self.doc.write(XMLHelper.starttag(name, attrs))
                        return
                    elif self.current_section_number == self.section_number:
                        self.in_section = True
                        self.section = io.StringIO()
                        self.insert_section_link_into_doc()
        if self.in_section:
            self.section.write(XMLHelper.starttag(name, attrs))
            self.collect_styles(attrs)
        else:
            self.doc.write(XMLHelper.starttag(name, attrs))



class ExtractAndRemoveSectionFromChapter:
    def __init__(self, maindir: str, chapter: str, section: str) -> None:
        self.maindir = Path(maindir)
        self.chapter = chapter
        self.section = section

    def extract(self) -> tuple[str, str, set[str]]:
        parser = xml.sax.make_parser()
        handler = ExtractAndRemoveHandler(self.chapter, self.section)
        parser.setContentHandler(handler)
        fn = helpers.chapter_fodt_file_path(self.maindir, self.chapter)
        parser.parse(fn)
        return (handler.get_section(), handler.get_doc(), handler.get_styles())


class ExtractSection:
    def __init__(self, maindir: str, chapter: str, section: str) -> None:
        self.maindir = Path(maindir)
        self.chapter = chapter
        self.section = section
        self.main_file = self.maindir / FileNames.main_document
        assert self.main_file.is_file()

    def create_section_file(self, section_txt: str, styles: set[str]) -> None:
        creator = CreateSectionFile(
            self.maindir, self.chapter, self.section, section_txt, styles
        )
        creator.create()

    def extract(self) -> str:
        extractor = ExtractAndRemoveSectionFromChapter(
            self.maindir, self.chapter, self.section
        )
        section_txt, chapter_doc, styles = extractor.extract()
        self.write_updated_chapter(chapter_doc)
        self.create_section_file(section_txt, styles)

    def write_updated_chapter(self, doc: str) -> None:
        fn = helpers.chapter_fodt_file_path(self.maindir, self.chapter)
        with open(fn, "w", encoding='utf8') as f:
            f.write(doc)
        logging.info(f"Wrote updated chapter file to {fn}.")

# USAGE: fodt-extract-section --maindir=<main_dir> --section<section_number>
#
# Example:
#
# fodt-extract-section --maindir=../../parts --section=11.2
#
@click.command()
@ClickOptions.maindir(required=False)
@click.option(
    '--section',
    type=str,
    required=True,
    help='Number of the section to extract. Example: 11.2'
)
def extract_section(maindir: str, section: str) -> None:
    """Extract the appendix from a FODT file."""
    logging.basicConfig(level=logging.INFO)
    (chapter, section) = helpers.split_section(section)
    logging.info(f"Extracting section {section} from chapter {chapter}.")
    extractor = ExtractSection(maindir, chapter, section)
    extractor.extract()

if '__name__' == '__main__':
    extract_section()
