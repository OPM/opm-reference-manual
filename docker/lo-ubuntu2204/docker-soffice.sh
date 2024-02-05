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
# NOTE:
#
#  See the script start-container.sh for more a more general/advanced solution. The
#  start-container.sh can automatically update the index of a libreoffice document and
#  also gets rid of the popup dialog
#
#    "The document contains one or more links to external data. Would you like to change the document,
#     and update all links to get the most recent data?"
#
#  See issue #67 : https://github.com/OPM/opm-reference-manual/issues/67 for more information.
#
#
# NOTES for macOS:
#
#  Make sure docker desktop is running.
#  The XQuartz server must be running before running this script.
#  The IP address of the XQuartz server is obtained using ipconfig.
#  The IP address is used to set the DISPLAY environment variable in the Docker container.
#  The XQuartz server must be configured to allow connections from network clients.
#

# Check if a file argument is provided
if [ $# -eq 0 ]; then
    echo "No file provided. Usage: ./docker-soffice.sh <file.fodt>"
    exit 1
fi

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


if [[ $(uname) == "Darwin" ]]; then
    # macOS
    # Get the IP address of the XQuartz server
    # Check if XQUARTZ_IP is set by the user, otherwise obtain it dynamically
    if [ -z "$XQUARTZ_IP" ]; then
        # Get the IP address of the XQuartz server using ipconfig
        XQUARTZ_IP=$(ipconfig getifaddr en0) # Change 'en0' to your active network interface
    fi
    DISPLAY_IP="$XQUARTZ_IP:0"
    docker run -v "${host_directory}:${docker_home}/$shared_dir" \
               -v "${font_dir}:${docker_font_dir}:ro" \
               -v "${HOME}/.Xauthority:/home/docker-user/.Xauthority:rw" \
               --rm \
               -e DISPLAY=$DISPLAY_IP \
               $docker_image \
               libreoffice "$docker_home/$shared_dir/$1"
else
    # Allow Docker Container to Access the Host's X Server
    # Temporarily allow connections from any client
    xhost +
    docker run -v "${host_directory}:${docker_home}/$shared_dir" \
               -v "${font_dir}:${docker_font_dir}:ro" \
               --rm \
               -e DISPLAY=$DISPLAY \
               -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
               $docker_image \
               libreoffice "$docker_home/$shared_dir/$1"
    # Revoke the X11 access on Linux
    xhost -
fi
