from pathlib import Path
from lodocker import helpers

def test_git_root_exists(tmp_path: Path):
    # Create a dummy git repository in the tmp_path directory
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    # Create a folders and a file: "docker/.venv/lib/python3.12/site-packages/lodocker/run_container.py"
    docker_dir = tmp_path / "docker/.venv/lib/python3.12/site-packages/lodocker"
    docker_dir.mkdir(parents=True)
    run_container = docker_dir / "run_container.py"
    run_container.touch()
    # Create a parts directory
    parts_dir = tmp_path / "parts"
    parts_dir.mkdir()
    # Create a main.fodt file
    main_fodt = parts_dir / "main.fodt"
    main_fodt.touch()
    found_root = helpers.locate_git_root_from_path(run_container)
    assert found_root == tmp_path
