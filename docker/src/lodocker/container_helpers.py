from lodocker.constants import Paths
from lodocker import helpers

def get_libreoffice_exec_name() -> str:
    """Get the executable name for LibreOffice in the development container."""
    return str(Paths.container_home / "libreoffice" / "instdir" / "program" / "soffice")

def get_image_name(dockerfile_dirname: str) -> str:
    image_name_prefix = helpers.get_tag_name_from_docker_dirname(dockerfile_dirname)
    image_names = helpers.get_docker_image_names()
    # Extract those image name that starts with image_name_prefix
    image_names = [name for name in image_names if name.startswith(image_name_prefix)]
    image_name = helpers.user_input(
        options=image_names, prompt="Please select a docker image", custom_value=True
    )
    return image_name
