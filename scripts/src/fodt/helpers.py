import importlib.resources  # access non-code resources
import shutil
import xml.sax.saxutils

from pathlib import Path
from fodt.constants import Directories, FileExtensions, FileNames
from fodt.exceptions import InputException

class Helpers:

    @staticmethod
    def chapter_fodt_file_path(
        outputdir: str,
        chapter: str,
    ) -> Path:
        filename = (
            Path(outputdir) /
            Directories.chapters /
            f"{chapter}.{FileExtensions.fodt}"
        )
        return filename

    @staticmethod
    def create_backup_document(filename) -> None:
        outputdir = filename.parent
        backupdir = outputdir / Directories.backup
        backupdir.mkdir(parents=True, exist_ok=True)
        shutil.copy(filename, backupdir)
        backup_file = backupdir / filename.name
        return backup_file

    @staticmethod
    def get_keyword_dir(keyword_dir: str) -> str:
        if keyword_dir is None:
            try_path = Path('../keyword-names')
            if try_path.exists():
                keyword_dir = try_path
            else:
                raise FileNotFoundError(f"Keyword names directory not found.")
        return keyword_dir

    @staticmethod
    def keyword_file(outputdir: Path, chapter: int, section: int) -> Path:
        directory = f"{chapter}.{section}"
        filename = FileNames.keywords
        dir_ = outputdir / Directories.info / Directories.keywords / directory
        file = dir_ / filename
        return file

    @staticmethod
    def keyword_file_v2(keyword_dir: str, chapter: int, section: int) -> Path:
        directory = f"{chapter}.{section}"
        file = Path(keyword_dir) / directory / FileNames.keywords
        return file

    @staticmethod
    def keyword_fodt_file_path(
        outputdir: str,
        chapter: str,
        section: str,
        keyword_name: str
    ) -> Path:
        directory = f"{chapter}.{section}"
        filename = (
            Path(outputdir) /
            Directories.chapters /
            Directories.subsections /
            directory /
            f"{keyword_name}.{FileExtensions.fodt}"
        )
        return filename

    @staticmethod
    def keywords_inverse_map(keyw_list: list[str]) -> dict[str, int]:
        return {keyw_list[i]: i + 1 for i in range(len(keyw_list))}

    @staticmethod
    def read_keyword_order(outputdir: Path, chapter: int, section: int) -> list[str]:
        file = Helpers.keyword_file(outputdir, chapter, section)
        if not file.exists():
            raise InputException(f"Could not find file {file}.")
        with open(file, "r", encoding='utf8') as f:
            keywords = [line.strip() for line in f.readlines()]
        return keywords

    def read_keyword_order_v2(keyword_dir: str, chapter: int, section: int) -> list[str]:
        file = Helpers.keyword_file_v2(keyword_dir, chapter, section)
        if not file.exists():
            raise InputException(f"Could not find file {file}.")
        with open(file, "r", encoding='utf8') as f:
            keywords = [line.strip() for line in f.readlines()]
        return keywords

    @staticmethod
    def read_keyword_template() -> str:
        # NOTE: This template was created from the COLUMNS keyword in section 4.3
        path = importlib.resources.files("fodt.data").joinpath("keyword_template.xml")
        with open(path, "r", encoding='utf8') as f:
            template = f.read()
        return template

    @staticmethod
    def replace_section_callback(part: str, keyword: str) -> str:
        section = ".".join(part.split(".")[:2])
        href = f"{Directories.subsections}/{section}/{keyword}.fodt"
        href = xml.sax.saxutils.escape(href)
        return (f"""<text:section text:style-name="Sect1" text:name="Section{section}:{keyword}" """
                   f"""text:protected="true">\n"""
                f"""     <text:section-source xlink:href="{href}" """
                   f"""text:filter-name="OpenDocument Text Flat XML" """
                   f"""text:section-name="{keyword}"/>\n"""
                f"""    </text:section>\n""")

    @staticmethod
    def split_section(section: str) -> tuple[str, str]:
        parts = section.split(".")
        if len(parts) != 2:
            raise ValueError(f"Section must be of the form <chapter>.<section>, but got {section}")
        # check that chapter and section are integers
        try:
            int(parts[0])
            int(parts[1])
        except ValueError as e:
            raise ValueError(f"Section must be of the form <chapter>.<section>, "
                             f"where <chapter> and <section> are integers, but got {section}")
        return (parts[0], parts[1])


    @staticmethod
    def write_keyword_order(outputdir: Path, chapter: int, section: int,
                            keywords: list[str]
    ) -> None:
        file = Helpers.keyword_file(outputdir, chapter, section)
        with open(file, "w", encoding='utf8') as f:
            for keyword in keywords:
                f.write(f"{keyword}\n")
        return

    @staticmethod
    def write_keyword_order_v2(keyword_dir: str, chapter: int, section: int,
                               keywords: list[str]
    ) -> None:
        file = Helpers.keyword_file_v2(keyword_dir, chapter, section)
        with open(file, "w", encoding='utf8') as f:
            for keyword in keywords:
                f.write(f"{keyword}\n")
        return
