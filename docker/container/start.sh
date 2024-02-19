#!/bin/bash

# This file is run when the Docker container is started "docker run" without additional arguments.
# We have wrapped the "docker run" in a script "start-container.sh" that takes care of
# mounting the shared directory and the fonts directory, and also sets up the X11 connection.
#
# This script "start.sh" starts the LibreOffice daemon and the Python Flask server in the
# Docker container that enables the host to communicate with the Docker container using a REST API.

# Further, we would like to get rid of the popup dialog when opening a file with links to other files.
#  The popup dialog has the message:
#
#  "The document main.fodt contains one or more links to external data.
#   Would you like to change the document, and update all links to get
#   the most recent data?", see:
#
# https://ask.libreoffice.org/t/avoid-popup-dialog-at-startup-would-you-like-to-update-all-links-to-get-the-most-recent-data/99189
#
# I first tried to pass "com.sun.star.document.UpdateDocMode.QUIET_UPDATE" to the loadComponentFromURL()
# method in the python script "docker-server.py", but that did not work.
# I have submitted a PR to fix this: https://gerrit.libreoffice.org/c/core/+/161628
#
# In the mean time, I found a workaround by modifying the user profile file
#  "registrymodifications.xcu". This file is located in the directory
#  "/home/docker-user/.config/libreoffice/4/user/" and needs to be modified
#  as shown in the script "update-libreoffice-config.sh".
#
# However, we cannot modify this file before LibreOffice has been started once
#  to initialize the user profile. Therefore we start LibreOffice, wait 5 seconds,
#  kill it, modify the file, and start it again. See below:

${LIBREOFFICE_EXE} --accept="socket,host=localhost,port=${LIBREOFFICE_PORT};urp;" --headless \
  --norestore --nofirststartwizard --nologo --nodefault --pidfile=/home/docker-user/lo_pid.txt &


echo "Waiting 5 seconds for LibreOffice to start and intialize..."
sleep 5

# Call a script that opens a blank document in LibreOffice Writer
python3 open-blank-document.py
echo "Waiting 5 seconds for LibreOffice to open a blank document..."
sleep 5
echo "Killing LibreOffice..."
kill $(cat /home/docker-user/lo_pid.txt)

# Modify the user profile to get rid of popup dialog when opening a file with
# links to other files
./update-libreoffice-config.sh

echo "Restarting LibreOffice..."
# Restart LibreOffice with the modified user profile
${LIBREOFFICE_EXE} --accept="socket,host=localhost,port=${LIBREOFFICE_PORT};urp;" \
  --norestore --nofirststartwizard --nologo --nodefault --pidfile=/home/docker-user/lo_pid.txt &

# Start the Flask server
exec python3 docker-server.py
