# PowerShell Script to Run LibreOffice 7.5.9 from a Docker Container with Ubuntu 22.04
# To run the image on Windows in PowerShell:
# - first ensure that the Docker Desktop is running
# - Check that execution policy is set to RemoteSigned or Unrestricted
# - Ensure that the X server is running and accessible for Windows (e.g., VcXsrv, Xming)
#   (tested with VcXsrv)

param(
    [string]$filePath
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

# Use explicit concatenation to set the DISPLAY variable
$ENV:DISPLAY = $ipAddress + ":0.0"
Write-Host "Using DISPLAY: $ENV:DISPLAY"


# Check if a file argument is provided
if (-not $filePath) {
    Write-Host "No file provided. Usage: .\docker-soffice.ps1 <file.fodt>"
    exit
}

# Assume this script is run from the directory containing the Dockerfile
# this means that the root of the repository is two levels up
$sharedDir = "parts"
$hostDirectory = Join-Path (Get-Location).Path "../../$sharedDir"
$dockerImage = "lo-ubuntu2204"
# The home directory of the user in the Docker container
$dockerHome = "/home/docker-user"
# Directory where fonts are stored in the repository
$fontDir = Join-Path (Get-Location).Path "../../fonts"
# Directory inside the Docker container where fonts will be stored
$dockerFontDir = "/usr/local/share/fonts"

# Run soffice in the Docker container
docker run -v "${hostDirectory}:${dockerHome}/$sharedDir" `
           -v "${fontDir}:${dockerFontDir}:ro" `
           --rm `
           -e DISPLAY=$ENV:DISPLAY `
           $dockerImage `
           libreoffice "$dockerHome/$sharedDir/$filePath"

