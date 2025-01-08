import io
import logging
import shutil
import subprocess
import xml.sax
import xml.sax.handler
import xml.sax.xmlreader
import xml.sax.saxutils

import click

from pathlib import Path
import fodt.string_functions
from fodt.constants import ClickOptions, Directories, FileNames
from fodt.remove_chapters import RemoveChapters
from fodt.xml_helpers import xml_helper

class ElementHandler(xml.sax.handler.ContentHandler):
    def __init__(self) -> None:
        self.content = io.StringIO()
        self.in_table = False
        self.current_tag_name = None
        self.nesting = 0

    def characters(self, content: str):
        self.content.write(xml_helpers.escape(content))

    def check_correct_table(self, attrs: xml.sax.xmlreader.AttributesImpl) -> bool:
        keys = attrs.keys()
        if "table:name" in keys and "table:style-name" in keys:
            if (attrs.get("table:name") == "Table109" and
                    attrs.get("table:style-name") == "Table109"):
                return True
        return False

    def endElement(self, name: str):
        if self.in_table:
            if name == "table:table":
                self.in_table = False
            elif name == "text:bookmark-ref":
                # remove this tag
                return
        self.content.write(xml_helpers.endtag(name))

    def startElement(self, name:str, attrs: xml.sax.xmlreader.AttributesImpl):
        # logging.info(f"startElement: {name}")
        if (not self.in_table) and name == "table:table":
            if self.check_correct_table(attrs):
                self.in_table = True
        if self.in_table and name == "text:bookmark-ref":
            # remove this tag
            return
        self.content.write(xml_helpers.starttag(name, attrs))


class FixupMasterStyles():
    def __init__(self, maindir: str) -> None:
        self.maindir = Path(maindir)

    def fixup(self) -> None:
        self.filename = (
            self.maindir /
            Directories.meta /
            Directories.meta_sections /
            FileNames.master_styles_fn
        )
        if not self.filename.exists():
            raise FileNotFoundError(f"Master styles file {self.filename} not found!.")
        bak_file = f"{self.filename}.bak"
        shutil.copy(self.filename, bak_file)
        parser = xml.sax.make_parser()
        self.handler = ElementHandler()
        parser.setContentHandler(self.handler)
        parser.parse(bak_file)
        with open(self.filename, "w") as f:
            f.write(self.handler.content.getvalue())

class Splitter():
    def __init__(self, maindir: str, filename: str) -> None:
        self.filename = filename
        self.maindir = Path(maindir)
        self.maindir.mkdir(parents=True, exist_ok=True)
        self.chapters = "1-12"

    def create_main_document(self) -> None:
        logging.info(f"Creating main document in {self.maindir}.")
        self.mainfile = self.maindir / FileNames.main_document
        if self.mainfile.exists():
            logging.info(f"Main document {self.mainfile} already exists, skipping.")
            return
        replace_callback = self.replace_section_callback
        chapters = fodt.string_functions.parse_parts(self.chapters)
        remover = RemoveChapters(self.mainfile, self.filename, chapters, replace_callback)

    def create_subdocuments(self) -> None:
        logging.info(f"Creating subdocuments in {self.maindir}.")
        subprocess.run([
            "fodt-create-subdocument",
            f"--maindir={self.maindir}",
            f"--chapters={self.chapters}",
        ])

    def extract_document_attrs(self) -> None:
        subprocess.run([
            "fodt-extract-document-attrs",
            f"--maindir={self.maindir}",
            f"--filename={self.filename}",
        ])

    def extract_metadata(self) -> None:
        logging.info(f"Extracting metadata..")
        subprocess.run([
            "fodt-extract-metadata",
            f"--maindir={self.maindir}",
            f"--filename={self.filename}",
        ])

    def extract_style_info(self) -> None:
        logging.info(f"Extracting style info..")
        subprocess.run([
            "fodt-extract-style-info",
            f"--maindir={self.maindir}",
        ])

    def extract_chapters(self) -> None:
        logging.info(f"Extracting chapters {self.chapters}..")
        subprocess.run([
            "fodt-extract-chapters",
            f"--maindir={self.maindir}",
            f"--chapters={self.chapters}",
            f"--filename={self.filename}",
        ])

    def fixup_master_styles(self) -> None:
        logging.info(f"Fixing up master styles..")
        FixupMasterStyles(self.maindir).fixup()

    def replace_section_callback(self, section_number: int) -> str:
        return (f"""<text:section text:style-name="Sect1" text:name="Section{section_number}" """
                   f"""text:protected="true">\n"""
                f"""     <text:section-source xlink:href="{Directories.chapters}/{section_number}.fodt" """
                   f"""text:filter-name="OpenDocument Text Flat XML" """
                   f"""text:section-name="Chapter{section_number}"/>\n"""
                #f"""     <text:p text:style-name="P17509">This is Section{section_number}</text:p>\n"""
                f"""    </text:section>\n""")

    def split(self) -> None:
        self.extract_metadata()
        self.fixup_master_styles()
        self.extract_style_info()
        self.extract_document_attrs()
        self.extract_chapters()
        self.create_subdocuments()
        self.create_main_document()


@click.command()
@ClickOptions.maindir()
@ClickOptions.filename
def split_main(maindir: str, filename: str) -> None:
    logging.basicConfig(level=logging.INFO)
    splitter = Splitter(maindir, filename)
    splitter.split()

if __name__ == "__main__":
    split_main()
