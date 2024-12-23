import io
import logging
import xml.sax
import xml.sax.handler
import xml.sax.xmlreader
import xml.sax.saxutils

from pathlib import Path

import click

from fodt.constants import ClickOptions, Directories, FileExtensions
from fodt.exceptions import HandlerDoneException
from fodt import helpers
from fodt.xml_helpers import XMLHelper

class FileHandler(xml.sax.handler.ContentHandler):
    def __init__(self, keyword_name: str) -> None:
        self.keyword_name = keyword_name
        self.in_section = False
        # For empty tags, we use a special trick to rewrite them with a shortened
        #  end /> tag instead of the full end tag </tag>
        self.start_tag_open = False
        self.in_binary_data = False  # We should skip binary data
        self.in_kw_link = False  # We should skip keyword links inside the office:binary-data tag
        self.content = io.StringIO()
        self.num_links_removed = 0

    def characters(self, content: str):
        # NOTE: characters() is only called if there is content between the start
        # tag and the end tag. If there is no content, characters() is not called.
        if self.start_tag_open:
            self.content.write(">")
            self.start_tag_open = False
        if self.in_kw_link:
            # We are inside an errouneous link, and we should actually not skip this content
            #  since it was part of the original binary data
            pass
        self.content.write(XMLHelper.escape(content))

    def endDocument(self):
        pass

    def endElement(self, name: str):
        if name == "office:binary-data":
            self.in_binary_data = False
        if name == "text:a":
            if self.in_kw_link:
                self.in_kw_link = False
                self.num_links_removed += 1
                # Do not write the end tag
                return
        if self.start_tag_open:
            self.content.write("/>")
            self.start_tag_open = False
        else:
            self.content.write(XMLHelper.endtag(name))

    def get_content(self) -> str:
        return self.content.getvalue()

    def get_num_links_removed(self) -> int:
        return self.num_links_removed

    # This callback is used for debugging, it can be used to print
    #  line numbers in the XML file
    def setDocumentLocator(self, locator):
        self.locator = locator

    def startDocument(self):
        self.content.write(XMLHelper.header)

    def startElement(self, name:str, attrs: xml.sax.xmlreader.AttributesImpl):
        if self.start_tag_open:
            self.content.write(">")  # Close the start tag
            self.start_tag_open = False
        if name == "office:binary-data":
            self.in_binary_data = True
        elif name == "text:a":
            if self.in_binary_data:
                # We are inside a binary data tag, so this is the start of an errouneous link
                self.in_kw_link = True
                # Do not write the start tag
                return
        self.start_tag_open = True
        self.content.write(XMLHelper.starttag(name, attrs, close_tag=False))


class CheckLinks:
    def __init__(
        self,
        maindir: Path,
        subsection: str|None,
        filename: str|None,
        kw_dir: Path,
    ) -> None:
        self.maindir = maindir
        self.kw_dir = kw_dir
        self.subsection = subsection
        self.filename = filename

    def check_links(self) -> None:
        for item in self.kw_dir.iterdir():
            if not item.is_dir():
                continue
            if self.subsection:
                if item.name != self.subsection:
                    logging.info(f"Skipping directory: {item}")
                    continue
            logging.info(f"Processing directory: {item}")
            for item2 in item.iterdir():
                if item2.suffix == f".{FileExtensions.fodt}":
                    if self.filename:
                        if item2.name != self.filename:
                            logging.info(f"Skipping file: {item2.name}")
                            continue
                    keyword_name = item2.name.removesuffix(f".{FileExtensions.fodt}")
                    self.check_links_in_file(item2, keyword_name)

    def check_links_in_file(self, filename: Path, keyword_name: str) -> None:
        parser = xml.sax.make_parser()
        handler = FileHandler(keyword_name)
        parser.setContentHandler(handler)
        try:
            parser.parse(str(filename))
        except HandlerDoneException as e:
            pass
        num_links_removed = handler.get_num_links_removed()
        if num_links_removed > 0:
            with open(filename, "w", encoding='utf8') as f:
                f.write(handler.content.getvalue())
            logging.info(f"{filename.name}: Removed {num_links_removed} links.")
        else:
            logging.info(f"{filename.name}: No links removed.")



# fodt-check-links-office-binary-data
# -----------------------------------
#
# SHELL USAGE:
#
# fodt-check-links-office-binary-data \
#    --maindir=<main_dir> \
#    --keyword_dir=<keyword_dir> \
#    --subsection=<subsection> \
#    --filename=<filename> \
#
# DESCRIPTION:
#
#   This script checks for errouneous links in the office:binary-data elements in the
#   .fodt keyword files. These links might have been inserted by the fodt-link-keywords
#   script. The script is now fixed, but we need to check files processed and merged by
#   the old version of the script.
#   The links are on the form: <text:a xlink:href="#....">KEYWORD</text:a>
#
#   If --subsection is not given, the script will process all subsections. If --subsection
#   is given, the script will only process the specified subsection, or if --filename is
#   given, the script will only process the specified file within the specified subsection.
#
# EXAMPLES:
#
#    fodt-check-links-office-binary-data
#
#  Will use the default values: --maindir=../../parts, --keyword_dir=../../keyword-names,
#  and process all keyword files in all subsections (chapters 1-12).
#
#
@click.command()
@ClickOptions.maindir()
@ClickOptions.keyword_dir
@click.option('--subsection', help='The subsection to process')
@click.option('--filename', help='The filename to process')
def check_links_office_binary_data(
    maindir: str|None,
    keyword_dir: str|None,
    subsection: str|None,
    filename: str|None,
) -> None:
    logging.basicConfig(level=logging.INFO)
    maindir = helpers.get_maindir(maindir)
    keyword_dir = helpers.get_keyword_dir(keyword_dir)
    kw_dir = maindir / Directories.chapters / Directories.subsections
    CheckLinks(maindir, subsection, filename, kw_dir).check_links()

if __name__ == "__main__":
    check_links_office_binary_data()
