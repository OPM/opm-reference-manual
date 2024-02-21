import pytest
import shutil
import tempfile
from git import Repo
from pathlib import Path

from fodt.split_git_commit import Splitter

# NOTE: It is best to manually initialize the git repository in the temporary directory
#   and then copy the contents of the data/git_repo directory to the temporary directory.
#   Otherwise, the git will think it is a submodule and will not work as expected.
#   The same for GitHub Actions.
@pytest.fixture
def temp_git_repo(tmp_path):
    # Initialize a new git repository in the temporary directory
    repo_dir = tmp_path / "git_repo"
    repo_dir.mkdir()
    repo = Repo.init(repo_dir)
    # Setup first version of the file
    file_path = repo_dir / "COLUMNS.fodt"
    first_version_path = Path(__file__).parent / "data/git_repo/COLUMNS_1.fodt"
    shutil.copy(first_version_path, file_path)
    repo.index.add([str(file_path)])
    repo.index.commit("1st version")
    # Setup second version of the file
    second_version_path = Path(__file__).parent / "data/git_repo/COLUMNS_2.fodt"
    shutil.copy(second_version_path, file_path)
    repo.index.add([str(file_path)])
    repo.index.commit("2nd version")
    return repo

@pytest.fixture
def splitter(temp_git_repo: Repo):
    return Splitter(temp_git_repo)

@pytest.fixture
def create_temp_file_with_content(tmp_path: Path):
    def _create_temp_file_with_content(content: str) -> str:
        file_path = tmp_path / "testfile.fodt"
        file_path.write_text(content, encoding='utf-8')
        return str(file_path)
    return _create_temp_file_with_content
