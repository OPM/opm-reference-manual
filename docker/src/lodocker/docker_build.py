import logging

from pathlib import Path

import click
import colorama

from lodocker.colors import green_color
from lodocker import helpers, click_helpers

def get_dev_build_command(dockerfile_dirname: str):
    build_type = helpers.user_input(
        options=["debug", "release"],
        prompt="Please select a build type",
        default="debug",
    )
    git_tag_name = helpers.user_input(
        prompt="Please select a git tag name",
        default="libreoffice-7.6.5.1",
        custom_value=True,
    )
    tag_name = helpers.get_tag_name_from_docker_dirname(dockerfile_dirname)
    if tag_name is None:
        logging.error("Aborting docker build.")
        return
    docker_tag_name = f"{tag_name}-{git_tag_name}_{build_type}"
    logging.info(f"Building docker image: {docker_tag_name}")
    dockerfile = Path("docker_files") / dockerfile_dirname / "Dockerfile"
    command = ["docker", "build", "-f", str(dockerfile),
               "--build-arg", f"BUILD_TYPE={build_type}",
               "--build-arg", f"GIT_TAG={git_tag_name}",
               "--network=host", "-t", docker_tag_name, "."]
    return command, tag_name

@click.command()
@click.option(
    '--dir', 'dockerfile_dirname',
    callback=click_helpers.directory_callback,
    expose_value=True,
    is_eager=False,
    prompt=False,
    required=False,
    help='Directory name with Dockerfile inside the docker_files directory'
)
def build_docker_image(dockerfile_dirname: str):
    logging.basicConfig(level=logging.INFO)
    colorama.init(autoreset=True)
    if helpers.is_dev_container(dockerfile_dirname):
        command, tag_name = get_dev_build_command(dockerfile_dirname)
    else:
        tag_name = helpers.get_tag_name_from_docker_dirname(dockerfile_dirname)
        if tag_name is None:
            logging.error("Aborting docker build.")
            return
        dockerfile = Path("docker_files") / dockerfile_dirname / "Dockerfile"
        command = ["docker", "build", "-f", str(dockerfile), "-t", tag_name, "."]
    command_str = " ".join(command)
    exit_code = helpers.run_command(command)
    if exit_code == 0:
        logging.info(f"docker build for tag {tag_name} was successful.")
    else:
        logging.error(f"docker build for tag {tag_name} failed with exit code: {exit_code}.")
    print("NOTE: You can also run this \"docker build\" command manually: ")
    print(f"{green_color(command_str)}")

if __name__ == "__main__":
    build_docker_image()
