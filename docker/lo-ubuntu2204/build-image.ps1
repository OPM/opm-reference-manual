# This script is for PowerShell on Windows, see build-image.sh for the equivalent
# in Linux and macOS.
#
# To build the image on Windows in PowerShell, first ensure that the Docker Desktop is running
# and check that execution policy is set to RemoteSigned or Unrestricted

docker build -t lo-ubuntu2204 .