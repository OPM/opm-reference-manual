# Run LibreOffice from a docker container

The Python scripts in this folder allow you to run LibreOffice from a Docker
container. Currently, there is one Dockerfile with Ubuntu 22.04 and
LibreOffice version 7.5.9, and another one that allows you to build LibreOffice from
source (from a specified git tag and with or without debugging symbols).

The scripts need to be installed (with e.g. `poetry`) before they will be available,
see the section below for how to install the scripts. After installation, the following
script are available:

- `lodocker-build-image` : Builds the Docker image,
- `lodocker-run-container` : Runs LibreOffice from a Docker container with specified file,
- `lodocker-start-container` : Starts a container as a server. The host can communicate with
                               it using an API, see below.

The following scripts can be used to communicate with the container, in the case
the container is started as a Flask server with the above `lodocker-start-container` script:

- `lodocker-open-file`
- `lodocker-open-file-and-update`

are two scripts that can be used to run LibreOffice on a
Linux host, see sections below for details on Windows and macOS.

## Scripts

`Dockerfile`'s are located in the directory `docker_files`. Currently, there are two
Dockerfile directories, namely `ubuntu2204-lo7.5.9` and `ubuntu2310-dev`.
The first one can be used to build a Docker image with Ubuntu22.04 and LibreOffice version
7.5.9. The second, allow you to build LibreOffice from source from a specified git tag
and with or without debugging symbols.

### `lodocker-build-image`

This script builds a Docker image. You can supply the directory of the Dockerfile as an
optional argument to the script. So

```
$ lodocker-build-image --dir=ubuntu2204-lo7.5.9
```

will build the image for the Dockerfile located in directory `docker_files/ubuntu2204-lo7.5.9`.
If you do not specify a directory name, a menu of directory names will be presented, and you
can choose one from the menu.

NOTE: The actual tag name of the Docker image is not necessarily the same as the directory name.



### `lodocker-run-container`

This script runs LibreOffice from a Docker container. You should supply the file name you
want to open in LibreOffice as the first argument to the script. The file names are
relative to directory `../parts` (as seen from this directory, i.e. the directory containing
this `README.md` file). You can also supply the
directory of the Dockerfile you used to build the image (see `lodocker-build-image`) as an
optional argument to the script. So

```
$ lodocker-run-container main.fodt --dir=ubuntu2204-lo7.5.9
```

will open LibreOffice with `../parts/main.fodt` from the Docker container built from directory
`ubuntu2204-lo7.5.9`. If you do not specify a directory name, a menu of directory names will
be presented, and you can choose one from the menu.

### `lodocker-start-container`

Starts a container as a server and also starts LibreOffice as a daemon process
(a standalone background process that listens to messages over a socket) inside the container.
The host can then communicate
with LibreOffice through server (which is using a Python UNO bridge to communicate with LibreOffice)
using an API. The API currently only has two
end points "open-document" and "open-document-and-update", which will open a given document
and the latter will also update its indexes.

To simplify the use of these end points, you can use the Python scripts `lodocker-open-file <file.fodt>`
and `lodocker-open-file-and-update <file.fodt>`.

NOTE: When the server has started successfully, leave this terminal window open to view log messages
from the server.
To communicate with the server, open another terminal window and run e.g. `lodocker-open-file` from there.
To stop the server, press CTRL+C in the server's terminal window (this only works on Linux)

### `lodocker-open-file`

If you have started the docker container as a server with LibreOffice running as a background process,
see `lodocker-start-container`, you can run this script `lodocker-open-file` to communicate
to the server that you want to open a file. So for example:

```
$ lodocker-open-file main.fodt
```
Will open `main.fodt` in the LibreOffice that is running in the server.

### `lodocker-open-file-and-update`

Similar to `lodocker-open-file`, except that it also automatically updates the indexes
in the document. The updating of indexes currently has a bug, see
https://github.com/OPM/opm-reference-manual/pull/108#issuecomment-1928479617

## Platform specific comments

### Windows

On Windows, you will have to install Docker Desktop, see: https://docs.docker.com/desktop/install/windows-install/
and an X Server, for example VcXsrv or Xming.
Then, ensure that the PowerShell execution policy is set to `RemoteSigned` or `Unrestricted`, see: https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.security/set-executionpolicy?view=powershell-7.4,
such that you are allowed to run scripts from PowerShell.

Make sure that both Docker Desktop and the X server are running, and open a PowerShell terminal window.
You should now be able to install the Python scripts, build the Docker image, and run the LibreOffice Docker container.

### macOS

On macOS, you will have to install Docker Desktop, see: https://docs.docker.com/desktop/install/mac-install/
and the XQuartz X Server.

Make sure that both Docker Desktop and the X server are running, and open a terminal window.
You should now be able to install the Python scripts, build the Docker image, and run the LibreOffice Docker container.

## Installation of the python scripts
- Requires python3 >= 3.10
- Change to the current directory (`docker/lo-ubuntu2204`) before running any of the commands below

### Using poetry
For development it is recommended to use poetry:

- Install [poetry](https://python-poetry.org/docs/)
- Then run:
```
$ poetry install
$ poetry shell
```

### Installation into virtual environment
If you do not plan to change the code, you can do a regular installation into a VENV:

```
$ python -m venv .venv
$ source .venv/bin/activate
$ pip install .
```

- NOTE: On Windows (PowerShell) type `.\.venv\Scripts\Activate.ps1` to activate the VENV