import io
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
from fodt.xml_helpers import XMLHelper

class FileHandler(xml.sax.handler.ContentHandler):
    def __init__(self, keyword_name: str, kw_uri_map: dict[str, str]) -> None:
        self.keyword_name = keyword_name
        self.kw_uri_map = kw_uri_map
        self.in_section = False
        # For empty tags, we use a special trick to rewrite them with a shortened
        #  end /> tag instead of the full end tag </tag>
        self.start_tag_open = False
        self.in_p = False
        self.is_example_p = []  # Stack of boolean values: If current p tag is an example
        self.p_recursion = 0   # We can have nested p tags
        self.in_a = False
        self.content = io.StringIO()
        # Create a regex pattern with alternation on the keyword names
        self.regex = self.compile_regex()
        self.num_links_inserted = 0
        self.office_body_found = False
        self.example_styles = set()  # Set of paragraph styles using fixed width fonts

    def compile_regex(self) -> re.Pattern:
        # Do not include the keyword name itself in the regex pattern
        pattern = re.compile(
            r'\b(' + 
            '|'.join(
                re.escape(k) for k in self.kw_uri_map.keys() if k != self.keyword_name
                ) +
            r')\b'
        )
        return pattern

    def characters(self, content: str):
        # NOTE: characters() is only called if there is content between the start
        # tag and the end tag. If there is no content, characters() is not called.
        if self.start_tag_open:
            self.content.write(">")
            self.start_tag_open = False
        # NOTE: We need to escape the content before we apply the regex pattern
        #  because it may insert tags (<text:a ...>) that should not be escaped.
        content = XMLHelper.escape(content)
        if self.office_body_found:
            if self.in_p and not self.in_a:
                if not self.is_example_p[-1]:
                    content = self.regex.sub(self.replace_match_function, content)
        self.content.write(content)

    def collect_style(self, attrs: xml.sax.xmlreader.AttributesImpl) -> None:
        # Collect the paragraph styles that use fixed width fonts
        if "style:name" in attrs.getNames():
            style_name = attrs.getValue("style:name")
            self.example_styles.add(style_name)

    def endDocument(self):
        pass

    def endElement(self, name: str):
        if self.office_body_found:
            if name == "text:p":
                self.p_recursion -= 1
                if self.p_recursion == 0:
                    self.in_p = False
                self.is_example_p.pop()
            elif name == "text:a":
                self.in_a = False
        if self.start_tag_open:
            self.content.write("/>")
            self.start_tag_open = False
        else:
            self.content.write(XMLHelper.endtag(name))

    def get_content(self) -> str:
        return self.content.getvalue()

    def get_num_links_inserted(self) -> int:
        return self.num_links_inserted

    def replace_match_function(self, match: re.Match) -> str:
        keyword = match.group(0)
        uri = self.kw_uri_map[keyword]
        self.num_links_inserted += 1
        return f'<text:a xlink:href="#{uri}">{keyword}</text:a>'

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
        if not self.office_body_found:
            if name == "office:body":
                self.office_body_found = True
            else:
                if name == "style:style":
                    if "style:parent-style-name" in attrs.getNames():
                         if attrs.getValue("style:parent-style-name") == "_40_Example":
                            self.collect_style(attrs)
        else:
            if name == "text:p":
                self.in_p = True
                self.p_recursion += 1
                self.update_example_stack(attrs)
            elif name == "text:a":
                # We are inside an anchor, and we should not insert another text:a tag here
                self.in_a = True
        self.start_tag_open = True
        self.content.write(XMLHelper.starttag(name, attrs, close_tag=False))

    def update_example_stack(self, attrs: xml.sax.xmlreader.AttributesImpl) -> None:
        if "text:style-name" in attrs.getNames():
            style_name = attrs.getValue("text:style-name")
            self.is_example_p.append(style_name in self.example_styles)
        else:
            self.is_example_p.append(False)

class InsertLinks():
    def __init__(self, maindir: Path, kw_dir: Path, kw_uri_map: dict[str, str]) -> None:
        self.maindir = maindir
        self.kw_dir = kw_dir
        self.kw_uri_map = kw_uri_map

    def insert_links(self) -> None:
        for item in self.kw_dir.iterdir():
            if not item.is_dir():
                continue
            logging.info(f"Processing directory: {item}")
            breakpoint()
            for item2 in item.iterdir():
                if item2.suffix == f".{FileExtensions.fodt}":
                    keyword_name = item2.name.removesuffix(f".{FileExtensions.fodt}")
                    self.insert_links_in_file(item2, keyword_name)

    def insert_links_in_file(self, filename: Path, keyword_name: str) -> None:
        parser = xml.sax.make_parser()
        handler = FileHandler(keyword_name, self.kw_uri_map)
        parser.setContentHandler(handler)
        try:
            parser.parse(str(filename))
        except HandlerDoneException as e:
            pass
        num_links_inserted = handler.get_num_links_inserted()
        if num_links_inserted > 0:
            with open(filename, "w", encoding='utf8') as f:
                f.write(handler.content.getvalue())
            logging.info(f"{filename.name}: Inserted {num_links_inserted} links.")
        else:
            logging.info(f"{filename.name}: No links inserted.")


def load_kw_uri_map(maindir: Path) -> dict[str, str]:
    kw_uri_map_path = maindir / Directories.meta / FileNames.kw_uri_map
    if not kw_uri_map_path.exists():
        raise FileNotFoundError(f"File not found: {kw_uri_map_path}")
    kw_uri_map = {}
    with open(kw_uri_map_path, "r", encoding='utf-8') as f:
        for line in f:
            # Each line is on the format "<kw> <uri>" where <kw> is the keyword name and
            # does not contain any whitespace characters, and <uri> is the URI of the
            # keyword subsection subdocument. The <uri> may contain whitespace characters.
            # There is a single whitespace character between <kw> and <uri>.
            match = re.match(r"(\S+)\s+(.+)", line)
            if match:
                parts = match.groups()
                kw_uri_map[parts[0]] = parts[1]
            else:
                raise ParsingException(f"Could not parse line: {line}")
    return kw_uri_map

# fodt-link-keywords
# ------------------
#
# SHELL USAGE:
#
# fodt-link-keyword --maindir=<main_dir>
#
# DESCRIPTION:
#
#   Links all keyword names found inside <p> tags in the subsection documents to the
#   corresponding keyword subsection subdocument.
#   Uses the mapping file "meta/kw_uri_map.txt" generated by the script
#   "fodt-gen-kw-uri-map".
#
# EXAMPLE:
#
#  fodt-link-keywords
#
#  Will use the default value: --maindir=../../parts
#
@click.command()
@ClickOptions.maindir()
def link_keywords(maindir: str|None) -> None:
    logging.basicConfig(level=logging.INFO)
    maindir = helpers.get_maindir(maindir)
    kw_uri_map = load_kw_uri_map(maindir)
    kw_dir = maindir / Directories.chapters / Directories.subsections
    InsertLinks(maindir, kw_dir, kw_uri_map).insert_links()

if __name__ == "__main__":
    link_keywords()
