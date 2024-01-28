# Run LibreOffice from Ubuntu 22.04 docker container

The scripts in this folder allows you to run LibreOffice version 7.5.9 inside a docker
container. Currently, there are two scripts that can be used to run LibreOffice:

- `docker-soffic.sh` : This script runs LibreOffice the same way that you would use
   outside the container. So running `./docker-soffice.sh main.fodt` will open the
main document.
- `start-container.sh` : This script will run LibreOffice as daemon (a standalone background process that
   listens to messages over a socket) inside the docker container. The host can then communicate
   with this daemon using a Python UNO bridge script that is running inside the docker container.
   The communication between the host machine and docker container is done using a rest API against a
   flask web server running inside the docker container. The API currently only has a single
   end point "open-document" which will open a given FODT document and also update its indexes.

   To simplify the use of this end point, you can use the Python script `lodocker-open-file <file.fodt>`.
   See information about installing the Python script below.

## Installation of the python scripts
- Requires python3 >= 3.10

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
