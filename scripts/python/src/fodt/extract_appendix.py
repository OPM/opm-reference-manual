# Specialized script to extract the Appendix A from file ../../parts/main.fodt
# We will save the appendix in directory ../../parts/appendices/A.fodt

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
from fodt.exceptions import HandlerDoneException
from fodt import xml_helpers

class CreateAppendixFile():
    def __init__(self, maindir: str, appendix: str, appendix_txt: str, styles: set[str]) -> None:
        self.maindir = Path(maindir)
        self.appendix = appendix
        self.appendix_txt = appendix_txt
        self.styles = styles

    def create(self) -> None:
        self.appendix_dir = self.maindir / Directories.appendices
        self.appendix_dir.mkdir(parents=True, exist_ok=True)
        self.appendix_file = self.appendix_dir / f"{self.appendix}.{FileExtensions.fodt}"
        with open(self.appendix_file, "w", encoding='utf-8') as f:
            self.outputfile = f
            self.write_xml_header()
            self.write_office_document_start_tag()
            self.write_meta()
            self.write_office_body_start_tag()
            self.write_appendix()
            self.write_xml_footer()

    def write_appendix(self) -> None:
        self.outputfile.write("\n")
        self.outputfile.write(self.appendix_txt)

    def write_office_body_start_tag(self) -> None:
        section_name = f"Appendix{self.appendix}"
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
        tag = xml_helpers.get_office_document_start_tag(self.metadir)
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
        self.outputfile.write(content)

    def write_xml_header(self) -> None:
        self.outputfile.write(xml_helpers.HEADER)

    def write_xml_footer(self) -> None:
        self.outputfile.write("""
   </text:section>
  </office:text>
 </office:body>
</office:document>\n""")

# Extract the appendix from the main fodt file.
# Appendix A will start with a <text:list> tag with attribute "xml:id" = "list3623483562"
#
# Appendix A ends with a <text:list> tag with attribute "xml:id" = "list105923873468832"
#
# The removed appendix is replaced with a link to the extracted appendix.
# The link is inserted in the main document as follows:
# <text:section text:style-name="Sect1" text:name="AppendixA" text:protected="true">
#     <text:section-source xlink:href="appendices/A.fodt"
#                          text:filter-name="OpenDocument Text Flat XML"
#                          text:section-name="AppendixA">
#    </text:section-source>
#  </text:section>
#
class ExtractAndRemoveHandler(xml.sax.handler.ContentHandler):
    def __init__(self, appendix_number: str, start_id: str, end_id: str) -> None:
        self.start_id = f"list{start_id}"
        if end_id == "<<section>>":
            self.end_type = "section"
        elif end_id == "<<end>>":
            self.end_type = "end"
        else:
            self.end_type = "list"
            self.end_id = f"list{end_id}"
        self.appendix_number = appendix_number
        self.in_appendix = False
        self.appendix = None
        self.doc = io.StringIO()
        self.styles = set()
        self.style_attrs = AutomaticStyles.attr_names

    def characters(self, content: str):
        if self.in_appendix:
            self.appendix.write(xml_helpers.escape(content))
        else:
            self.doc.write(xml_helpers.escape(content))

    def collect_styles(self, attrs: xml.sax.xmlreader.AttributesImpl) -> None:
        for (key, value) in attrs.items():
            if key in self.style_attrs:
                self.styles.add(value)

    def endElement(self, name: str):
        if self.in_appendix:
            self.appendix.write(xml_helpers.endtag(name))
        else:
            self.doc.write(xml_helpers.endtag(name))

    def get_appendix(self) -> str:
        return self.appendix.getvalue()

    def get_doc(self) -> str:
        return self.doc.getvalue()

    def get_styles(self) -> set[str]:
        return self.styles

    def insert_section_link_into_doc(self) -> None:
        self.doc.write(f"""<text:section text:style-name="Sect1" """
                       f"""text:name="Section{self.appendix_number}" text-protected="true">\n"""
                       f""" <text:section-source text:link-type="simple" """
                       f"""xlink:href="appendices/{self.appendix_number}.fodt" """
                       f"""text:filter-name="OpenDocument Text Flat XML" """
                       f"""text:section-name="Appendix{self.appendix_number}">\n"""
                       f""" </text:section-source>\n"""
                       f"""</text:section>\n"""
        )

    def startDocument(self):
        self.doc.write(xml_helpers.HEADER)

    def startElement(self, name:str, attrs: xml.sax.xmlreader.AttributesImpl):
        if (not self.in_appendix) and (name == "text:list"):
            if "xml:id" in attrs.getNames():
                xml_id = attrs.getValue("xml:id")
                if xml_id == self.start_id:
                    self.in_appendix = True
                    self.appendix = io.StringIO()
                    self.insert_section_link_into_doc()
        elif self.in_appendix:
            if (self.end_type == "list") and (name == "text:list"):
                if "xml:id" in attrs.getNames():
                    xml_id = attrs.getValue("xml:id")
                    if xml_id == self.end_id:
                        self.in_appendix = False
                        self.doc.write(xml_helpers.starttag(name, attrs))
                        return
            elif (self.end_type == "section") and (name == "text:section"):
                self.in_appendix = False
                self.doc.write(xml_helpers.starttag(name, attrs))
                return
            elif (self.end_type == "end") and (name == "text:p"):
                if "text:style-name" in attrs.getNames():
                    style_name = attrs.getValue("text:style-name")
                    if style_name == "ENDENDEND":
                        self.in_appendix = False
                        self.doc.write(xml_helpers.starttag(name, attrs))
                        return
        if self.in_appendix:
            self.appendix.write(xml_helpers.starttag(name, attrs))
            self.collect_styles(attrs)
        else:
            self.doc.write(xml_helpers.starttag(name, attrs))

class ExtractAndRemoveAppendixFromMain:
    def __init__(self, main_file: Path, appendix_number: str) -> None:
        self.main_file = main_file
        self.appendix_number = appendix_number

    def extract(self) -> tuple[str, str, set[str]]:
        parser = xml.sax.make_parser()
        if self.appendix_number == "A":
            ids = ("3623483562", "105923873468832")
        elif self.appendix_number == "B":
            ids = ("105923873468832", "105925008885815")
        elif self.appendix_number == "C":
            ids = ("105925008885815", "105924600149260")
        elif self.appendix_number == "D":
            ids = ("105924600149260", "<<section>>")
        elif self.appendix_number == "E":
            ids = ("105926382943660", "105927136285395")
        elif self.appendix_number == "F":
            ids = ("105927136285395", "<<end>>")
        else:
            raise ValueError(f"Invalid appendix number: {self.appendix_number}")
        handler = ExtractAndRemoveHandler(
            appendix_number=self.appendix_number, start_id=ids[0], end_id=ids[1]
        )
        parser.setContentHandler(handler)
        parser.parse(self.main_file)
        return (handler.get_appendix(), handler.get_doc(), handler.get_styles())

class ExtractAppendix:
    def __init__(self, maindir: str, appendix: str) -> None:
        self.maindir = Path(maindir)
        valid_appendices = {"A", "B", "C", "D", "E", "F"}
        if appendix not in valid_appendices:
            # Only certain appendices are supported for now..
            raise ValueError(
                f"Requires appendix ∈ {valid_appendices}. Appendix {appendix} is not supported."
            )
        self.appendix = appendix
        self.main_file = self.maindir / FileNames.main_document
        assert self.main_file.is_file()

    def create_appendix_file(self, appendix_txt: str, styles: set[str]) -> None:
        creator = CreateAppendixFile(
            self.maindir, self.appendix, appendix_txt, styles
        )
        creator.create()

    def extract(self) -> str:
        extractor = ExtractAndRemoveAppendixFromMain(self.main_file, self.appendix)
        appendix_txt, doc, styles = extractor.extract()
        self.write_updated_main(doc)
        self.create_appendix_file(appendix_txt, styles)

    def write_updated_main(self, doc: str) -> None:
        with open(self.main_file, "w", encoding='utf8') as f:
            f.write(doc)
        logging.info(f"Wrote updated main file to {self.main_file}.")


# USAGE: fodt-extract-appendix --maindir=<main_dir> --appendix=<appendix_number>

@click.command()
@ClickOptions.maindir(required=False)
@click.option('--appendix', type=str, required=True, help='Number of the appendix to extract.')
def extract_appendix(maindir: str, appendix: int) -> None:
    """Extract the appendix from a FODT file."""
    logging.basicConfig(level=logging.INFO)
    logging.info(f"Extracting appendix {appendix} from {maindir}.")
    extractor = ExtractAppendix(maindir, appendix)
    extractor.extract()

if '__name__' == '__main__':
    extract_appendix()
