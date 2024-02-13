import logging

from pathlib import Path

import click
import colorama

from lodocker.colors import green_color
from lodocker.helpers import ClickHelpers, Helpers

@click.command()
@click.option(
    '--dir', 'dockerfile_dirname',
    callback=ClickHelpers.directory_callback,
    expose_value=True,
    is_eager=False,
    prompt=False,
    required=False,
    help='Directory name with Dockerfile inside the docker_files directory'
)
def build_docker_image(dockerfile_dirname: str):
    logging.basicConfig(level=logging.INFO)
    colorama.init(autoreset=True)
    tag_name = Helpers.get_tag_name_from_docker_dirname(dockerfile_dirname)
    if tag_name is None:
        logging.error("Aborting docker build.")
        return
    dockerfile = Path("docker_files") / dockerfile_dirname / "Dockerfile"
    command = ["docker", "build", "-f", str(dockerfile), "-t", tag_name, "."]
    command_str = " ".join(command)
    exit_code = Helpers.run_command(command)
    if exit_code == 0:
        logging.info(f"docker build for tag {tag_name} was successful.")
    else:
        logging.error(f"docker build for tag {tag_name} failed with exit code: {exit_code}.")
    print("NOTE: You can also run this \"docker build\" command manually: ")
    print(f"{green_color(command_str)}")

if __name__ == "__main__":
    build_docker_image()
