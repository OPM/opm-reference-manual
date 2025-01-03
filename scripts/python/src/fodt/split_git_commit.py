from datetime import datetime
import io
import logging
import os
import sys
import tempfile
import xml.sax
import xml.sax.handler
import xml.sax.xmlreader
import xml.sax.saxutils

from pathlib import Path

import click
from git import Repo

from fodt.extract_xml_tag import ExtractXmlTag
from fodt import xml_helpers

class ContentHandler(xml.sax.handler.ContentHandler):
    def __init__(self, old_body: str) -> None:
        self.body = old_body
        self.content = io.StringIO()
        self.in_body = False

    def get_content(self) -> str:
        return self.content.getvalue()

    def endElement(self, name: str):
        if name == 'office:body':
            self.in_body = False
        else:
            if not self.in_body:
                self.content.write(xml_helpers.endtag(name))

    def characters(self, content: str):
        if not self.in_body:
            self.content.write(xml.sax.saxutils.escape(content))

    def startDocument(self):
        self.content.write(xml_helpers.HEADER)

    def startElement(self, name: str, attrs: xml.sax.xmlreader.AttributesImpl):
        if name == 'office:body':
            self.in_body = True
            # NOTE: assume that the body is escaped content (xml.sax.saxutils.escape)
            self.content.write(self.body)
        else:
            if not self.in_body:
                self.content.write(xml_helpers.starttag(name, attrs))


class Splitter:
    def __init__(self, repo: Repo) -> None:
        self.repo = repo

    def check_for_uncommitted_changes(self) -> None:
        """Check if there are uncommitted changes in the working directory."""
        changed_files = [item.a_path for item in self.repo.index.diff(None)]
        if changed_files:
            print("Error: There are uncommitted changes in the working directory. "
                  "Please commit or stash them before running this script.")
            sys.exit(1)

    def commit_changes(self, file_path: str, content: str, commit_message: str) -> None:
        """Commit changes to a specified file with a custom message."""
        # Construct the absolute path to the file within the repository
        abs_file_path = os.path.join(self.repo.working_dir, file_path)
        # Write the content to the file at the correct location
        with open(abs_file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        # Add the file to the index and commit the changes
        self.repo.index.add([abs_file_path])
        self.repo.index.commit(commit_message)
        print(f"Changes committed with message: {commit_message}")

    def create_backup_branch(self) -> None:
        """Create a backup of the current branch."""
        current_branch = self.repo.active_branch.name
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        self.backup_branch_name = f"{current_branch}_backup_{timestamp}"
        self.repo.git.checkout('HEAD', b=self.backup_branch_name)
        print(f"Backup branch created: {self.backup_branch_name}")
        # Switch back to the original branch after creating the backup
        self.repo.git.checkout(current_branch)

    def delete_current_commit(self):
        """Reset the current branch to its parent."""
        # Reset to the parent commit (HEAD~1), keeping changes in the working directory
        self.repo.git.reset('--soft', 'HEAD~1')

    def extract_file_versions(self, fodt_file: str):
        """Extract the current and previous versions of the .fodt file."""
        # Path for the current version (working directory version)
        current_file_path = Path(self.repo.working_dir) / fodt_file

        # Create a temporary file to hold the previous version
        previous_file_fd, previous_file_path = tempfile.mkstemp()
        os.close(previous_file_fd)  # Close the file descriptor as we'll use the path

        # Use Git to get the file content from the parent of the current HEAD
        previous_content = self.repo.git.show(f'HEAD~1:{fodt_file}')

        # Write the previous content to the temporary file
        with open(previous_file_path, 'w', encoding='utf-8') as file:
            file.write(previous_content)

        return current_file_path, previous_file_path

    def extract_xml_tag_content(self, filename, tag_name) -> str:
        """Extract the content of a specified XML tag from a .fodt file."""
        handler = ExtractXmlTag(filename, tag_name, enable_indent=False)
        return handler.extract()

    def get_content_change(self, current_file: str) -> str:
        """Read the content of the current_file and return it as a string"""
        with open(current_file, 'r', encoding='utf-8') as file:
            return file.read()

    def get_last_commit_changed_files(self) -> list[str]:
        """Retrieve files changed in the last commit."""
        last_commit = list(self.repo.iter_commits('HEAD', max_count=1))[0]
        return list(last_commit.stats.files.keys())

    def get_style_change(self, current_file: str, previous_file: str) -> str:
        """Extract style changes between two versions of a .fodt file.
        Parse a .fodt file and return a new version with style changes only."""
        old_body = self.extract_xml_tag_content(previous_file, 'office:body')
        # The XML parser stops at the end of the last xml tag in the file,
        #  but there might be trailing whitespace after the last tag.
        white_space_at_end = self.get_trailing_whitespace(previous_file)
        # Parse the current file and extract the body content
        parser = xml.sax.make_parser()
        handler = ContentHandler(old_body)
        parser.setContentHandler(handler)
        parser.parse(current_file)
        return handler.get_content() + white_space_at_end

    def get_trailing_whitespace(self, filename: str) -> str:
        """Extract trailing whitespace from a file."""
        with open(filename, 'r') as file:
            content = file.read()
        # Find the index of the last non-whitespace character
        non_whitespace_index = len(content.rstrip()) - 1
        # Extract the trailing whitespace
        trailing_whitespace = content[non_whitespace_index + 1:]
        return trailing_whitespace

    def save_commit_message(self) -> None:
        """Save the commit message of the current commit."""
        self.saved_commit_message = self.repo.head.commit.message

    def split_commit(self) -> None:
        if self.repo.is_dirty(untracked_files=True):
            self.check_for_uncommitted_changes()
        last_commit_files = self.get_last_commit_changed_files()
        fodt_file = self.validate_and_get_fodt_file(last_commit_files)
        self.create_backup_branch()
        self.save_commit_message()
        self.split_commit_two_parts(fodt_file)
        self.verify_no_difference_with_backup()

    def split_commit_two_parts(self, fodt_file: str) -> None:
        """Split the commit into two parts for style and content changes."""
        # Extract current and previous versions of the file
        current_file, previous_file = self.extract_file_versions(fodt_file)

        # Identify style and content changes
        style_change_content = self.get_style_change(current_file, previous_file)
        content_change_content = self.get_content_change(current_file)
        self.delete_current_commit()

        # Create commits for style and content changes
        self.commit_changes(
            fodt_file,
            style_change_content,
            f"{self.saved_commit_message} - Style changes"
        )
        self.commit_changes(
            fodt_file,
            content_change_content,
            f"{self.saved_commit_message} - Content changes"
        )

    def validate_and_get_fodt_file(self, last_commit_files: list[str]) -> str:
        """Validate the last commit and return the .fodt filename."""
        if len(last_commit_files) == 1 and last_commit_files[0].endswith('.fodt'):
            return last_commit_files[0]
        else:
            print("Error: No .fodt file specified and last commit does not "
                  "contain exactly one .fodt file.")
            sys.exit(1)

    def verify_no_difference_with_backup(self) -> None:
        """Verify that there is no difference between the current branch and the backup branch."""
        diff = self.repo.git.diff(self.backup_branch_name, 'HEAD')
        if diff:
            logging.error(
                "Error: There is a difference between the backup branch and the current state."
            )
        else:
            logging.info(
                "Verification successful: No difference between the backup branch and "
                "the current state."
            )

# fodt-split-commit
# -----------------
# SHELL USAGE
# -----------
#
# fodt-split-commit
#
# DESCRIPTION
# -----------
# Split the last committed file in a Git repository into separate commits for style and
#  content changes. To simplify complexities with stashing of files, the last commit
#  should contain changes to a single .fodt file. If the last commit contains
#  changes to multiple files an error will be raised. The user is then required
#  to manually separate the changes into separate commits before running this script.
#  If the last commit contains changes to a file that is not a .fodt file, an error
#  will be raised.
#
#  The commit message of the last commit will be used as a prefix for the commit
#  messages of the two new commits (that replaces the current commit) with style
#  and content changes.
#
#  The script will create a backup branch before replacing the current commit.
#  After the replacement, the script will verify that there is no difference
#  between the backup branch and the current state.
#  The name of the backup branch will be the name of the current branch with a
#  timestamp appended.
#
@click.command()
def split_commit():
    logging.basicConfig(level=logging.INFO)
    repo_path = '../..'
    repo = Repo(repo_path)
    Splitter(repo).split_commit()

if __name__ == "__main__":
    split_commit()
