from __future__ import annotations

import asyncio
from pathlib import Path
from typing import List, Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from pascai_skill.core.exceptions import SkillNotFoundError
from pascai_skill.core.models import SkillStatus, MemoryEntry, KnowledgeEntry
from pascai_skill.installer.bootstrap import Bootstrap
from pascai_skill.knowledge.base import KnowledgeBase
from pascai_skill.memory.store import MemoryStore
from pascai_skill.plugins.discovery import AutoDiscovery
from pascai_skill.plugins.loader import PluginLoader
from pascai_skill.skills.manager import SkillManager
from pascai_skill.skills.metadata import SkillMetadataLoader
from pascai_skill.skills.registry import SkillRegistry
from pascai_skill.upstream.repository import GitUpstreamRepository
from pascai_skill.upstream.sync import SyncManager
from pascai_skill.upstream.version_db import VersionDatabase
from pascai_skill.engine.update_engine import UpdateEngine
from pascai_skill.engine.backup import BackupManager

console = Console()


def _get_bootstrap(ctx: click.Context) -> Bootstrap:
    base_dir: Path = ctx.obj["base_dir"]
    bootstrap = Bootstrap(base_dir)
    bootstrap.initialize()
    return bootstrap


def _get_skill_manager(ctx: click.Context) -> SkillManager:
    bootstrap = _get_bootstrap(ctx)
    if bootstrap.registry.list_all(include_disabled=True):
        return SkillManager(bootstrap.registry)
    bootstrap.load_skills()
    return SkillManager(bootstrap.registry)


# --- init ---
@click.command()
@click.pass_context
def init_cmd(ctx: click.Context) -> None:
    bootstrap = _get_bootstrap(ctx)
    issues = bootstrap.validate_environment()
    if issues:
        console.print("[yellow]Validation issues found:[/yellow]")
        for issue in issues:
            console.print(f"  • {issue}")
    result = bootstrap.load_skills()
    console.print(
        f"[green]Initialized:[/green] {result['skills']} skills, {result['adapters']} adapters"
    )


# --- status ---
@click.command()
@click.pass_context
def status_cmd(ctx: click.Context) -> None:
    mgr = _get_skill_manager(ctx)
    skills = mgr.list_skills(include_disabled=True)
    table = Table(title="Pascai AI Runtime Status", box=box.ROUNDED)
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Version")
    table.add_column("Status")
    table.add_column("Upstream")
    for s in skills:
        status_style = "green" if s.is_enabled() else "red"
        upstream = "yes" if s.metadata.has_upstream() else "no"
        table.add_row(
            s.id, s.name, s.version,
            f"[{status_style}]{s.metadata.status.value}[/{status_style}]",
            upstream,
        )
    console.print(table)
    console.print(f"\nTotal: {mgr.skill_count()} skills")


# --- skill commands ---
@click.group()
def skill_cmd() -> None:
    pass


@skill_cmd.command("list")
@click.option("--all", "-a", "show_all", is_flag=True, help="Include disabled skills")
@click.pass_context
def skill_list(ctx: click.Context, show_all: bool) -> None:
    mgr = _get_skill_manager(ctx)
    skills = mgr.list_skills(include_disabled=show_all)
    table = Table(title="Skills", box=box.ROUNDED)
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Version")
    table.add_column("Status")
    table.add_column("Prompts")
    table.add_column("Templates")
    for s in skills:
        status_style = "green" if s.is_enabled() else "red"
        table.add_row(
            s.id, s.name, s.version,
            f"[{status_style}]{s.metadata.status.value}[/{status_style}]",
            str(len(s.list_prompts())),
            str(len(s.list_templates())),
        )
    console.print(table)


@skill_cmd.command("show")
@click.argument("skill_id")
@click.pass_context
def skill_show(ctx: click.Context, skill_id: str) -> None:
    mgr = _get_skill_manager(ctx)
    try:
        skill = mgr.get_skill(skill_id)
    except SkillNotFoundError:
        console.print(f"[red]Skill not found: {skill_id}[/red]")
        return
    m = skill.metadata
    info = Panel(
        f"[bold]ID:[/bold] {m.id}\n"
        f"[bold]Name:[/bold] {m.name}\n"
        f"[bold]Version:[/bold] {m.version}\n"
        f"[bold]Description:[/bold] {m.description}\n"
        f"[bold]Author:[/bold] {m.author}\n"
        f"[bold]Status:[/bold] {m.status.value}\n"
        f"[bold]Tags:[/bold] {', '.join(m.tags) if m.tags else 'none'}\n"
        f"[bold]Upstream:[/bold] {m.upstream.url if m.upstream else 'none'}\n"
        f"[bold]Prompts:[/bold] {len(skill.list_prompts())}\n"
        f"[bold]Templates:[/bold] {len(skill.list_templates())}\n"
        f"[bold]Tools:[/bold] {len(skill.list_tools())}\n"
        f"[bold]Examples:[/bold] {len(skill.list_examples())}",
        title=f"Skill: {skill_id}",
    )
    console.print(info)


@skill_cmd.command("enable")
@click.argument("skill_id")
@click.pass_context
def skill_enable(ctx: click.Context, skill_id: str) -> None:
    mgr = _get_skill_manager(ctx)
    try:
        mgr.enable_skill(skill_id)
        console.print(f"[green]Enabled: {skill_id}[/green]")
    except SkillNotFoundError:
        console.print(f"[red]Skill not found: {skill_id}[/red]")


@skill_cmd.command("disable")
@click.argument("skill_id")
@click.pass_context
def skill_disable(ctx: click.Context, skill_id: str) -> None:
    mgr = _get_skill_manager(ctx)
    try:
        mgr.disable_skill(skill_id)
        console.print(f"[yellow]Disabled: {skill_id}[/yellow]")
    except SkillNotFoundError:
        console.print(f"[red]Skill not found: {skill_id}[/red]")


@skill_cmd.command("install")
@click.argument("url")
@click.option("--branch", default="main", help="Git branch")
@click.option("--name", help="Skill name (default: from URL)")
@click.pass_context
def skill_install(ctx: click.Context, url: str, branch: str, name: str | None) -> None:
    base_dir: Path = ctx.obj["base_dir"]
    skill_id = name or url.rstrip("/").split("/")[-1].replace(".git", "")
    dest = base_dir / "_runtime" / "installed" / skill_id
    repo = GitUpstreamRepository()
    sync_mgr = SyncManager(repo, VersionDatabase(base_dir / "_runtime" / "version_db.json"))

    console.print(f"[cyan]Installing {skill_id} from {url}...[/cyan]")
    record = asyncio.run(sync_mgr.install_from_url(url, dest, skill_id, branch))

    manifest = SkillMetadataLoader.load_from_dir(dest)
    if manifest:
        registry = SkillRegistry()
        from pascai_skill.core.base_skill import BaseSkill
        skill = BaseSkill(manifest)
        registry.register(skill)
        console.print(f"[green]Installed: {skill_id} (commit: {record.current_commit[:8] if record.current_commit else 'unknown'})[/green]")
    else:
        console.print(f"[yellow]Installed but no skill.yaml found in {dest}[/yellow]")


@skill_cmd.command("remove")
@click.argument("skill_id")
@click.pass_context
def skill_remove(ctx: click.Context, skill_id: str) -> None:
    mgr = _get_skill_manager(ctx)
    try:
        mgr.remove_skill(skill_id)
        console.print(f"[green]Removed: {skill_id}[/green]")
    except SkillNotFoundError:
        console.print(f"[red]Skill not found: {skill_id}[/red]")


@skill_cmd.command("search")
@click.argument("query")
@click.pass_context
def skill_search(ctx: click.Context, query: str) -> None:
    mgr = _get_skill_manager(ctx)
    results = mgr.search_skills(query)
    if not results:
        console.print(f"[yellow]No skills found matching '{query}'[/yellow]")
        return
    table = Table(title=f"Search Results: {query}", box=box.ROUNDED)
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Description")
    for s in results:
        table.add_row(s.id, s.name, s.metadata.description[:60])
    console.print(table)


@skill_cmd.command("status")
@click.argument("skill_id")
@click.pass_context
def skill_status(ctx: click.Context, skill_id: str) -> None:
    mgr = _get_skill_manager(ctx)
    try:
        skill = mgr.get_skill(skill_id)
        status = skill.metadata.status
        style = "green" if status == SkillStatus.ENABLED else "red"
        console.print(f"Skill [cyan]{skill_id}[/cyan] status: [{style}]{status.value}[/{style}]")
    except SkillNotFoundError:
        console.print(f"[red]Skill not found: {skill_id}[/red]")


@skill_cmd.command("changelog")
@click.argument("skill_id")
@click.pass_context
def skill_changelog(ctx: click.Context, skill_id: str) -> None:
    base_dir: Path = ctx.obj["base_dir"]
    vdb = VersionDatabase(base_dir / "_runtime" / "version_db.json")
    records = vdb.get_history(skill_id)
    if not records:
        console.print(f"[yellow]No changelog for {skill_id}[/yellow]")
        return
    for r in records:
        console.print(f"[bold]Sync at {r.synced_at.isoformat()}[/bold]")
        console.print(f"  Status: {r.status}")
        console.print(f"  From: {r.previous_commit[:8] if r.previous_commit else 'N/A'}")
        console.print(f"  To: {r.current_commit[:8] if r.current_commit else 'N/A'}")
        if r.changes:
            for c in r.changes[:10]:
                console.print(f"    • {c}")


@skill_cmd.command("sync")
@click.argument("skill_id")
@click.pass_context
def skill_sync(ctx: click.Context, skill_id: str) -> None:
    base_dir: Path = ctx.obj["base_dir"]
    mgr = _get_skill_manager(ctx)
    try:
        skill = mgr.get_skill(skill_id)
    except SkillNotFoundError:
        console.print(f"[red]Skill not found: {skill_id}[/red]")
        return
    if not skill.metadata.upstream:
        console.print(f"[yellow]No upstream for {skill_id}[/yellow]")
        return
    repo = GitUpstreamRepository()
    vdb = VersionDatabase(base_dir / "_runtime" / "version_db.json")
    sync_mgr = SyncManager(repo, vdb)
    record = asyncio.run(sync_mgr.sync(skill.metadata.upstream, skill_id))
    console.print(f"[green]Sync {skill_id}: {record.status}[/green]")


# --- adapter commands ---
@click.group()
def adapter_cmd() -> None:
    pass


@adapter_cmd.command("list")
@click.pass_context
def adapter_list(ctx: click.Context) -> None:
    loader = PluginLoader()
    adapters = loader.discover_adapters()
    table = Table(title="Adapters", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Skills Loaded")
    for a in adapters:
        table.add_row(a.name, "0 (run 'pascai init' first)")
    console.print(table)


@adapter_cmd.command("config")
@click.argument("adapter_name")
@click.pass_context
def adapter_config(ctx: click.Context, adapter_name: str) -> None:
    mgr = _get_skill_manager(ctx)
    loader = PluginLoader()
    adapter = loader.load_adapter(adapter_name)
    if adapter is None:
        console.print(f"[red]Adapter not found: {adapter_name}[/red]")
        return
    enabled = mgr.get_enabled_skills()
    adapter.load_skills(enabled)
    config = adapter.generate_config()
    import json
    console.print(json.dumps(config, indent=2))


# --- update commands ---
@click.group()
def update_cmd() -> None:
    pass


@update_cmd.command("check")
@click.argument("skill_id", required=False)
@click.pass_context
def update_check(ctx: click.Context, skill_id: str | None) -> None:
    base_dir: Path = ctx.obj["base_dir"]
    mgr = _get_skill_manager(ctx)
    repo = GitUpstreamRepository()
    vdb = VersionDatabase(base_dir / "_runtime" / "version_db.json")
    sync_mgr = SyncManager(repo, vdb)
    backup_mgr = BackupManager(base_dir / "_runtime" / "backups")
    engine = UpdateEngine(mgr, sync_mgr, vdb, backup_mgr)

    if skill_id:
        entry = asyncio.run(engine.check_updates(skill_id))
        if entry:
            console.print(f"[green]Updates available for {skill_id}[/green]")
            for c in entry.changes:
                console.print(f"  • {c}")
        else:
            console.print(f"[yellow]No updates for {skill_id}[/yellow]")
    else:
        console.print("[cyan]Checking all skills...[/cyan]")
        for skill in mgr.list_skills():
            if skill.metadata.has_upstream():
                entry = asyncio.run(engine.check_updates(skill.id))
                if entry:
                    console.print(f"  [green]{skill.id}: updates available[/green]")
                else:
                    console.print(f"  {skill.id}: up to date")


@update_cmd.command("apply")
@click.argument("skill_id", required=False)
@click.pass_context
def update_apply(ctx: click.Context, skill_id: str | None) -> None:
    base_dir: Path = ctx.obj["base_dir"]
    mgr = _get_skill_manager(ctx)
    repo = GitUpstreamRepository()
    vdb = VersionDatabase(base_dir / "_runtime" / "version_db.json")
    sync_mgr = SyncManager(repo, vdb)
    backup_mgr = BackupManager(base_dir / "_runtime" / "backups")
    engine = UpdateEngine(mgr, sync_mgr, vdb, backup_mgr)

    if skill_id:
        report = asyncio.run(engine.apply_update(skill_id))
        status = "✅" if report.success else "❌"
        console.print(f"{status} Update {skill_id}: {report.version_from} → {report.version_to}")
        if report.warnings:
            for w in report.warnings:
                console.print(f"  [yellow]⚠ {w}[/yellow]")
    else:
        results = asyncio.run(engine.update_all_skills())
        for sid, report in results.items():
            status = "✅" if report.success else "❌"
            console.print(f"{status} {sid}: {report.version_from} → {report.version_to}")


@update_cmd.command("rollback")
@click.argument("skill_id")
@click.option("--version", required=True, help="Version to rollback to")
@click.pass_context
def update_rollback(ctx: click.Context, skill_id: str, version: str) -> None:
    base_dir: Path = ctx.obj["base_dir"]
    mgr = _get_skill_manager(ctx)
    repo = GitUpstreamRepository()
    vdb = VersionDatabase(base_dir / "_runtime" / "version_db.json")
    sync_mgr = SyncManager(repo, vdb)
    backup_mgr = BackupManager(base_dir / "_runtime" / "backups")
    engine = UpdateEngine(mgr, sync_mgr, vdb, backup_mgr)

    success = asyncio.run(engine.rollback(skill_id, version))
    if success:
        console.print(f"[green]Rolled back {skill_id} to {version}[/green]")
    else:
        console.print(f"[red]No backup found for {skill_id} @ {version}[/red]")


@update_cmd.command("history")
@click.argument("skill_id")
@click.pass_context
def update_history(ctx: click.Context, skill_id: str) -> None:
    base_dir: Path = ctx.obj["base_dir"]
    mgr = _get_skill_manager(ctx)
    repo = GitUpstreamRepository()
    vdb = VersionDatabase(base_dir / "_runtime" / "version_db.json")
    sync_mgr = SyncManager(repo, vdb)
    backup_mgr = BackupManager(base_dir / "_runtime" / "backups")
    engine = UpdateEngine(mgr, sync_mgr, vdb, backup_mgr)

    entries = asyncio.run(engine.get_history(skill_id))
    if not entries:
        console.print(f"[yellow]No update history for {skill_id}[/yellow]")
        return
    table = Table(title=f"Update History: {skill_id}", box=box.ROUNDED)
    table.add_column("Date")
    table.add_column("From")
    table.add_column("To")
    table.add_column("Changes")
    for e in entries:
        table.add_row(
            e.created_at.strftime("%Y-%m-%d %H:%M"),
            e.version_from or "N/A",
            e.version_to,
            str(len(e.changes)),
        )
    console.print(table)


# --- memory commands ---
@click.group()
def memory_cmd() -> None:
    pass


@memory_cmd.command("set")
@click.argument("key")
@click.argument("value")
@click.option("--namespace", "-n", default="default")
@click.option("--tags", "-t", help="Comma-separated tags")
@click.pass_context
def memory_set(ctx: click.Context, key: str, value: str, namespace: str, tags: str | None) -> None:
    base_dir: Path = ctx.obj["base_dir"]
    store = MemoryStore(base_dir / "_runtime" / "memory.db")
    tag_list = [t.strip() for t in tags.split(",")] if tags else []
    entry = MemoryEntry(key=key, value=value, namespace=namespace, tags=tag_list)
    asyncio.run(store.set(entry))
    console.print(f"[green]Memory set: {namespace}/{key}[/green]")


@memory_cmd.command("get")
@click.argument("key")
@click.option("--namespace", "-n", default="default")
@click.pass_context
def memory_get(ctx: click.Context, key: str, namespace: str) -> None:
    base_dir: Path = ctx.obj["base_dir"]
    store = MemoryStore(base_dir / "_runtime" / "memory.db")
    entry = asyncio.run(store.get(key, namespace))
    if entry:
        console.print(f"[bold]{namespace}/{key}[/bold]")
        console.print(entry.value)
    else:
        console.print(f"[yellow]Not found: {namespace}/{key}[/yellow]")


@memory_cmd.command("search")
@click.argument("query")
@click.option("--namespace", "-n", default="default")
@click.pass_context
def memory_search(ctx: click.Context, query: str, namespace: str) -> None:
    base_dir: Path = ctx.obj["base_dir"]
    store = MemoryStore(base_dir / "_runtime" / "memory.db")
    results = asyncio.run(store.search(query, namespace))
    if not results:
        console.print(f"[yellow]No results for '{query}'[/yellow]")
        return
    for r in results:
        console.print(f"[cyan]{r.key}[/cyan]: {r.value[:100]}")


# --- knowledge commands ---
@click.group()
def knowledge_cmd() -> None:
    pass


@knowledge_cmd.command("add")
@click.argument("source")
@click.argument("content")
@click.option("--type", "content_type", default="markdown")
@click.pass_context
def knowledge_add(ctx: click.Context, source: str, content: str, content_type: str) -> None:
    base_dir: Path = ctx.obj["base_dir"]
    kb = KnowledgeBase(base_dir / "_runtime" / "knowledge")
    entry = KnowledgeEntry(source=source, content=content, content_type=content_type)
    entry_id = asyncio.run(kb.store(entry))
    console.print(f"[green]Knowledge added: {entry_id}[/green]")


@knowledge_cmd.command("search")
@click.argument("query")
@click.pass_context
def knowledge_search(ctx: click.Context, query: str) -> None:
    base_dir: Path = ctx.obj["base_dir"]
    kb = KnowledgeBase(base_dir / "_runtime" / "knowledge")
    results = asyncio.run(kb.search(query))
    if not results:
        console.print(f"[yellow]No results for '{query}'[/yellow]")
        return
    for r in results:
        console.print(f"[cyan]{r.id[:8]}[/cyan] ({r.source}): {r.content[:100]}")
