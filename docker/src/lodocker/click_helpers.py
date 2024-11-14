from pathlib import Path
from typing import Optional, Any

import click

def get_directories(path: str) -> list[str]:
    """Get a list of subdirectory names in the given directory."""
    path = Path(path)
    return [dir.name for dir in path.iterdir() if dir.is_dir()]

def directory_callback(ctx: click.Context, param: click.Parameter, value: Optional[str]) -> Any:
    if value is None:
        # Dynamically read the directories and prompt the user to choose
        choices = get_directories('docker_files')
        if not choices:
            raise click.UsageError('No directories found in docker_files.')

        choice_dict = dict(enumerate(choices, start=1))
        click.echo("Select a Dockerfile:")
        for idx, choice in choice_dict.items():
            click.echo(f'{idx}. {choice}')
        choice = click.prompt('Please enter an integer', type=click.IntRange(1, len(choices)))
        return choice_dict[choice]
    return value
