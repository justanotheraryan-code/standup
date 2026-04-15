import sqlite3

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()


def print_entry(row: sqlite3.Row) -> None:
    content = (
        f"[bold]Yesterday[/bold]\n{row['yesterday']}\n\n"
        f"[bold]Today[/bold]\n{row['today']}"
    )
    if row["blockers"]:
        content += f"\n\n[bold red]Blockers[/bold red]\n{row['blockers']}"

    console.print(
        Panel(
            content,
            title=f"[bold cyan]Standup — {row['date']}[/bold cyan]",
            border_style="cyan",
            padding=(1, 2),
        )
    )


def print_week_table(rows: list[sqlite3.Row]) -> None:
    table = Table(
        title="This Week's Standups",
        box=box.ROUNDED,
        show_lines=True,
        header_style="bold cyan",
    )
    table.add_column("Date", style="cyan", no_wrap=True, width=12)
    table.add_column("Yesterday", max_width=40, overflow="fold")
    table.add_column("Today", max_width=40, overflow="fold")
    table.add_column("Blockers", max_width=30, overflow="fold", style="red")

    for row in rows:
        table.add_row(
            row["date"],
            row["yesterday"],
            row["today"],
            row["blockers"] or "—",
        )

    console.print(table)


def print_digest(markdown_text: str) -> None:
    console.print()
    console.print(
        Panel(
            Markdown(markdown_text),
            title="[bold green]Weekly Digest[/bold green]",
            border_style="green",
            padding=(1, 2),
        )
    )


def print_weeks_list(weeks: list[tuple[str, int]]) -> None:
    table = Table(
        title="Standup History",
        box=box.SIMPLE_HEAVY,
        header_style="bold cyan",
    )
    table.add_column("#", style="dim", width=4)
    table.add_column("Week", style="cyan")
    table.add_column("Entries", justify="right")

    for i, (week, count) in enumerate(weeks, 1):
        table.add_row(str(i), week, str(count))

    console.print(table)


def print_error(msg: str) -> None:
    console.print(Panel(f"[red]{msg}[/red]", border_style="red"))


def print_success(msg: str) -> None:
    console.print(f"[green]✓[/green] {msg}")


# ---------------------------------------------------------------------------
# Todo display
# ---------------------------------------------------------------------------

_STATUS_STYLE = {
    "open":    "[green]open[/green]",
    "done":    "[dim]done[/dim]",
    "skipped": "[yellow]skipped[/yellow]",
}

_SOURCE_STYLE = {
    "manual":    "",
    "suggested": " [dim magenta]ai[/dim magenta]",
}


def print_todos(rows: list[sqlite3.Row]) -> None:
    """Display all todos (any status) with status + project columns."""
    if not rows:
        print_error("No todos yet. Use 'standup add <text>' to create one.")
        return

    table = Table(
        title="Todos",
        box=box.ROUNDED,
        show_lines=True,
        header_style="bold cyan",
    )
    table.add_column("ID", style="dim", width=4, justify="right")
    table.add_column("Text", max_width=48, overflow="fold")
    table.add_column("Status", width=10, no_wrap=True)
    table.add_column("Project", width=14, style="dim", overflow="fold")
    table.add_column("Added", width=11, style="dim", no_wrap=True)

    for row in rows:
        status_label = _STATUS_STYLE.get(row["status"], row["status"])
        source_tag = _SOURCE_STYLE.get(row["source"], "")
        project = row["inferred_project"] or "—"
        added = str(row["created_at"])[:10]
        table.add_row(
            str(row["id"]),
            row["text"] + source_tag,
            status_label,
            project,
            added,
        )

    console.print(table)


def print_todo_added(todo_id: int, text: str) -> None:
    console.print(f"[green]✓[/green] Todo [bold]#{todo_id}[/bold] added: {text}")


def print_todo_done(todo_id: int, text: str) -> None:
    console.print(f"[green]✓[/green] Todo [bold]#{todo_id}[/bold] marked done: [dim]{text}[/dim]")


def print_todo_skipped(todo_id: int, text: str) -> None:
    console.print(f"[yellow]→[/yellow] Todo [bold]#{todo_id}[/bold] skipped: [dim]{text}[/dim]")


def print_suggestions(markdown_text: str) -> None:
    console.print()
    console.print(
        Panel(
            Markdown(markdown_text),
            title="[bold magenta]Tomorrow's Predicted Todos[/bold magenta]",
            border_style="magenta",
            padding=(1, 2),
        )
    )


def print_insights(markdown_text: str) -> None:
    console.print()
    console.print(
        Panel(
            Markdown(markdown_text),
            title="[bold yellow]Work Insights[/bold yellow]",
            border_style="yellow",
            padding=(1, 2),
        )
    )
