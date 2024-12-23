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
from fodt import helpers, keyword_uri_map_generator
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
        self.in_math = False   # We should not insert links inside math tags
        self.in_binary_data = False  # We should skip binary data
        self.in_draw_frame = False  # We should not insert links in Figure captions
        self.in_draw_recursion = 0  # We can have nested draw:frame tags
        self.content = io.StringIO()
        # Create a regex pattern with alternation on the keyword names
        self.regex = self.compile_regex()
        self.num_links_inserted = 0
        self.office_body_found = False
        # Set of paragraph styles using fixed width fonts, intialized with the
        #  "_40_Example" style that is used indirectly by the other example styles
        self.example_styles = {'_40_Example'}
        # Special span style that have been manually inserted to indicate that
        # a word should not be treated as a keyword and therefore should not be linked
        self.not_keyword = False
        # A temporary character buffer to store content between start and end tags
        self.char_buf = ""

    def compile_regex(self) -> re.Pattern:
        # Also include the keyword name itself in the regex pattern, see discussion
        # https://github.com/OPM/opm-reference-manual/pull/410
        pattern = re.compile(
            r'(?<![.‘"“])'  # Negative lookbehind for a dot or a single/double quote
            r'(?<!&quot;)'    # Negative lookbehind: no HTML double-quote entity before keyword
            r'\b(' +
            '|'.join(
                # Need to sort the keys by length in descending order to avoid
                #  matching a substring of a longer keyword. See
                # https://github.com/OPM/opm-reference-manual/pull/411#discussion_r1835446631
                sorted((re.escape(k) for k in self.kw_uri_map.keys()), key=len, reverse=True)
                ) +
            # NOTE: We cannot use \b here because if the keyword ends with "-" the word boundary
            #  \b will not match between a space and a hyphen. Instead we use a negative lookahead
            # Negative lookaheads: no word char, "-" or &apos; after the keyword
            r')(?![\w-])(?!&apos;)'
        )
        return pattern

    def characters(self, content: str):
        # NOTE: characters() is only called if there is content between the start
        # tag and the end tag. If there is no content, characters() is not called.
        if self.start_tag_open:
            self.content.write(">")
            self.start_tag_open = False
        # NOTE: Do not write characters immediately to the content buffer, instead
        #  add the content to the content stack. This is a quick fix to be able to
        #  detect if a keyword is followed by an apostrophe, for example "LGR's" or
        #  if the keyword is within quotes, for example "&quot;LGR&quot;". In those cases
        #  content would be split between multiple characters() calls.
        # TODO: This does not handle cases with interleaved tags, for example <text:a>
        #  and <text:span> tags.

        self.char_buf += content

    def collect_style(self, attrs: xml.sax.xmlreader.AttributesImpl) -> None:
        # Collect the paragraph styles that use fixed width fonts
        if "style:name" in attrs.getNames():
            style_name = attrs.getValue("style:name")
            self.example_styles.add(style_name)

    def endDocument(self):
        assert(self.char_buf == "")  # All content should have been written to the content buffer

    def endElement(self, name: str):
        self.maybe_write_characters()
        if self.office_body_found:
            if name == "text:p":
                self.p_recursion -= 1
                if self.p_recursion == 0:
                    self.in_p = False
                self.is_example_p.pop()
            elif name == "text:a":
                self.in_a = False
            elif name == "text:span":
                self.not_keyword = False  # This cannot be nested
            elif name == "math":
                self.in_math = False
            elif name == "office:binary-data":
                self.in_binary_data = False
            elif name == "draw:frame":
                self.in_draw_recursion -= 1
                if self.in_draw_recursion == 0:
                    self.in_draw_frame = False
        if self.start_tag_open:
            self.content.write("/>")
            self.start_tag_open = False
        else:
            self.content.write(XMLHelper.endtag(name))

    def get_content(self) -> str:
        return self.content.getvalue()

    def get_num_links_inserted(self) -> int:
        return self.num_links_inserted

    def is_table_caption(self, content: str) -> bool:
        # Check if the content is a specific table caption, in that case we should not insert links
        return re.search(rf'{re.escape(self.keyword_name)} Keyword Description', content)

    def maybe_write_characters(self) -> None:
        if len(self.char_buf) > 0:
            # NOTE: We need to escape the content before we apply the regex pattern
            #  because it may insert tags (<text:a ...>) that should not be escaped.
            characters = XMLHelper.escape(self.char_buf)
            if self.office_body_found:
                if (self.in_p
                    and (not self.in_a)
                    and (not self.not_keyword)
                    and (not self.in_math)
                    and (not self.in_binary_data)
                    and (not self.in_draw_frame)
                ):
                    if not self.is_example_p[-1]:
                        if not self.is_table_caption(characters):
                            characters = self.regex.sub(self.replace_match_function, characters)
            self.content.write(characters)
            self.char_buf = ""

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
        self.maybe_write_characters()
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
            elif name == "text:span":
                if "text:style-name" in attrs.getNames():
                    style_name = attrs.getValue("text:style-name")
                    if style_name == "NOT_KEYWORD":
                        self.not_keyword = True
            elif name == "math":
                self.in_math = True
            elif name == "office:binary-data":
                # We need to skip the binary data, otherwise the content will be corrupted
                self.in_binary_data = True
            elif name == "draw:frame":
                # We do not want the script to insert links in a Figure caption. These captions
                # are usually inside a draw:frame tag.
                self.in_draw_frame = True
                self.in_draw_recursion += 1
        self.start_tag_open = True
        self.content.write(XMLHelper.starttag(name, attrs, close_tag=False))

    def update_example_stack(self, attrs: xml.sax.xmlreader.AttributesImpl) -> None:
        if "text:style-name" in attrs.getNames():
            style_name = attrs.getValue("text:style-name")
            self.is_example_p.append(style_name in self.example_styles)
        else:
            self.is_example_p.append(False)

class InsertLinks():
    def __init__(
        self,
        maindir: Path,
        subsection: str|None,
        filename: str|None,
        kw_dir: Path, kw_uri_map: dict[str, str]
    ) -> None:
        self.maindir = maindir
        self.kw_dir = kw_dir
        self.kw_uri_map = kw_uri_map
        self.subsection = subsection
        self.filename = filename

    def insert_links(self) -> None:
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
# fodt-link-keyword \
#    --maindir=<main_dir> \
#    --keyword_dir=<keyword_dir> \
#    --subsection=<subsection> \
#    --filename=<filename> \
#    --use-map-file
#
# DESCRIPTION:
#
#   Links all keyword names found inside <p> tags in the subsection documents to the
#   corresponding keyword subsection subdocument.
# 
#   If the option --use-map-file is given, the script will use the mapping file
#   "meta/kw_uri_map.txt" (generated by running the script "fodt-gen-kw-uri-map"), else
#   it will generate the mapping on the fly. The mapping is a map from keyword name to
#   the URI of the keyword subsection subdocument. This map is needed to generate the
#   links.
#
#   If --subsection is not given, the script will process all subsections. If --subsection
#   is given, the script will only process the specified subsection, or if --filename is
#   given, the script will only process the specified file within the specified subsection.
#
# EXAMPLES:
#
#    fodt-link-keywords --subsection=5.3
#
#  Will use the default values: --maindir=../../parts, --keyword_dir=../../keyword-names,
#  and will process only the keywords in subsection 5.3, and will generate the mapping on the fly.
#
#    fodt-link-keywords
#
#  Same as above, but will process all subsections. And,
#
#    fodt-link-keywords --subsection=10.3 --filename=AQANCONL.fodt
#
#  Will process only the file "AQANCONL.fodt" in subsection 10.3.
#
@click.command()
@ClickOptions.maindir()
@ClickOptions.keyword_dir
@click.option('--subsection', help='The subsection to process')
@click.option('--use-map-file', is_flag=True, help='Use the mapping file "meta/kw_uri_map.txt"')
@click.option('--filename', help='The filename to process')
def link_keywords(
    maindir: str|None,
    keyword_dir: str|None,
    subsection: str|None,
    filename: str|None,
    use_map_file: bool
) -> None:
    logging.basicConfig(level=logging.INFO)
    maindir = helpers.get_maindir(maindir)
    keyword_dir = helpers.get_keyword_dir(keyword_dir)
    if use_map_file:
        kw_uri_map = load_kw_uri_map(maindir)
    else:
        kw_uri_map = keyword_uri_map_generator.get_kw_uri_map(maindir, keyword_dir)
    kw_dir = maindir / Directories.chapters / Directories.subsections
    InsertLinks(maindir, subsection, filename, kw_dir, kw_uri_map).insert_links()

if __name__ == "__main__":
    link_keywords()
