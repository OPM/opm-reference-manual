import importlib.resources  # access non-code resources
import re
import shutil

from pathlib import Path
from fodt.constants import Directories, FileExtensions, FileNames
from fodt.exceptions import InputException, ParsingException
from fodt import xml_helpers

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

def create_backup_document(filename) -> None:
    outputdir = filename.parent
    backupdir = outputdir / Directories.backup
    backupdir.mkdir(parents=True, exist_ok=True)
    shutil.copy(filename, backupdir)
    backup_file = backupdir / filename.name
    return backup_file

def derive_maindir_from_filename(filename: str) -> Path:
    """
    :param filename: Assumed to be an aboslute path to file inside maindir or subdirectories of maindir.
    :return: The absolute path to the maindir.
    """
    filename = Path(filename)
    assert filename.is_absolute()
    # Search parent directories for main.fodt in a directory called "parts"
    while True:
        # Check if we have reached the root directory
        #  filename.parent == filename is True if filename is the root directory
        if filename.parent == filename:
            raise FileNotFoundError(f"Could not derive maindir from filename: "
                  f"Could not find '{FileNames.main_document}' in a directory "
                  f"called '{Directories.parts}' by searching the parent "
                  f"directories of filename."
            )
        if filename.parent.name == Directories.parts:
            if (filename.parent / FileNames.main_document).exists():
                return filename.parent
        filename = filename.parent
    # This should never be reached

def get_keyword_dir(keyword_dir: str|None) -> Path:
    if keyword_dir is None:
        # Default value for keyword_dir is a relative path like "../../keyword-names"
        keyword_dir = Path(f'../../{Directories.keyword_names}')
    if not keyword_dir.exists():
        main_dir = locate_maindir_from_current_dir()
        keyword_dir = main_dir.parent / Directories.keyword_names
        if not keyword_dir.exists():
            raise FileNotFoundError(f"Keyword names directory not found.")
    return keyword_dir

def get_maindir(maindir: str) -> Path:
    """
    :param maindir: The main directory of the project. Can be relative or absolute.
    :return: The absolute path to the main directory.
    """
    if maindir is None:
        # Try to find maindir by searching the current working directory and its
        # parent directories for a file main.fodt inside a directory called parts
        maindir = locate_maindir_from_current_dir()
    else:
        maindir = Path(maindir)
        if not maindir.is_dir():
            # The default value for maindir is a relative path like "../../parts"
            # If it does not exist, try to find maindir by searching the current
            # working directory and its parent directories. This is better than
            # raising an exception here I think..
            maindir = locate_maindir_from_current_dir()
        else:
            maindir = maindir.absolute()
    return maindir

def keyword_file(outputdir: Path, chapter: int, section: int) -> Path:
    directory = f"{chapter}.{section}"
    filename = FileNames.keywords
    dir_ = outputdir / Directories.info / Directories.keywords / directory
    file = dir_ / filename
    return file

def keyword_file_v2(keyword_dir: str, chapter: int, section: int) -> Path:
    directory = f"{chapter}.{section}"
    file = Path(keyword_dir) / directory / FileNames.keywords
    return file

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

def keywords_inverse_map(keyw_list: list[str]) -> dict[str, int]:
    return {keyw_list[i]: i + 1 for i in range(len(keyw_list))}


def locate_maindir_and_filename(
    maindir: str,
    filename: str
) -> tuple[Path, Path]:
    """
    :param maindir: The main directory of the project. Can be relative or absolute.
    :param filename: The filename to locate. Can be relative or absolute. ``filename`` is assumed to be a file in maindir or a file in one of its subdirectories.
    :return: A tuple of the form (maindir, filename), where both are absolute paths."""
    filename = Path(filename)
    maindir = Path(maindir)  # maindir can be absolute or relative
    # If filename is an absolute path, ignore maindir
    if filename.is_absolute():
        assert filename.exists()
        maindir = derive_maindir_from_filename(filename)
        return maindir, Path(filename)
    else:
        # Try to find filename by concatenating maindir and filename
        if not maindir.is_absolute():
            # If both maindir and filename are relative, make filename relative
            # to maindir instead of relative to the current working directory
            maindir_abs = Path.cwd() / maindir
            filename_abs = maindir_abs / filename
            if filename_abs.exists():
                return maindir_abs, filename_abs
        else:
            filename = maindir / filename
            if filename.exists():
                return maindir, filename
        # If not found, search for filename relative to the current working directory
        filename = Path.cwd() / filename
        if filename.exists():
            maindir = derive_maindir_from_filename(filename)
            return maindir, filename
    raise FileNotFoundError(f"Could not find '{filename.name}' in a directory "
                            f"called '{maindir.name}'.")


def locate_maindir_from_current_dir() -> Path:
    cwd = Path.cwd()
    # We cannot use derive_maindir_from_filename() here because cwd does not
    # have to be inside maindir in this case
    while True:
        # Check if we have reached the root directory
        #  cwd.parent == cwd is True if filename is the root directory
        if cwd.parent == cwd:
            raise FileNotFoundError(f"Could not derive maindir from cwd: "
                  f"Could not find '{FileNames.main_document}' in a directory "
                  f"called '{Directories.parts}' by searching the parent "
                  f"directories of cwd."
            )
        # Check if there is a sibling directory called "parts" with a file main.fodt
        dir_ = cwd / Directories.parts
        if dir_.is_dir():
            if (dir_ / FileNames.main_document).exists():
                return dir_
        cwd = cwd.parent
    # This line should never be reached

def locate_maindir_from_current_dir() -> Path:
    cwd = Path.cwd()
    # We cannot use derive_maindir_from_filename() here because cwd does not
    # have to be inside maindir in this case
    while True:
        # Check if we have reached the root directory
        #  cwd.parent == cwd is True if filename is the root directory
        if cwd.parent == cwd:
            raise FileNotFoundError(f"Could not derive maindir from cwd: "
                  f"Could not find '{FileNames.main_document}' in a directory "
                  f"called '{Directories.parts}' by searching the parent "
                  f"directories of cwd."
            )
        # Check if there is a sibling directory called "parts" with a file main.fodt
        dir_ = cwd / Directories.parts
        if dir_.is_dir():
            if (dir_ / FileNames.main_document).exists():
                return dir_
        cwd = cwd.parent
    # This line should never be reached

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

def read_keyword_order(outputdir: Path, chapter: int, section: int) -> list[str]:
    file = keyword_file(outputdir, chapter, section)
    if not file.exists():
        raise InputException(f"Could not find file {file}.")
    with open(file, "r", encoding='utf8') as f:
        keywords = [line.strip() for line in f.readlines()]
    return keywords

def read_keyword_order_v2(keyword_dir: str, chapter: int, section: int) -> list[str]:
    file = keyword_file_v2(keyword_dir, chapter, section)
    if not file.exists():
        raise InputException(f"Could not find file {file}.")
    with open(file, "r", encoding='utf8') as f:
        keywords = [line.strip() for line in f.readlines()]
    return keywords

def read_keyword_template() -> str:
    # NOTE: This template was created from the COLUMNS keyword in section 4.3
    path = importlib.resources.files("fodt.data").joinpath("keyword_template.xml")
    with open(path, "r", encoding='utf8') as f:
        template = f.read()
    return template

def replace_section_callback(part: str, keyword: str) -> str:
    section = ".".join(part.split(".")[:2])
    href = f"{Directories.subsections}/{section}/{keyword}.fodt"
    href = xml_helpers.escape(href)
    return (f"""<text:section text:style-name="Sect1" text:name="Section{section}:{keyword}" """
               f"""text:protected="true">\n"""
            f"""     <text:section-source xlink:href="{href}" """
               f"""text:filter-name="OpenDocument Text Flat XML" """
               f"""text:section-name="{keyword}"/>\n"""
            f"""    </text:section>\n""")

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


def write_keyword_order(outputdir: Path, chapter: int, section: int,
                        keywords: list[str]
) -> None:
    file = keyword_file(outputdir, chapter, section)
    with open(file, "w", encoding='utf8') as f:
        for keyword in keywords:
            f.write(f"{keyword}\n")
    return

def write_keyword_order_v2(keyword_dir: str, chapter: int, section: int,
                           keywords: list[str]
) -> None:
    file = keyword_file_v2(keyword_dir, chapter, section)
    with open(file, "w", encoding='utf8') as f:
        for keyword in keywords:
            f.write(f"{keyword}\n")
    return
