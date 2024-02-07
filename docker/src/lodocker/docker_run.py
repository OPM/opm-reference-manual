import logging

import click
import colorama

from lodocker.helpers import ClickHelpers, Helpers
from lodocker.run_container import RunContainer


@click.command()
@click.argument("filename")
@click.option(
    '--dir', 'dockerfile_dirname',
    callback=ClickHelpers.directory_callback,
    expose_value=True,
    is_eager=False,
    prompt=False,
    required=False,
    help='Directory name with Dockerfile inside the docker_files directory'
)
def run_container(filename: str, dockerfile_dirname: str):
    """Run LibreOffice with the given FILENAME from a Docker container."""
    logging.basicConfig(level=logging.INFO)
    colorama.init(autoreset=True)
    image_name = Helpers.get_tag_name_from_docker_dirname(dockerfile_dirname)
    if image_name is None:
        logging.error("Aborting docker build.")
        return
    RunContainer().run_container(filename, image_name)

if __name__ == "__main__":
    run_container()
