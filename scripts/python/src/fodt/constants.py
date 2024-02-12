import enum
import click

class AutomaticStyles():
    attr_names = {"text:style-name", "table:style-name", "draw:style-name", "style:name"}

class ClickOptions():
    filename = lambda func: click.option(
        '--filename',
        envvar='FODT_FILENAME',
        required=True,
        help='Name of the FODT file to extract from.'
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
                help='Directory to save generated files.'
            )(func)
        return decorator

class Directories():
    appendices = "appendices"
    backup = "backup"
    info = "info"
    keywords = "keywords"
    meta = "meta"
    meta_sections = "sections"
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

