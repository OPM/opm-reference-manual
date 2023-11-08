import logging
import shutil
import subprocess

import click

from pathlib import Path
import fodt.string_functions
from fodt.constants import ClickOptions, Directories, FileNames
from fodt.remove_chapters import RemoveChapters

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

    def extract_chapters(self) -> None:
        logging.info(f"Extracting chapters {self.chapters}..")
        subprocess.run([
            "fodt-extract-chapters",
            f"--maindir={self.maindir}",
            f"--chapters={self.chapters}",
            f"--filename={self.filename}",
        ])

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
        self.extract_document_attrs()
        self.extract_chapters()
        self.create_subdocuments()
        self.create_main_document()


@click.command()
@ClickOptions.maindir
@ClickOptions.filename
def split_main(maindir: str, filename: str) -> None:
    logging.basicConfig(level=logging.INFO)
    splitter = Splitter(maindir, filename)
    splitter.split()

if __name__ == "__main__":
    split_main()