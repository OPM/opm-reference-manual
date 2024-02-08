import logging
import re
import requests
# import shutil
# import tempfile

from pathlib import Path

import click

from fodt.constants import ClickOptions

class FixIgnored:
    def __init__(self, maindir: str) -> None:
        self.maindir = maindir


    # Examples of phrases:
    # --------------------
    # APIVD: "This keyword is ignored by OPM Flow and has no effect on the simulation <text:span text:style-name="T5812">but is documented here for completeness.
    #
    def fix_file(self, file: Path, critical_keywords: set[str]) -> None:
        keyword = file.stem
        critical = keyword in critical_keywords
        # NOTE: Since the files are already backed up by git, we do not create a backup here
        # Take backup of the file to /tmp
        #tempfile_ = tempfile.mktemp()
        #shutil.copy(str(file), tempfile_)
        line_no = 0
        lines = []
        changed = False
        with open(file, "r") as f:
            # Read file line by line
            while line := f.readline():
                line_no += 1
                # NOTE: Use re.DOTALL to make "." match the trailing newline
                if match := re.match(r"""(\s*<text:p\s+.*?>)(.*?)(</text:p>.*$)""", line, re.DOTALL):
                    start, txt, end = match.groups()
                    # Remove span tags from txt
                    txt = re.sub(r"""<text:span .*?>(.*?)</text:span>""", r"\1", txt)
                    txt = re.sub(r"""<text:span>(.*?)</text:span>""", r"\1", txt)
                    if "is ignored by OPM Flow and has no effect on the simulation" in txt:
                        logging.info(f"Found ignored match in {file}:{line_no}.")
                        txt = self.replace_ignored(txt, critical)
                        line = start + txt + end
                        changed = True
                lines.append(line)
        if changed:
            logging.info(f"Writing changes to {file}.")
            with open(file, "w") as f:
                for line in lines:
                    f.write(line)

    def fix_files(self) -> None:
        logging.info(f"Fixing ignored keywords in {self.maindir}.")
        critical_keywords = self.get_critical_keywords()
        if critical_keywords is None:
            logging.error("Abort.")
            return
        # Directory containing the keyword files
        keyword_dir = Path(self.maindir) / "chapters" / "subsections"
        assert keyword_dir.is_dir()
        subdirs = keyword_dir.glob(f"*")
        for subdir in sorted(subdirs):
            if subdir.is_dir():
                self.fix_subdir(subdir, critical_keywords)

    def fix_subdir(self, subdir: Path, critical_keywords: set[str]) -> None:
        logging.info(f"Processing {subdir}.")
        files = subdir.glob("*.fodt")
        for file in sorted(files):
            self.fix_file(file, critical_keywords)

    def get_critical_keywords(self) -> set[str] | None:
        """Return a set of critical keywords. Download the file:
        https://raw.githubusercontent.com/OPM/opm-simulators/master/opm/simulators/utils/UnsupportedFlowKeywords.cpp
        and extract the critical keywords from it.
        """
        # Download the file
        url = "https://raw.githubusercontent.com/OPM/opm-simulators/master/opm/simulators/utils/UnsupportedFlowKeywords.cpp"
        response = requests.get(url)
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            lines = content.split("\n")
            critical_keywords = set()
            # The format of the lines to consider is:
            # "        {"ACTION", {true, std::nullopt}}," # ACTION is a critical keyword
            # "        {"ACTION", {false, std::nullopt}}," # ACTION is a non-critical keyword
            for line in lines:
                if match := re.match(r"""^\s+\{"(.*?)", \{(\w+),""", line):
                    keyword = match.group(1)
                    critical = match.group(2)
                    if critical == "true":
                        critical_keywords.add(keyword)
            logging.info(f"Found {len(critical_keywords)} critical keywords.")
            return critical_keywords
        else:
            logging.error(f"Failed to download {url}.")
        return None

    def replace_ignored(self, txt: str, critical: set[str]) -> str:
        if critical:
            replacement = ("This keyword is not supported by OPM Flow but would change "
                    "the results if supported so the simulation will be stopped.")
        else:
            replacement = ("This keyword is not supported by OPM Flow but has no effect "
                    "on the results so it will be ignored.")

        variants = ["This keyword is ignored by OPM Flow and has no effect on the simulation;",
                    ", it is ignored by OPM Flow and has no effect on the simulation but is documented here for completeness."]
        found_variant = False
        for variant in variants:
            if variant in txt:
                if variant[0:2] == ", ":
                    replacement = ". " + replacement
                elif variant[-1] == ";":
                    replacement = replacement[:-1] + ";"
                txt = txt.replace(variant, replacement)
                found_variant = True
                break
        if not found_variant:
            txt = replacement
        return txt

# USAGE:
#
#   fodt-fix-ignored-keywords
#
# DESCRIPTION:
#
#  Scan all keyword documents for certain phrases regarding ignored keywords. If found, change the
#  phrase to a new phrase. To determine the new phrase, the keyword is checked for criticality.
#
#  - Download file with information about critcal/non-critical keywords here:
#
#    https://raw.githubusercontent.com/OPM/opm-simulators/master/opm/simulators/utils/UnsupportedFlowKeywords.cpp
#
#  - Phrases to look for:
#    - "is ignored by OPM Flow and has no effect on the simulation"
#
#  - Replacement phrase for critical keywords:
#    "This keyword is not supported by OPM Flow but would change the results "
#       if supported so the simulation will be stopped."
#
#  - Replacement phrase for non-critical keywords:
#     "This keyword is not supported by OPM Flow but has no effect on the results so will be ignored."
#
@click.command()
@ClickOptions.maindir(required=False)
def fix_ignored(maindir: str
) -> None:
    """Remove bookmark refs from the master style section in all subdocuments."""
    logging.basicConfig(level=logging.INFO)
    FixIgnored(maindir).fix_files()

if __name__ == "__main__":
    fix_ignored()
