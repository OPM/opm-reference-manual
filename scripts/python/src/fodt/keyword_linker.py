import enum
import io
import logging
import re
import xml.sax
import xml.sax.handler
import xml.sax.xmlreader
import xml.sax.saxutils

from dataclasses import dataclass
from pathlib import Path

import click

from fodt.constants import ClickOptions, Directories, FileExtensions
from fodt.exceptions import HandlerDoneException
from fodt import helpers, keyword_uri_map_generator, xml_helpers

class FileType(enum.Enum):
    CHAPTER = 1
    SUBSECTION = 2
    APPENDIX = 3

@dataclass
class MonoParagraphStyle:
    style_name: str = ""
    loext_graphic_properties: bool = False
    style_paragraph_properties: bool = False
    style_text_properties: bool = False
    libre_mono_font: bool = False
    #libre_mono_font_size: bool = False

    def in_style_style_element(self) -> bool:
        return self.style_name != ""

    def valid(self) -> bool:
        return (self.loext_graphic_properties
                and self.style_paragraph_properties
                and self.style_text_properties
                and self.libre_mono_font)
                #and self.libre_mono_font_size)


# This style is used to determine if we are inside a Table caption, for example in the following XML:
#  (Here backslash \ is used to indicate a line continuation here in the example, in the real XML
#   there would be no newline character or backslash.)
#
#   <text:p text:style-name="P14560">Table \
#     <text:sequence text:ref-name="refTable701" text:name="Table" \
#      text:formula="ooow:Table+1" style:num-format="1">F.2\
#     </text:sequence>: RUNSPEC Input and Output File Format Keywords\
#   </text:p>
#
# We would like to avoid linking the RUNSPEC keyword in this case. The TableCaptionInfo class
# below is used to help determine if we are inside such a Table caption.
#
@dataclass
class TableCaptionInfo:
    seen_table_txt: bool = False
    in_sequence: bool = False
    end_sequence_seen: bool = False

    def valid(self) -> bool:
        return (self.seen_table_txt and self.end_sequence_seen)


class FileHandler(xml.sax.handler.ContentHandler):
    def __init__(
        self,
        file_info: str,
        file_type: FileType,
        kw_uri_map: dict[str, str]
    ) -> None:
        self.file_info = file_info   # Keyword name or chapter name
        self.file_type = file_type
        self.kw_uri_map = kw_uri_map
        self.in_section = False
        # For empty tags, we use a special trick to rewrite them with a shortened
        #  end /> tag instead of the full end tag </tag>
        self.start_tag_open = False
        self.in_p = False
        self.table_caption_info = TableCaptionInfo() # Information about the table caption
        # Paragraphs with a certain style with monospaced text, should not be linked
        self.mono_paragraph_style = MonoParagraphStyle()
        self.in_mono_paragraph = False  # Inside a paragraph with monospaced text
        self.mono_paragraph_styles = set()  # Style names that use monospaced text
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

    def check_mono_paragraph(self, attrs: xml.sax.xmlreader.AttributesImpl) -> None:
        if "text:style-name" in attrs.getNames():
            style_name = attrs.getValue("text:style-name")
            if style_name in self.mono_paragraph_styles:
                self.in_mono_paragraph = True

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
        if self.in_p and content.startswith("Table "):
            self.table_caption_info.seen_table_txt = True

    def collect_example_style(self, attrs: xml.sax.xmlreader.AttributesImpl) -> None:
        # Collect the paragraph styles that use fixed width fonts
        if "style:name" in attrs.getNames():
            style_name = attrs.getValue("style:name")
            self.example_styles.add(style_name)

    def endDocument(self):
        assert(self.char_buf == "")  # All content should have been written to the content buffer

    def endElement(self, name: str):
        self.maybe_write_characters()
        if self.office_body_found:
            if name == "text:sequence":
                if self.table_caption_info.in_sequence:
                    self.table_caption_info.end_sequence_seen = True
                    self.table_caption_info.in_sequence = False
            elif name == "text:p":
                self.p_recursion -= 1
                if self.p_recursion == 0:
                    self.in_p = False
                self.is_example_p.pop()
                self.in_mono_paragraph = False   # Assume this is not recursive
                self.table_caption_info = TableCaptionInfo() # Reset the info
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
        else:  # office:body not found yet
            if name == "style:style":
                self.maybe_add_mono_paragraph_style()
        if self.start_tag_open:
            self.content.write("/>")
            self.start_tag_open = False
        else:
            self.content.write(xml_helpers.endtag(name))

    def get_content(self) -> str:
        return self.content.getvalue()

    def get_num_links_inserted(self) -> int:
        return self.num_links_inserted

    def is_table_caption(self, content: str) -> bool:
        # Check if the content is a specific table caption, in that case we should not insert links
        keyword_name = self.file_info
        return re.search(rf'{re.escape(keyword_name)} Keyword Description', content)

    def maybe_add_mono_paragraph_style(self) -> None:
        if self.mono_paragraph_style.valid():
            self.mono_paragraph_styles.add(self.mono_paragraph_style.style_name)
        self.mono_paragraph_style = MonoParagraphStyle()  # Reset the style

    def maybe_collect_mono_paragraph_style(
        self, name: str, attrs: xml.sax.xmlreader.AttributesImpl
    ) -> None:
        if name == "style:style":
            attr = "style:parent-style-name"
            if attr in attrs.getNames():
                if attrs.getValue(attr) == "Text_20_body":
                    attr2 = "style:family"
                    if attr2 in attrs.getNames():
                        if attrs.getValue(attr2) == "paragraph":
                            attr3 = "style:name"
                            if attr3 in attrs.getNames():
                                style_name = attrs.getValue(attr3)
                                self.mono_paragraph_style.style_name = style_name
        elif self.mono_paragraph_style.in_style_style_element():
            if name == "loext:graphic-properties":
                self.mono_paragraph_style.loext_graphic_properties = True
            elif name == "style:paragraph-properties":
                self.mono_paragraph_style.style_paragraph_properties = True
            elif name == "style:text-properties":
                self.mono_paragraph_style.style_text_properties = True
                attr = "style:font-name"
                if attr in attrs.getNames():
                    if attrs.getValue(attr) == "Liberation Mono":
                        self.mono_paragraph_style.libre_mono_font = True
                # NOTE: Originally we wanted to check for a specific font size equal to 8pt,
                #    but it might be changed in the future. Therefore we skip the check for
                #    the font size for now
                #attr2 = "fo:font-size"
                #if attr2 in attrs.getNames():
                    #fontsize = attrs.getValue(attr2)
                    #if len(fontsize) > 0:  # Check if the font size is set
                    #    self.mono_paragraph_style.libre_mono_font_size = True

    def maybe_write_characters(self) -> None:
        if len(self.char_buf) > 0:
            # NOTE: We need to escape the content before we apply the regex pattern
            #  because it may insert tags (<text:a ...>) that should not be escaped.
            characters = xml_helpers.escape(self.char_buf)
            if self.office_body_found:
                if (self.in_p
                    and (not self.in_a)
                    and (not self.not_keyword)
                    and (not self.in_math)
                    and (not self.in_binary_data)
                    and (not self.in_draw_frame)
                    and (not self.in_mono_paragraph)
                    and (not self.table_caption_info.valid())
                ):
                    if not self.is_example_p[-1]:
                        if ((    self.file_type == FileType.CHAPTER
                              or self.file_type == FileType.APPENDIX) or
                            (self.file_type == FileType.SUBSECTION and
                              (not self.is_table_caption(characters)))):
                                characters = self.regex.sub(self.replace_match_function, characters)
            self.content.write(characters)
            self.char_buf = ""

    def replace_match_function(self, match: re.Match) -> str:
        keyword = match.group(0)
        uri = self.kw_uri_map[keyword]
        self.num_links_inserted += 1
        return f'<text:a xlink:href="#{uri}">{keyword}</text:a>'

    # This callback is used for debugging, it can be used to print
    #  line numbers in the XML file, for example:
    #          print(f"Line: {self.locator.getLineNumber()}")
    def setDocumentLocator(self, locator):
        self.locator = locator

    def startDocument(self):
        self.content.write(xml_helpers.HEADER)

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
                            self.collect_example_style(attrs)
                self.maybe_collect_mono_paragraph_style(name, attrs)
        else:
            if name == "text:sequence":
                if self.table_caption_info.seen_table_txt:
                    self.table_caption_info.in_sequence = True
            elif name == "text:p":
                self.in_p = True
                self.p_recursion += 1
                self.update_example_stack(attrs)
                self.check_mono_paragraph(attrs)
            elif name == "text:a":
                # We are inside an anchor, and we should not insert another text:a tag here
                self.in_a = True
            elif name == "text:span":
                if "text:style-name" in attrs.getNames():
                    style_name = attrs.getValue("text:style-name")
                    if style_name == "NotKeyword":
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
        self.content.write(xml_helpers.starttag(name, attrs, close_tag=False))

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
        subsections: list[str],
        chapters: list[str],
        appendices: list[str],
        filename: str|None,
        kw_uri_map: dict[str, str],
        check_changed: bool
    ) -> None:
        self.maindir = maindir
        self.subsections = subsections
        self.chapters = chapters
        self.appendices = appendices
        self.filename = filename
        self.kw_uri_map = kw_uri_map
        self.check_changed = check_changed

    def insert_links(self) -> int:
        num_links_inserted = 0
        if len(self.chapters) > 0:
            num_links_inserted += self.insert_links_in_chapters()
        if len(self.subsections) > 0:
            num_links_inserted += self.insert_links_in_subsections()
        if len(self.appendices) > 0:
            num_links_inserted += self.insert_links_in_appendices()
        return num_links_inserted

    def insert_links_in_chapters(self) -> int:
        start_dir = self.maindir / Directories.chapters
        num_links_inserted = 0
        for chapter in self.chapters:
            logging.info(f"Processing chapter: {chapter}")
            filename = f"{chapter}.{FileExtensions.fodt}"
            path = start_dir / filename
            count = self.insert_links_in_file(path, filename, FileType.CHAPTER)
            num_links_inserted += count
        return num_links_inserted

    def insert_links_in_appendices(self) -> int:
        start_dir = self.maindir / Directories.appendices
        num_links_inserted = 0
        for appendix in self.appendices:
            logging.info(f"Processing appendix: {appendix}")
            filename = f"{appendix}.{FileExtensions.fodt}"
            path = start_dir / filename
            count = self.insert_links_in_file(path, filename, FileType.APPENDIX)
            num_links_inserted += count
        return num_links_inserted

    def insert_links_in_subsections(self) -> int:
        start_dir = self.maindir / Directories.chapters / Directories.subsections
        num_links_inserted = 0
        if self.filename:
            assert len(self.subsections) == 1
            path = start_dir / self.subsections[0] / self.filename
            keyword_name = self.filename.removesuffix(f".{FileExtensions.fodt}")
            num_links_inserted = self.insert_links_in_file(path, keyword_name, FileType.SUBSECTION)
        else:
            for subsection in self.subsections:
               count =  self.insert_links_in_subsection(start_dir, subsection)
               num_links_inserted += count
        return num_links_inserted

    def insert_links_in_subsection(self, start_dir: Path, subsection: str) -> int:
        files_processed = 0
        num_links_inserted = 0
        item = start_dir / subsection
        logging.info(f"Processing subsection: {item.name}")
        for item2 in item.iterdir():
            if item2.suffix == f".{FileExtensions.fodt}":
                keyword_name = item2.name.removesuffix(f".{FileExtensions.fodt}")
                files_processed += 1
                count = self.insert_links_in_file(
                    item2, keyword_name, FileType.SUBSECTION, verbose=False, indent=True
                )
                num_links_inserted += count
        if files_processed == 0:
            logging.info("  No files processed.")
        else:
            logging.info(f"  Processed {files_processed} files.")
        return num_links_inserted

    def insert_links_in_file(
        self,
        filename: Path,
        file_info: str,
        file_type: FileType,
        verbose: bool = True,
        indent: bool = False
    ) -> int:
        parser = xml.sax.make_parser()
        handler = FileHandler(file_info, file_type, self.kw_uri_map)
        parser.setContentHandler(handler)
        try:
            parser.parse(str(filename))
        except HandlerDoneException as e:
            pass
        num_links_inserted = handler.get_num_links_inserted()
        indent_str = "  " if indent else ""
        if num_links_inserted > 0:
            if self.check_changed:
                logging.info(f"{indent_str}{filename.name}: Links would be inserted.")
            else:
                with open(filename, "w", encoding='utf8') as f:
                    f.write(handler.content.getvalue())
                logging.info(f"{indent_str}{filename.name}: Inserted {num_links_inserted} links.")
        else:
            if verbose and not self.check_changed:
                logging.info(f"{indent_str}{filename.name}: No links inserted.")
        return num_links_inserted

VALID_SUBSECTIONS = "4.3,5.3,6.3,7.3,8.3,9.3,10.3,11.3,12.3"
VALID_CHAPTERS = "1,2,3,4,5,6,7,8,9,10,11,12"
VALID_APPENDICES = "B,C,D,E,F"

def validate_subsections(subsections: str|None, filename: str|None) -> list[str]:
    if subsections is None:
        return []
    subsections = subsections.split(",")
    if filename is not None:
        if len(subsections) != 1:
            raise ValueError("If --filename is given, only one subsection can be specified.")
    valid_subsections = VALID_SUBSECTIONS.split(",")
    for subsection in subsections:
        if subsection not in valid_subsections:
            raise ValueError(f"Invalid subsection: {subsection}")
    return subsections

def validate_chapters(chapters: str|None) -> list[str]:
    if chapters is None:
        return []
    chapters = chapters.split(",")
    valid_chapters = VALID_CHAPTERS.split(",")
    for chapter in chapters:
        if chapter not in valid_chapters:
            raise ValueError(f"Invalid chapter: {chapter}")
    return chapters

def validate_appendices(appendices: str|None) -> list[str]:
    if appendices is None:
        return []
    appendices = appendices.split(",")
    valid_appendices = VALID_APPENDICES.split(",")
    for appendix in appendices:
        if appendix not in valid_appendices:
            raise ValueError(f"Invalid appendix: {appendix}")
    return appendices

# fodt-link-keywords
# ------------------
#
# SHELL USAGE:
#
# fodt-link-keywords \
#    --maindir=<main_dir> \
#    --keyword_dir=<keyword_dir> \
#    --subsections=<subsections> \
#    --chapters=<chapters> \
#    --appendices=<appendices> \
#    --filename=<filename> \
#    --all \
#    --generate-map \
#    --check-changed \
#
# DESCRIPTION:
#
#   Links all keyword names found inside <p> tags in the subsection documents to the
#   corresponding keyword subsection subdocument.
#
#   If the option --generate-map is given, the script will generate the keyword URI map on the fly
#   (but not save it to disk). This is useful if you suspect that libreoffice might have changed the
#   references to the keywords. Another option is to run the script "fodt-gen-kw-uri-map" to generate
#   a new map (this will save the map to disk).
#
#   If --subsections is given, the script will only process the specified subsections, or
#   if --chapters is given, the script will only process the specified chapters, or
#   if --appendices is given, the script will only process the specified appendices. If --filename
#   and --subsections are given, the script will only process the specified file within the
#   specified subsection. If --all is given, the script will process all files. Option --all
#   cannot be combined with --chapters, --appendices or --subsections.
#
#   If --check-changed is given, the script will only check if the files have changed and not write
#   the files back to disk. It will return a non-zero exit code if any files have changed.
#
# EXAMPLES:
#
#    fodt-link-keywords --subsections=5.3
#
#  Will use the default values: --maindir=../../parts, --keyword_dir=../../keyword-names,
#  and will process only the keywords in subsection 5.3, and will generate the mapping on the fly.
#
#    fodt-link-keywords --subsections=10.3 --filename=AQANCONL.fodt
#
#  Will process only the file "AQANCONL.fodt" in subsection 10.3.
#
#    fodt-link-keywords --chapters=4,5
#
#  Will process will process chapters 4 and 5.
#
#   fodt-link-keywords --all
#
#  Will process all keywords in subsections 4.3, 5.3, 6.3, 7.3, 8.3, 9.3, 10.3, 11.3, and 12.3.
#  Then chapters 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, and 12, and finally appendices B, C, D, E, and F.
#
@click.command()
@ClickOptions.maindir()
@ClickOptions.keyword_dir
@click.option('--subsections', help='The subsections to process')
@click.option('--chapters', help='The chapters to process')
@click.option('--appendices', help='The appendices to process')
@click.option('--generate-map', is_flag=True, default=False, help='Do not use the mapping file "meta/kw_uri_map.txt". If you suspect that libreoffice might have changed the references to the keywords, you can use this option to bypass the kw_uri_map.txt file and generate the map on the fly. Another option is to run the script "fodt-gen-kw-uri-map" to generate a new map.')
@click.option('--filename', help='The filename to process')
@click.option('--all', is_flag=True, help='Process all files')
@click.option('--check-changed', is_flag=True, help='Check if files have changed')
def link_keywords(
    maindir: str|None,
    keyword_dir: str|None,
    subsections: str|None,
    chapters: str|None,
    appendices: str|None,
    generate_map: bool,
    filename: str|None,
    all: bool,
    check_changed: bool
) -> None:
    logging.basicConfig(level=logging.INFO)
    maindir = helpers.get_maindir(maindir)
    keyword_dir = helpers.get_keyword_dir(keyword_dir)
    if all:
        if sum(x is not None for x in [subsections, chapters, appendices]) != 0:
            raise ValueError(
                "Option --all cannot be combined with any of --subsections, --chapters "
                "and --appendices."
            )
        subsections = VALID_SUBSECTIONS
        chapters = VALID_CHAPTERS
        appendices = VALID_APPENDICES
    subsections = validate_subsections(subsections, filename)
    chapters = validate_chapters(chapters)
    appendices = validate_appendices(appendices)
    if generate_map:
        kw_uri_map = keyword_uri_map_generator.get_kw_uri_map(maindir, keyword_dir)
    else:
        kw_uri_map = helpers.load_kw_uri_map(maindir)
    num_links_inserted = InsertLinks(
        maindir,
        subsections,
        chapters,
        appendices,
        filename,
        kw_uri_map,
        check_changed
    ).insert_links()
    if check_changed:
        if num_links_inserted > 0:
            logging.error(f"Files have changed. {num_links_inserted} links would be inserted.")
            exit(1)
        else:
            logging.info("Files have not changed.")
            exit(0)

if __name__ == "__main__":
    link_keywords()
