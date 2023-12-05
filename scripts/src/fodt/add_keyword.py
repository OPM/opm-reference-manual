import logging
import click
from pathlib import Path
from fodt.constants import ClickOptions, Directories, FileExtensions
from fodt.create_subdocument import CreateSubDocument3
from fodt.helpers import Helpers
from fodt.remove_subsections import RemoveSubSections

class AddKeyword():
    def __init__(
        self,
        maindir: str,
        keyword_dir: str,
        keyword: str,
        chapter: int,
        section: int
    ) -> None:
        self.maindir = maindir
        self.keyword_dir = Helpers.get_keyword_dir(keyword_dir)
        self.keyword = keyword
        self.chapter = chapter
        self.section = section
        self.add_keyword()
        self.update_subdocument()
        self.update_chapter_document()

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
            self.maindir, self.keyword_dir, self.chapter, self.section, self.keyword
        )



# fodt-add-keyword
# -----------------
#
# SHELL USAGE:
#
# fodt-add-keyword --maindir=<main_dir> \
#                   --keyword=<keyword> \
#                   --section=<section_number>
#
# DESCRIPTION:
#
# Adds a new keyword to the given chapter and section
#
# EXAMPLE:
#
#  fodt-add-keyword --maindir=../parts \
#                   --keyword=NEW_KEYWORD \
#                   --section=4.3
#
@click.command()
@ClickOptions.maindir
@ClickOptions.keyword_dir
@click.option('--keyword', type=str, required=True, help='Name of the keyword to add.')
@click.option('--section', type=str, required=True, help='Number of the section.')
def add_keyword(maindir: str, keyword_dir: str, keyword: str, section: str) -> None:
    logging.basicConfig(level=logging.INFO)
    (chapter, section) = Helpers.split_section(section)
    add_keyword = AddKeyword(maindir, keyword_dir, keyword, chapter, section)

if __name__ == "__main__":
    add_keyword()