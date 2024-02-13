import logging
import subprocess

from pathlib import Path
from typing import Optional, Any

import click

class ClickHelpers:
    @staticmethod
    def get_directories(path: str) -> list[str]:
        """Get a list of subdirectory names in the given directory."""
        path = Path(path)
        return [dir.name for dir in path.iterdir() if dir.is_dir()]

    @staticmethod
    def directory_callback(ctx: click.Context, param: click.Parameter, value: Optional[str]) -> Any:
        if value is None:
            # Dynamically read the directories and prompt the user to choose
            choices = ClickHelpers.get_directories('docker_files')
            if not choices:
                raise click.UsageError('No directories found in docker_files.')

            choice_dict = dict(enumerate(choices, start=1))
            click.echo("Select a Dockerfile:")
            for idx, choice in choice_dict.items():
                click.echo(f'{idx}. {choice}')
            choice = click.prompt('Please enter an integer', type=click.IntRange(1, len(choices)))
            return choice_dict[choice]
        return value



class Helpers:
    @staticmethod
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

    @staticmethod
    def run_command(command: str | list) -> int:
        # Determine if command should be executed within a shell
        shell = isinstance(command, str)
        # Execute the command
        result = subprocess.run(command,  shell=shell)
        exit_code = result.returncode
        return exit_code
