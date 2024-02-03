# This script is for PowerShell in Windows, see start-container.sh for the equivalent in Linux.
#
# This script will run a docker container with Ubuntu 22.04 and libreoffice as a server
# that the host can connect to and communicate with using a REST API.
#
# The version of libreoffice in the container is 7.5.9
#
#  USAGE: .\start-container.ps1
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
# To run the image on Windows in PowerShell:
# - first ensure that the Docker Desktop is running
# - Check that execution policy is set to RemoteSigned or Unrestricted
# - Ensure that the X server is running and accessible for Windows (e.g., VcXsrv, Xming)
#   (tested with VcXsrv)
#
# TODO: Tested with VcXsrv, but it is very slow.
#
param(
    [string]$filePath,
    [string]$ipAddressOverride
)
if (-not $ipAddressOverride) {
    $ipAddress = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {
        $_.IPAddress -notlike "169.254.*" -and $_.IPAddress -notlike "127.0.0.1" -and $_.InterfaceAlias -match "Wi-Fi|Ethernet"
    } | Select-Object -ExpandProperty IPAddress -First 1)
    if (-not $ipAddress) {
        Write-Host "No suitable IPv4 address found for the DISPLAY variable using automatic detection."
    } else {
        Write-Host "Automatically detected suitable IPv4 address: $ipAddress"
    }
} else {
    $ipAddress = $ipAddressOverride
    Write-Host "Using provided IP address: $ipAddressOverride"
}

if (-not $ipAddress) {
    Write-Error "Please supply an IP address as an argument."
    exit
}

$ENV:DISPLAY = $ipAddress + ":0.0"
Write-Host "Using DISPLAY: $ENV:DISPLAY"

# Set default values for LIBREOFFICE_PORT and FLASK_PORT if not already set
$ENV:LIBREOFFICE_PORT = if ($null -eq $ENV:LIBREOFFICE_PORT) { "2002" } else { $ENV:LIBREOFFICE_PORT }
$ENV:FLASK_PORT = if ($null -eq $ENV:FLASK_PORT) { "8080" } else { $ENV:FLASK_PORT }

# Define directories for shared content and fonts
$sharedDir = "parts"
$hostDirectory = Join-Path (Get-Location).Path "../../$sharedDir"
$dockerImage = "lo-ubuntu2204"
$dockerHome = "/home/docker-user"
$fontDir = Join-Path (Get-Location).Path "../../fonts"
$dockerFontDir = "/usr/local/share/fonts"

# Assuming X server is running and accessible for Windows (e.g., VcXsrv, Xming)
docker run --rm `
  -e DISPLAY=$ENV:DISPLAY `
  -p "${ENV:FLASK_PORT}:${ENV:FLASK_PORT}" `
  -e LIBREOFFICE_PORT="$ENV:LIBREOFFICE_PORT" `
  -e FLASK_PORT="$ENV:FLASK_PORT" `
  -v "${hostDirectory}:${dockerHome}/$sharedDir" `
  -v "${fontDir}:${dockerFontDir}:ro" `
  $dockerImage

