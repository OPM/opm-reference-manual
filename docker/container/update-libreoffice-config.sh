#!/bin/bash

# This file is needed to avoid the popup dialog with message:
#  "The document main.fodt contains one or more links to external data.
#   Would you like to change the document, and update all links to get
#   the most recent data?", see:
#
# https://ask.libreoffice.org/t/avoid-popup-dialog-at-startup-would-you-like-to-update-all-links-to-get-the-most-recent-data/99189
#

CONFIG_FILE="/home/docker-user/${LIBREOFFICE_USERDIR}/user/registrymodifications.xcu"
TEMP_FILE="/home/docker-user/${LIBREOFFICE_USERDIR}/user/temp_registrymodifications.xcu"

# Append the SecureURL item
append_secure_url() {
    echo '<item oor:path="/org.openoffice.Office.Common/Security/Scripting"><prop oor:name="SecureURL" oor:op="fuse"><value><it>$(home)/parts</it></value></prop></item>' >> "$TEMP_FILE"
}

# Append the Update LinkMode item
append_update_link_mode() {
    echo '<item oor:path="/org.openoffice.Office.Writer/Content/Update"><prop oor:name="Link" oor:op="fuse"><value>2</value></prop></item>' >> "$TEMP_FILE"
}

# Copy original content excluding the last line (</oor:items>)
head -n -1 "$CONFIG_FILE" > "$TEMP_FILE"

# Append new configuration items
append_secure_url
append_update_link_mode

# Append the final closing tag
echo '</oor:items>' >> "$TEMP_FILE"

# Replace the original file with the modified one
mv "$TEMP_FILE" "$CONFIG_FILE"

# Display a message
echo "Modified registrymodifications.xcu successfully"
