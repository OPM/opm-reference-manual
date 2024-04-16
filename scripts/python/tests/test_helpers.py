import os
from pathlib import Path

import pytest
from fodt.constants import Directories, FileNames
from fodt.helpers import Helpers

class TestLocateMainDirAndFilename:
    def test_locate_with_absolute_path_exists(self, tmp_path: Path) -> None:
        """Test locating maindir and filename when the maindir is given as an absolute path."""
        maindir = tmp_path / Directories.parts
        maindir.mkdir()
        mainfile = maindir / FileNames.main_document
        mainfile.touch()
        filename_dir = maindir / Directories.chapters
        filename_dir.mkdir()
        filename = filename_dir / "1.fodt"
        filename.touch()
        result_maindir, result_filename = Helpers.locate_maindir_and_filename(
            str(maindir), str(filename)
        )
        assert result_maindir == maindir
        assert result_filename == filename

    def test_locate_with_absolute_path_exists_no_main(self, tmp_path: Path) -> None:
        """Test locating maindir and filename when the maindir is given as an absolute path
        and the main file does not exist. This should raise an error."""
        maindir = tmp_path / Directories.parts
        maindir.mkdir()
        mainfile = maindir / FileNames.main_document
        # mainfile.touch()  # Do not create the main file
        filename_dir = maindir / Directories.chapters
        filename_dir.mkdir()
        filename = filename_dir / "1.fodt"
        filename.touch()
        with pytest.raises(FileNotFoundError) as excinfo:
            Helpers.locate_maindir_and_filename(
                str(maindir), str(filename)
            )
        assert (f"Could not find '{FileNames.main_document}' in a directory "
                f"called '{Directories.parts}'" in str(excinfo.value))

    def test_locate_with_relative_path_in_maindir_exists(self, tmp_path: Path) -> None:
        """Test locating maindir and filename when the maindir is absolute and the
        filename is a relative path."""
        maindir = tmp_path / Directories.parts
        maindir.mkdir()
        mainfile = maindir / FileNames.main_document
        mainfile.touch()  # Ensure the main document exists
        # Change directory to maindir
        os.chdir(str(maindir))
        filename_dir = Path(Directories.appendices)
        filename_dir.mkdir()
        filename = "A.fodt"
        filename_path = filename_dir / filename
        filename_path.touch()  # Create the file within maindir
        filename_abs_path = maindir / filename_path
        result_maindir, result_filename = Helpers.locate_maindir_and_filename(
            str(maindir), str(filename_path)
        )
        assert result_maindir == maindir
        assert result_filename == filename_abs_path

    def test_locate_with_relative_path_not_in_maindir_but_in_cwd(
            self, tmp_path: Path
    ):
        """Test locating maindir and filename when the maindir is absolute and the
        filename is a relative path. The filename is not found in the maindir but
        is found in the current working directory."""
        cwd = tmp_path / "cwd"
        cwd.mkdir()
        os.chdir(str(cwd))
        filename = "1.fodt"
        filename_path = cwd / filename
        filename_path.touch()  # Create the file in CWD
        maindir = tmp_path  # Some dummy path that is not the maindir
        with pytest.raises(FileNotFoundError) as excinfo:
            Helpers.locate_maindir_and_filename(
                str(maindir), str(filename_path)
            )
        assert excinfo.match(
            f"Could not find '{FileNames.main_document}' in a directory "
            f"called '{Directories.parts}' by searching the parent "
            f"directories of filename."
        )

    def test_locate_with_absolute_path_not_exists(self, tmp_path: Path):
        """Test locating maindir and filename when the maindir is absolute and the
        filename is a relative path. The filename is not found in the maindir and
        is not found in the current working directory. This should raise an error."""
        maindir = tmp_path / Directories.parts
        maindir.mkdir()
        filename = tmp_path / "nonexistent.fodt"
        # Do not create the file, simulating a non-existent file scenario

        with pytest.raises(AssertionError):
            Helpers.locate_maindir_and_filename(
                str(maindir), str(filename)
            )

class TestLocateMainDirFromCwd:
    def test_locate_exists_in_cwd(self, tmp_path: Path):
        """Test locating maindir from the current working directory when the maindir
        exists in the current working directory."""
        maindir = tmp_path / Directories.parts
        maindir.mkdir()
        mainfile = maindir / FileNames.main_document
        mainfile.touch()
        os.chdir(str(tmp_path))
        result = Helpers.locate_maindir_from_current_dir()
        assert result == maindir

    def test_locate_exists_as_parent(self, tmp_path: Path):
        """Test locating maindir from the current working directory when the maindir
        is the parent of the current working directory."""
        maindir = tmp_path / Directories.parts
        maindir.mkdir()
        mainfile = maindir / FileNames.main_document
        mainfile.touch()
        os.chdir(str(maindir))
        result = Helpers.locate_maindir_from_current_dir()
        assert result == maindir

    def test_locate_exists_as_sibling_of_parent(self, tmp_path: Path):
        """Test locating maindir from the current working directory when the maindir
        is a sibling of the parent of the current working directory."""
        maindir = tmp_path / Directories.parts
        maindir.mkdir()
        mainfile = maindir / FileNames.main_document
        mainfile.touch()
        os.chdir(str(tmp_path))
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        os.chdir(str(subdir))
        result = Helpers.locate_maindir_from_current_dir()
        assert result == maindir
