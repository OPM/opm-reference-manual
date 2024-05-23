# Removes lines in a range [start, end] from a file
# Range is inclusive
# Currently only intended for use with debbugging
# First create a backup of the file of the file to remove lines from

import logging
import shutil
import tempfile

import click

@click.command()
@click.option('--start', type=int, required=True, help='Start line')
@click.option('--end', type=int, required=True, help='End line')
@click.option('--filename', type=str, required=True, help='Name of the file to remove lines from.')
def remove_lines(start: int, end: int, filename: str) -> None:
    """Remove lines in a range [start, end] from a file. Range is inclusive.
    First creates a backup of the file."""
    logging.basicConfig(level=logging.INFO)
    tempfilename = tempfile.mktemp()
    shutil.copy(filename, tempfilename)
    logging.info(f"Created backup of {filename} in {tempfilename}.")
    with open(tempfilename, "r", encoding='utf-8') as file:
        with open(filename, "w", encoding='utf-8') as file2:
            for idx, line in enumerate(file):
                i = idx + 1
                if i < start or i > end:
                    file2.write(line)
    logging.info(f"Removed lines {start}-{end} from {filename}.")

if __name__ == "__main__":
    remove_lines()