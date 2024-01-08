import io
import logging
import re
import shutil
import tempfile
import xml.sax
import xml.sax.handler
import xml.sax.xmlreader
import xml.sax.saxutils
from pathlib import Path

import click

from fodt.constants import ClickOptions, Directories, FileExtensions, KeywordStatus
from fodt.create_subdocument import CreateSubDocument3
from fodt.helpers import Helpers
from fodt.remove_subsections import RemoveSubSections
from fodt.templates import Templates
from fodt.xml_helpers import XMLHelper

class AppendixHandler(xml.sax.handler.ContentHandler):
    def __init__(self, keyword: str, status: KeywordStatus, title: str) -> None:
        self.keyword_name = keyword
        self.keyword_status = status
        self.keyword_title = title
        self.in_styles = False
        self.content = io.StringIO()
        self.current_row = io.StringIO()
        self.rows = []
        self.current_keyword = None
        self.keyword_names = []
        self.between_rows = ''
        self.style_templates = {
            'AppendixA_TableRow': Templates.AppendixA.Styles.table_row_template,
            'AppendixA_TableCell': Templates.AppendixA.Styles.table_cell_template,
            'AppendixA_TableCell_Orange': Templates.AppendixA.Styles.table_cell_orange_template,
            'AppendixA_TableCell_Green': Templates.AppendixA.Styles.table_cell_green_template,
        }
        self.style_names = {keys for keys in self.style_templates.keys()}
        self.found_appendix_table = False
        self.in_appendix_table = False
        self.in_table_cell = False
        self.in_table_row = False
        self.keyword_table_number = self.get_keyword_table_number()
        self.current_table_number = 0

    def characters(self, content: str):
        if self.in_styles:
            self.content.write(xml.sax.saxutils.escape(content))
        elif self.in_appendix_table:
            if self.in_table_row:
                self.current_row.write(xml.sax.saxutils.escape(content))
            else:
                self.between_rows += content
                # Capture stuff between the rows, such that we
                # can add it back. There can be tags like
                # <text:soft-page-break></text:soft-page-break>
                #   between the table:table-row tags...
        else:
            if self.in_table_cell:
                if content.startswith(
                    'Alphabetic Listing of Keywords Starting with the Letter '
                ):
                    self.current_table_number += 1
                    if self.current_table_number == self.keyword_table_number:
                        self.found_appendix_table = True
            self.content.write(xml.sax.saxutils.escape(content))

    def endElement(self, name: str):
        if name == "table:table-cell":
            self.in_table_cell = False
        elif name == "table:table-row":
            self.in_table_row = False
        if self.in_appendix_table:
            if name == "table:table-row":
                self.current_row.write(XMLHelper.endtag(name))
                current_row = self.between_rows + self.current_row.getvalue()
                self.between_rows = ''
                self.rows.append(current_row)
                self.keyword_names.append(self.current_keyword)
            elif name == "table:table":
                self.in_appendix_table = False
                self.write_appendix_table()
                self.content.write(self.between_rows)
                self.content.write(XMLHelper.endtag(name))
            elif self.in_table_row:
                self.current_row.write(XMLHelper.endtag(name))
            else:
                self.between_rows += XMLHelper.endtag(name)
        else:
            if self.in_styles:
                if name == "office:automatic-styles":
                    self.in_styles = False
                    self.write_missing_styles()
            self.content.write(XMLHelper.endtag(name))

    def extract_keyword_name(self, href: str) -> str:
        # Assume href starts with "#xxx.yyy.zzz.KEYWORD_NAME<space>"
        if m:= re.match(r"#\d+\.\d+\.\d+\.(\w+)\s+", href):
            return m.group(1)
        else:
            return '<NOT FOUND>'

    def get_content(self) -> str:
        return self.content.getvalue()

    def get_keyword_table_number(self) -> int:
        first_letter = self.keyword_name[0]
        if first_letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            return ord(first_letter) - ord('A') + 1
        else:
            raise ValueError(f"Invalid keyword name: {self.keyword_name}.")

    def get_new_appendix_row(self) -> str:
        new_row = Templates.AppendixA.Content.table_row_template
        new_row = re.sub(r'###KEYWORD_NAME###', self.keyword_name, new_row)
        new_row = re.sub(r'###KEYWORD_DESCRIPTION###', self.keyword_title, new_row)
        if self.keyword_status == KeywordStatus.ORANGE:
            color = "Orange"
        elif self.keyword_status == KeywordStatus.GREEN:
            color = "Green"
        else:
            raise ValueError(f"Invalid status value: {self.keyword_status}.")
        new_row = re.sub(r'###COLOR###', color, new_row)
        return new_row

    def startDocument(self):
        self.content.write(XMLHelper.header)

    def startElement(self, name:str, attrs: xml.sax.xmlreader.AttributesImpl):
        if self.in_styles:
            if name == "style:style":
                if "style:name" in attrs.getNames():
                    style_name = attrs.getValue("style:name")
                    if style_name in self.style_names:
                        # If the style already exists, remove it from the set
                        self.style_names.remove(style_name)
        elif name == "office:automatic-styles":
            self.in_styles = True
        if self.in_styles:
            self.content.write(XMLHelper.starttag(name, attrs))
        else:
            if name == "table:table-row":
                self.in_table_row = True
                if self.found_appendix_table:
                    self.in_appendix_table = True
                    self.found_appendix_table = False
                if self.in_appendix_table:
                    self.current_row = io.StringIO()
            elif name == "table:table-cell":
                self.in_table_cell = True
            elif (name == "text:a" and self.in_appendix_table
                   and self.in_table_row and self.in_table_cell):
                if "xlink:href" in attrs.getNames():
                    self.current_keyword = self.extract_keyword_name(
                        attrs.getValue("xlink:href")
                    )
            if self.in_appendix_table:
                if self.in_table_row:
                    self.current_row.write(XMLHelper.starttag(name, attrs))
                else:
                    self.between_rows += XMLHelper.starttag(name, attrs)
            else:
                self.content.write(XMLHelper.starttag(name, attrs))

    def write_appendix_table(self) -> None:
        idx_found = False
        new_row = '\n' + self.get_new_appendix_row()
        for (idx, keyword_name) in enumerate(self.keyword_names):
            # Find the correct position to insert the new keyword
            if (not idx_found) and keyword_name >= self.keyword_name:
                self.content.write(new_row)
                idx_found = True
            self.content.write(self.rows[idx])
        if not idx_found:  # last item in the list
            self.content.write(new_row)

    def write_missing_styles(self):
        for style_name in self.style_names:
            self.content.write(self.style_templates[style_name])
            self.content.write("\n")


class AddKeyword():
    def __init__(
        self,
        maindir: str,
        keyword_dir: str,
        keyword: str,
        chapter: int,
        section: int,
        title: str,
        status: KeywordStatus
    ) -> None:
        self.maindir = maindir
        self.keyword_dir = Helpers.get_keyword_dir(keyword_dir)
        self.keyword = keyword
        self.chapter = chapter
        self.section = section
        self.title = title
        self.status = status
        self.add_keyword()
        self.update_subdocument()
        self.update_chapter_document()
        self.update_appendixA()

    def add_keyword(self) -> None:
        self.documentdir = Path(self.maindir) / Directories.chapters
        keyw_list = Helpers.read_keyword_order_v2(self.keyword_dir, self.chapter, self.section)
        #keyw_list = Helpers.read_keyword_order(self.documentdir, self.chapter, self.section)
        keywords = set(keyw_list)
        if self.keyword in keywords:
            logging.info(f"Keyword {self.keyword} already exists. Aborting.")
            return
        keywords.add(self.keyword)
        keyw_list = sorted(list(keywords))
        #Helpers.write_keyword_order(self.documentdir, self.chapter, self.section, keyw_list)
        Helpers.write_keyword_order_v2(self.keyword_dir, self.chapter, self.section, keyw_list)
        logging.info(f"Added keyword {self.keyword} to chapter {self.chapter}, section {self.section}.")
        return

    def update_appendixA(self) -> None:
        logging.info(f"Updating appendix A.")
        self.filename = Path(self.maindir) / Directories.appendices / f"A.{FileExtensions.fodt}"
        if not self.filename.is_file():
            raise FileNotFoundError(f"File {self.filename} not found.")
        # parse the xml file
        parser = xml.sax.make_parser()
        handler = AppendixHandler(self.keyword, self.status, self.title)
        parser.setContentHandler(handler)
        parser.parse(self.filename)
        # Take a backup of the file
        tempfile_ = tempfile.mktemp()
        shutil.copy(self.filename, tempfile_)
        logging.info(f"Created backup of {self.filename} in {tempfile_}.")
        # write handler content to file
        with open(self.filename, "w", encoding='utf8') as f:
            f.write(handler.content.getvalue())
        logging.info(f"Wrote updated file to {self.filename}.")

    def update_chapter_document(self) -> None:
        logging.info(f"Updating chapter document {self.chapter}.")
        filename = self.documentdir / f"{self.chapter}.{FileExtensions.fodt}"
        source_file = Helpers.create_backup_document(filename)
        dest_file = filename
        replace_callback = Helpers.replace_section_callback
        # NOTE: This will remove the subsection the first time it is called, and then
        #     if it is called again (for example using add-keyword), it will remove
        #     the inserted <text:section> tag that was inserted by the first call.
        #     And update those if the keyword list has changed (which it has if add-keyword was
        #     run).
        remover = RemoveSubSections(
            source_file,
            dest_file,
            self.keyword_dir,
            self.chapter,
            self.section,
            replace_callback
        )

    def update_subdocument(self) -> None:
        logging.info(f"Updating subdocument {self.chapter}.{self.section}:{self.keyword}.")
        creator = CreateSubDocument3(
            self.maindir,
            self.keyword_dir,
            self.chapter,
            self.section,
            self.keyword,
            self.title
        )



# fodt-add-keyword
# -----------------
#
# SHELL USAGE:
#
# fodt-add-keyword --maindir=<main_dir> \
#                   --keyword=<keyword> \
#                   --section=<section_number> \
#                   --title=<title> \
#                   --status=<status>
#
# DESCRIPTION:
#
# Adds a new keyword to the given chapter and section
#
# EXAMPLE:
#
#  fodt-add-keyword --maindir=../parts \
#                   --keyword=NEW_KEYWORD \
#                   --section=4.3 \
#                   --title="New Keyword" \
#                   --status=orange
#
@click.command()
@ClickOptions.maindir()
@ClickOptions.keyword_dir
@click.option('--keyword', type=str, required=True, help='Name of the keyword to add.')
@click.option('--section', type=str, required=True, help='Number of the section.')
@click.option(
    '--title', type=str, required=True, help='The link text displayed in the appendix.'
)
@click.option('--status', type=str, required=True, help='The status of the keyword.')
def add_keyword(
    maindir: str,
    keyword_dir: str,
    keyword: str,
    section: str,
    title: str,
    status: str
) -> None:
    logging.basicConfig(level=logging.INFO)
    (chapter, section) = Helpers.split_section(section)
    try:
        status = KeywordStatus[status.upper()]
    except ValueError:
        raise ValueError(f"Invalid status value: {status}.")
    add_keyword = AddKeyword(maindir, keyword_dir, keyword, chapter, section, title, status)

if __name__ == "__main__":
    add_keyword()