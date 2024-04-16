import enum
import click

class AutomaticStyles():
    attr_names = {"text:style-name", "table:style-name", "draw:style-name", "style:name"}

class ClickOptions():
    filename = lambda func: click.option(
        '--filename',
        envvar='FODT_FILENAME',
        required=True,
        help='Name of the FODT file to extract from. Used in combination with the --maindir option. This can be an absolute path or a relative path. If the filename is an absolute path, the --maindir option is ignored and the filename is used as is. If the filename is a relative path, and not found by concatenating maindir and filename it is searched for relative to the current working directory. If found, maindir is derived from the filename by searching its parent directories for a file main.fodt.'
    )(func)
    keyword_dir = lambda func: click.option(
        '--keyword-dir',
        type=str,
        required=False,
        help='Name of the directory containing the keyword names.'
    )(func)

    @staticmethod
    def maindir(required: bool = True, default: str = '../../parts'):
        def decorator(func):
            return click.option(
                '--maindir',
                envvar='FODT_MAIN_DIR',
                required=required,
                default=default,
                type=str,
                help='Directory where the main.fodt file is located. Often used in combination with the --filename option. Defaults to ../../parts (this default is based on that it is likely the user will run the script from the scripts/python directory) The environment variable FODT_MAIN_DIR can also be used to provide this value. If the filename is an absolute path, this option is ignored and maindir is derived from the filename by searching its parent directories for a file main.fodt. If the filename is a relative path, and not found by concatenating maindir and filename it is searched for relative to the current working directory. If found, maindir is derived from the filename by searching its parent directories for a file main.fodt.'
            )(func)
        return decorator

class Directories():
    appendices = "appendices"
    backup = "backup"
    info = "info"
    keywords = "keywords"
    keyword_names = "keyword-names"
    meta = "meta"
    meta_sections = "sections"
    parts = "parts"
    styles = "styles"
    chapters = "chapters"
    sections = "sections"
    subsections = "subsections"

class FileExtensions():
    xml = "xml"
    fodt = "fodt"
    txt = "txt"
    bak = "bak"

class FileNames():
    keywords = "keywords.txt"
    main_document = "main.fodt"
    master_styles_fn = "master-styles.xml"
    office_attr_fn = "office_attrs.txt"
    styles = "styles"
    styles_info_fn = "styles_info.txt"
    subsection = "section"
    subdocument = "section"

class KeywordStatus(enum.Enum):
    ORANGE = 0
    GREEN = 1

class MetaSections():
    names = [
        'office:meta',
        'office:settings',
        'office:scripts',
        'office:font-face-decls',
        'office:styles',
        'office:automatic-styles',
        'office:master-styles',
    ]

class TagEvent():
    NONE = 0
    START = 1
    END = 2

