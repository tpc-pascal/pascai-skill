from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from pascai_skill.cli.commands import (
    adapter_cmd,
    init_cmd,
    knowledge_cmd,
    memory_cmd,
    skill_cmd,
    status_cmd,
    update_cmd,
)

console = Console()


@click.group()
@click.option(
    "--dir",
    "-d",
    default=".",
    help="Runtime base directory",
    envvar="pascai_RUNTIME_DIR",
)
@click.pass_context
def cli(ctx: click.Context, dir: str) -> None:
    ctx.ensure_object(dict)
    ctx.obj["base_dir"] = Path(dir).resolve()


cli.add_command(skill_cmd)
cli.add_command(adapter_cmd)
cli.add_command(update_cmd)
cli.add_command(memory_cmd)
cli.add_command(knowledge_cmd)
cli.add_command(init_cmd)
cli.add_command(status_cmd)


def run_async(coro):
    return asyncio.run(coro)


if __name__ == "__main__":
    cli()
