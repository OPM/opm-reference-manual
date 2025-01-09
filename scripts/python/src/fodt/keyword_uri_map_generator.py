import logging
import re
import xml.sax
import xml.sax.handler
import xml.sax.xmlreader
import xml.sax.saxutils

from pathlib import Path

import click

from fodt.constants import ClickOptions, Directories, FileNames, FileExtensions
from fodt.exceptions import HandlerDoneException, ParsingException
from fodt import helpers

class ExtractURI_Handler(xml.sax.handler.ContentHandler):
    def __init__(self, keyword_name: str) -> None:
        self.keyword_name = keyword_name
        self.in_section = False
        self.in_bookmark = False
        self.in_bookmark2 = False
        self.uri = ""

    def characters(self, content: str):
        if self.in_bookmark2:
            # Check if the content matches the keyword name
            match =  re.search(self.keyword_name, content)
            if match is None:
                #self.uri = None
                #raise ParsingException(
                #    f"Keyword name {self.keyword_name} not found in bookmark content: {content}"
                #)
                # NOTE: Since the content may contain span tags, for example the CO2STORE keyword goes like this
                #  <text:span text:style-name="T6">C</text:span>O2STORE
                # we cannot expect to find the keyword name in the content. Instead we print a warning and
                # the user can manually check the warning message to see if the keyword name was found.
                logging.warning(f"Keyword name {self.keyword_name} not found in bookmark content: {content}")
            raise HandlerDoneException("Done parsing.")

    def endDocument(self):
        raise ParsingException("Keyword name not found in document")

    def endElement(self, name: str):
        if name == "text:h":
            if self.in_section:
                self.in_section = False
                # The keyword URI must be found within the text:h, since we are done parsing
                # the tag, we raise an exception here to catch an unexpected situation.
                raise ParsingException("Keyword name not found in document")
        elif self.in_section and name == "text:bookmark-start":
            if self.in_bookmark:
                self.in_bookmark2 = True  # In the middle of a bookmark between start and end
        elif self.in_section and name == "text:bookmark-end":
            if self.in_bookmark:
                self.in_bookmark = False
                raise ParsingException("Keyword name not found in document")

    def get_extracted_uri(self) -> str:
        return self.uri

    # This callback is used for debugging, it can be used to print
    #  line numbers in the XML file
    def setDocumentLocator(self, locator):
        self.locator = locator

    def startDocument(self):
        pass

    def startElement(self, name:str, attrs: xml.sax.xmlreader.AttributesImpl):
        if name == "text:h":
            if "text:outline-level" in attrs.getNames():
                level = attrs.getValue("text:outline-level")
                if level == "3":
                    self.in_section = True
        elif self.in_section and name == "text:bookmark-start":
            self.in_bookmark = True
            # Assume there always will be a text:bookmark-start tag immediately
            # following the text:h tag. This element will contain the keyword name.
            self.uri = attrs.getValue("text:name")


class ExtractURI:
    def __init__(self, file: Path, keyword_name: str) -> None:
        self.filename = file
        self.keyword_name = keyword_name

    def extract(self) -> str:
        parser = xml.sax.make_parser()
        handler = ExtractURI_Handler(self.keyword_name)
        parser.setContentHandler(handler)
        try:
            parser.parse(str(self.filename))
        except HandlerDoneException as e:
            pass
        uri = handler.get_extracted_uri()
        return uri

class ProcessChapter:
    def __init__(self, maindir: Path, chapter: str, section: str, kw_file: Path, kw_uri_map: dict[str, str]) -> None:
        self.chapter = chapter
        self.section = section
        self.kw_file = kw_file
        self.kw_uri_map = kw_uri_map
        self.maindir = maindir

    def process(self) -> None:
        with open(self.kw_file, "r", encoding='utf8') as f:
            for line in f:
                keyword = line.strip()
                uri = self.keyword_uri(keyword)
                self.kw_uri_map[keyword] = uri

    def keyword_uri(self, keyword: str) -> str:
        kw_file = (self.maindir / Directories.chapters / Directories.subsections / 
                   f"{self.chapter}.{self.section}" / f"{keyword}.{FileExtensions.fodt}")
        uri = ExtractURI(kw_file, keyword).extract()
        return uri

def get_kw_uri_map(maindir: Path, keyword_dir: Path) -> dict[str, str]:
    kw_uri_map = {}
    # Assume all directories in keyword_dir are keyword directories on the form xx.yy
    # where xx is the chapter number and yy is the section number.
    for item1 in keyword_dir.iterdir():
        if not item1.is_dir():
            continue
        chapter_str = item1.name
        (chapter, section) = chapter_str.split(".")
        kw_file = item1 / FileNames.keywords
        logging.info(f"Processing chapter {chapter_str}")
        ProcessChapter(maindir, chapter, section, kw_file, kw_uri_map).process()
    add_keyword_aliases(kw_uri_map)
    return kw_uri_map

def add_keyword_aliases(kw_uri_map: dict[str, str]) -> None:
    # Add aliases for keywords
    for keyword in ["ENKRVD", "ENPTVD", "IKRG", "IKRGR", "IKRO", "IKRORG", "IKRORW",
                    "IKRW", "IKRWR", "IMBNUM", "IMKRVD", "IMPTVD", "ISGCR", "ISGL",
                    "ISGU", "ISOGCR", "ISOWCR", "ISWCR", "ISWL", "ISWU",
                    "KRG", "KRGR", "KRNUM", "KRO", "KRORG", "KRORW", "KRW", "KRWR",
                    "SGCR", "SGL", "SGU", "SOGCR", "SOWCR", "SWCR", "SWL", "SWU"]:
        add_xyz_aliases(kw_uri_map, keyword)
    for keyword in ["KRNUM"]:
        add_rt_aliases(kw_uri_map, keyword)

def add_xyz_aliases(kw_uri_map: dict[str, str], keyword: str) -> None:
    for extension in ["X", "Y", "Z", "X-", "Y-", "Z-"]:
        add_alias(kw_uri_map, keyword, f"{keyword}{extension}")

def add_rt_aliases(kw_uri_map: dict[str, str], keyword: str) -> None:
    for extension in ["R", "T", "R-", "T-"]:
        add_alias(kw_uri_map, keyword, f"{keyword}{extension}")

def add_alias(kw_uri_map: dict[str, str], keyword: str, alias: str) -> None:
    uri = kw_uri_map[keyword]
    kw_uri_map[alias] = uri

# fodt-gen-kw-uri-map
# -------------------
#
# SHELL USAGE:
#
# fodt-gen-kw-uri-map --maindir=<main_dir> --keyword_dir=<keyword_dir>
#
# DESCRIPTION:
#
#   Generates a map: KW_NAME -> URI for all keywords. The map is saved to the file
#   "meta/kw_uri_map.txt" in the main directory.
#
# EXAMPLE:
#
#  fodt-gen-kw-uri-map
#
#  Will use the default values: --maindir=../../parts --keyword_dir=../../keyword-names
#
@click.command()
@ClickOptions.maindir()
@ClickOptions.keyword_dir
def gen_kw_uri_map_cli(maindir: str|None, keyword_dir: str|None) -> None:
    logging.basicConfig(level=logging.INFO)
    keyword_dir = helpers.get_keyword_dir(keyword_dir)
    maindir = helpers.get_maindir(maindir)
    kw_uri_map = get_kw_uri_map(maindir, keyword_dir)
    with open(maindir / Directories.meta / FileNames.kw_uri_map, "w", encoding='utf8') as f:
        for kw in sorted(kw_uri_map.keys()):
            f.write(f"{kw} {kw_uri_map[kw]}\n")
    logging.info(f"Generated keyword URI map to {maindir / Directories.meta / FileNames.kw_uri_map}")

if __name__ == "__main__":
    gen_kw_uri_map_cli()
