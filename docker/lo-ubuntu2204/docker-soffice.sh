#! /bin/bash

# This script will run libreoffice 7.5.9 from a Docker container with Ubuntu 22.04
#
#  USAGE: ./docker-soffice.sh <file.fodt>
#
#  Here, <file.fodt> is the file to be opened in the Docker container.
#  The file.fodt file must be in the directory "parts" in the root of the repository.
#  The file will be opened in the Docker container and the container will
#  be removed when the file is closed.
#
#
#  EXAMPLES:
#
#  ./docker-soffice.sh main.fodt          # opens main.fodt in the Docker container
#  ./docker-soffice.sh appendices/A.fodt  # opens appendices/A.fodt in the Docker container
#
#
# Assume this script is run from the directory containing the Dockerfile
#  this means that the root of the repository is two levels up
shared_dir="parts"
host_directory="$PWD/../../$shared_dir"
docker_image="lo-ubuntu2204"
# The home directory of the user in the Docker container
docker_home="/home/docker-user"
# Directory where fonts are stored in the repository
font_dir="$PWD/../../fonts"
# Directory inside the Docker container where fonts will be stored
docker_font_dir="/usr/local/share/fonts"

# Check if a file argument is provided
if [ $# -eq 0 ]; then
    echo "No file provided. Usage: ./docker-soffice.sh <file.fodt>"
    exit 1
fi

# Allow Docker Container to Access the Host's X Server
# Temporarily allow connections from any client
xhost +
# Run soffice in the Docker container
docker run -v "${host_directory}:${docker_home}/$shared_dir" \
           -v "${font_dir}:${docker_font_dir}:ro" \
           --rm \
           -e DISPLAY=$DISPLAY \
           -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
           $docker_image \
           libreoffice "$docker_home/$shared_dir/$1"
# Revoke the X11 access
xhost -
