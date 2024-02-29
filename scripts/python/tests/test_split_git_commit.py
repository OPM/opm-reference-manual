from pathlib import Path
from typing import Callable

from git import Repo
# from pytest_mock.plugin import MockerFixture

from fodt.split_git_commit import Splitter

def test_repo_initialization(temp_git_repo: Repo) -> None:
    assert temp_git_repo is not None
    assert len(list(temp_git_repo.iter_commits())) == 2  # Assuming there are 2 commits
    assert 'COLUMNS.fodt' in [
        Path(file).name for file in temp_git_repo.git.ls_files().split('\n')
    ]

def test_split_commit_two_parts(splitter: Splitter, temp_git_repo: Repo) -> None:
    splitter.split_commit()
    # After splitting, expect 3 commits: 2 for the split and 1 for the backup
    assert len(list(temp_git_repo.iter_commits())) == 3
    # Verify content changes in the last two commits
    last_commit_msg = temp_git_repo.head.commit.message
    assert "Content changes" in last_commit_msg
    # Verify style changes in the commit before the last
    previous_commit_msg = temp_git_repo.head.commit.parents[0].message
    assert "Style changes" in previous_commit_msg


def test_backup_branch_creation(splitter: Splitter, temp_git_repo: Repo) -> None:
    splitter.split_commit()  # Run the split process
    backup_branch_name = splitter.backup_branch_name
    assert backup_branch_name in temp_git_repo.git.branch().split()


def test_get_trailing_whitespace_no_trailing_space(
    create_temp_file_with_content: Callable[[str], str],
    splitter: Splitter,
) -> None:
    # Case: File without trailing whitespace
    content = "This is a test."
    file_path = create_temp_file_with_content(content)
    assert splitter.get_trailing_whitespace(file_path) == ""

def test_get_trailing_whitespace_with_newline(
    create_temp_file_with_content: Callable[[str], str],
    splitter, tmp_path
) -> None:
    # Case: File with a newline as trailing whitespace
    content = "This is a test.\n"
    file_path = create_temp_file_with_content(content)
    assert splitter.get_trailing_whitespace(file_path) == "\n"

def test_get_trailing_whitespace_with_spaces_and_newlines(
    create_temp_file_with_content: Callable[[str], str],
    splitter: Splitter
) -> None:
    # Case: File with spaces and newlines as trailing whitespace
    content = "This is a test.   \n\n"
    file_path = create_temp_file_with_content(content)
    assert splitter.get_trailing_whitespace(file_path) == "   \n\n"