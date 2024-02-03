#! /bin/bash

# This script will run a docker container with Ubuntu 22.04 and libreoffice as a server
# that the host can connect to and communicate with using a REST API.
#
# The version of libreoffice in the container is 7.5.9
#
#  USAGE: ./start-container.sh
#
# After starting the docker container server the following API is available
# to communicate with the server:
#
#  curl -X POST http://localhost:8080/open-document -H "Content-Type: application/json" \
#                                           -d '{"path":"main.fodt"}'
#
# Or use the python script "lodocker-open-file" for example:
#
#
#  lodocker-open-file main.fodt          # opens main.fodt in the Docker container
#  lodocker-open-file appendices/A.fodt  # opens appendices/A.fodt in the Docker container
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
# Default to 2002 if not set
LIBREOFFICE_PORT=${LIBREOFFICE_PORT:-2002}
# Default to 8080 if not set
FLASK_PORT=${FLASK_PORT:-8080}

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

# Check the operating system
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
           -p "$FLASK_PORT":"$FLASK_PORT" \
           -e DISPLAY=$DISPLAY_IP \
           -e LIBREOFFICE_PORT="$LIBREOFFICE_PORT" \
           -e FLASK_PORT="$FLASK_PORT" \
           $docker_image
else
    # Linux
    # Allow Docker Container to Access the Host's X Server
    # Temporarily allow connections from any client
    xhost +
    # Run soffice in the Docker container
    docker run -v "${host_directory}:${docker_home}/$shared_dir" \
               -v "${font_dir}:${docker_font_dir}:ro" \
               --rm \
               -p "$FLASK_PORT":"$FLASK_PORT" \
               -e DISPLAY="$DISPLAY" \
               -e LIBREOFFICE_PORT="$LIBREOFFICE_PORT" \
               -e FLASK_PORT="$FLASK_PORT" \
               -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
               $docker_image
    # Revoke the X11 access on Linux
    xhost -
fi
