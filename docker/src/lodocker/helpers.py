import logging
import subprocess

from pathlib import Path

from lodocker.constants import Directories, FileNames
from lodocker import container_helpers as dev_container

def get_libreoffice_exec_name(dockerfile_dirname: str) -> str:
    """Get the executable name for LibreOffice."""
    if is_dev_container(dockerfile_dirname):
        exec_name = dev_container.get_libreoffice_exec_name()
    else:
        exec_name = "libreoffice"
    return exec_name

def get_image_name(dockerfile_dirname: str) -> str:
    """Get the image name for the Docker container."""
    if is_dev_container(dockerfile_dirname):
        image_name = dev_container.get_image_name(dockerfile_dirname)
    else:
        image_name = get_tag_name_from_docker_dirname(dockerfile_dirname)
    return image_name

def get_libreoffice_userdir(dockerfile_dirname: str) -> str:
    """Get the user directory for LibreOffice. This is relative to
    the home directory of the user in the Docker container."""
    if is_dev_container(dockerfile_dirname):
        return str(Path("libreoffice") / "instdir")
    else:
        return str(Path(".config") / "libreoffice" / "4")

def get_tag_name_from_docker_dirname(dockerfile_dirname: str) -> str | None:
    """Get the tag name for a docker image from the directory name of the Dockerfile.
    :param dockerfile_dirname: The directory name of the Dockerfile.
    :return: The tag name for the docker image.
    If there exists a file named "tag_name.txt" in the directory, use the contents of
    that file as the tag name. Otherwise, display an error message and return.
    """
    dockerfile_dirname = Path("docker_files") / dockerfile_dirname
    # Check that the Dockerfile exists
    if not dockerfile_dirname.exists():
        logging.error(f"Dockerfile directory {dockerfile_dirname} does not exist.")
        return None
    tag_name_file = dockerfile_dirname / "tag_name.txt"
    if tag_name_file.exists():
        return tag_name_file.read_text().strip()
    else:
        logging.error(f"Cannot determine docker image tag name: File {tag_name_file} does not exist.")
        return None

def is_dev_container(dockerfile_dirname: str) -> bool:
    """Check if the Dockerfile is for a development container."""
    return dockerfile_dirname == "ubuntu2310-dev"

def locate_git_root() -> Path:
    """Locate the root directory of a git repository. Note that this may fail in the
    unlikely case that the user has installed the project globally outside the git
    repository and the current working directory is not within the repository.
    """
    root = None
    try:
        root = locate_git_root_from_path(Path(__file__))
    except FileNotFoundError:
        pass
    if root is None:
        root = locate_git_root_from_path(Path.cwd())
    return root

def locate_git_root_from_path(path: Path) -> Path:
    """Locate the root directory of a git repository from a file within the repository.
    :param file: A file within the git repository.
    :return: The root directory of the git repository.
    """
    path = path.resolve()
    if path.is_file():
        path = path.parent
    assert path.is_absolute(), "File path must be absolute."
    assert path.is_dir(), "File path must be a file."
    cwd = path
    while True:
        # Check if we have reached the root directory
        #  filename.parent == filename is True if filename is the root directory
        if cwd.parent == cwd:
            raise FileNotFoundError(f"Could not derive git root from '{path}'.")
        # Check if the current directory is a git repository and that there is a
        #  directory named "parts" with a main document file therein
        if (cwd / ".git").exists() and (cwd / ".git").is_dir():
            if (cwd / Directories.parts).exists():
                if (cwd / Directories.parts / FileNames.main_document).exists():
                    return cwd
        cwd = cwd.parent
    # This should never be reached
    return Path("")

def run_command(command: str | list) -> int:
    # Determine if command should be executed within a shell
    shell = isinstance(command, str)
    # Execute the command
    result = subprocess.run(command,  shell=shell)
    exit_code = result.returncode
    return exit_code

def user_input(
    prompt: str,
    default: str | None = None,
    options: list | None = None,
    custom_value: bool = False
):
   # Validate default value against options if options are provided and default is not None
    if options is not None and default is not None:
        if not custom_value and (default not in options):
            raise ValueError("Default value must be one of the options.")

    if options is None or len(options) == 0:
        if not custom_value:  # Check for disallowed state
            raise ValueError("custom_value must be True when no options are provided.")
        options = None  # Treat empty list the same as None

    if options is None:
        # Simplify the prompt if no options are provided
        full_prompt = f"{prompt} (default is {default}): " if default is not None else f"{prompt}: "
    else:
        # Display the initial prompt and options
        print(prompt)
        for i, option in enumerate(options, start=1):
            print(f"{i}. {option}")
        if custom_value:
            print(f"{len(options) + 1}. or enter a custom value")
        full_prompt = f"Select an option (default is {default}): " if default is not None else "Select an option: "

    while True:
        user_choice = input(full_prompt).strip()

        if not user_choice and default is not None:
            return default

        if options is not None:
            if user_choice.isdigit():
                user_choice = int(user_choice)
                if 1 <= user_choice <= len(options):
                    return options[user_choice - 1]
                elif custom_value and user_choice == len(options) + 1:
                    return input("Enter your custom value: ").strip()
                else:
                    print("Invalid option, please try again.")
            else:
                print("Invalid input, please try again.")
        else:
            # Directly return user choice if options is None and input is not empty,
            #  or return default if it's not None
            return user_choice if user_choice else default

def get_docker_image_names() -> list[str]:
    """Get a list of docker image names from "docker images"."""
    docker_images = subprocess.run(
        ["docker", "images", "--format", "{{.Repository}}"],
         capture_output=True, text=True
    )
    return docker_images.stdout.splitlines()
