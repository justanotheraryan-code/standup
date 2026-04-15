from datetime import date, timedelta

import typer

from standup import ai, config, db, display, todos, predictor

app = typer.Typer(
    name="standup",
    help="Zero-fluff async standup logger. Summarized weekly by Claude AI.",
    no_args_is_help=True,
    add_completion=False,
)


@app.callback()
def main() -> None:
    config.ensure_dir()
    db.init()


def _current_week_start() -> str:
    today = date.today()
    return (today - timedelta(days=today.weekday())).isoformat()


@app.command()
def log() -> None:
    """Log today's standup."""
    yesterday = typer.prompt("What did you do yesterday?")
    today_work = typer.prompt("What are you doing today?")
    blockers = typer.prompt("Any blockers?", default="")

    db.upsert_standup(
        date_str=date.today().isoformat(),
        yesterday=yesterday,
        today=today_work,
        blockers=blockers,
    )
    display.print_success(f"Logged standup for {date.today().isoformat()}")


@app.command()
def show(
    week: bool = typer.Option(False, "--week", "-w", help="Show the entire current week"),
) -> None:
    """Display today's standup or the whole week."""
    if week:
        rows = db.get_week(_current_week_start())
        if not rows:
            display.print_error("No entries this week. Run 'standup log' first.")
            raise typer.Exit(1)
        display.print_week_table(rows)
    else:
        row = db.get_today()
        if not row:
            display.print_error("No entry for today. Run 'standup log' first.")
            raise typer.Exit(1)
        display.print_entry(row)


@app.command()
def digest() -> None:
    """Generate a Claude AI weekly digest for the current week."""
    if not config.ANTHROPIC_API_KEY:
        display.print_error(
            "ANTHROPIC_API_KEY is not set. Add it to .env or export it."
        )
        raise typer.Exit(1)

    rows = db.get_week(_current_week_start())
    if not rows:
        display.print_error("No entries this week to summarize.")
        raise typer.Exit(1)

    entries = [dict(r) for r in rows]
    display.console.print("[bold]Generating weekly digest...[/bold]\n")

    try:
        markdown_text, usage = ai.generate_digest(entries)
        display.print_digest(markdown_text)
        display.console.print(
            f"\n[dim]Tokens — input: {usage['input_tokens']}, "
            f"output: {usage['output_tokens']}, "
            f"cache read: {usage['cache_read_input_tokens']}, "
            f"cache write: {usage['cache_creation_input_tokens']}[/dim]"
        )
    except Exception as e:
        display.print_error(f"Claude API error: {e}")
        raise typer.Exit(1)


@app.command()
def history() -> None:
    """List all weeks that have standup entries."""
    weeks = db.get_all_weeks()
    if not weeks:
        display.print_error("No standup history found.")
        raise typer.Exit(1)
    display.print_weeks_list(weeks)


# ---------------------------------------------------------------------------
# Todo commands
# ---------------------------------------------------------------------------

@app.command()
def add(text: str = typer.Argument(..., help="Todo text")) -> None:
    """Add a new todo item."""
    todo_id = todos.add_todo(text)
    display.print_todo_added(todo_id, text)


@app.command()
def done(todo_id: int = typer.Argument(..., help="Todo ID to mark as done")) -> None:
    """Mark a todo as done."""
    open_rows = todos.get_open_todos()
    match = next((t for t in open_rows if t["id"] == todo_id), None)
    if match is None:
        display.print_error(f"No open todo with ID {todo_id}. Run 'standup todos' to see IDs.")
        raise typer.Exit(1)
    todos.set_status(todo_id, "done")
    display.print_todo_done(todo_id, match["text"])


@app.command()
def skip(todo_id: int = typer.Argument(..., help="Todo ID to skip/dismiss")) -> None:
    """Skip/dismiss a todo."""
    open_rows = todos.get_open_todos()
    match = next((t for t in open_rows if t["id"] == todo_id), None)
    if match is None:
        display.print_error(f"No open todo with ID {todo_id}. Run 'standup todos' to see IDs.")
        raise typer.Exit(1)
    todos.set_status(todo_id, "skipped")
    display.print_todo_skipped(todo_id, match["text"])


@app.command(name="todos")
def todos_list() -> None:
    """List all todos with their status."""
    rows = todos.get_all_todos()
    display.print_todos(rows)


# ---------------------------------------------------------------------------
# Prediction + insights commands
# ---------------------------------------------------------------------------

@app.command()
def suggest() -> None:
    """Predict probable todos for tomorrow based on standup history."""
    if not config.ANTHROPIC_API_KEY:
        display.print_error("ANTHROPIC_API_KEY is not set. Add it to .env or export it.")
        raise typer.Exit(1)

    recent = db.get_recent_standups(n=14)
    entry_count = len(recent)

    if entry_count < 3:
        noun = "entry" if entry_count == 1 else "entries"
        display.print_error(
            f"Only {entry_count} standup {noun} found. "
            "Need at least 3 to generate predictions."
        )
        raise typer.Exit(1)

    open_todos = [dict(t) for t in todos.get_open_todos()]
    stats = todos.get_completion_stats()
    entries = [dict(r) for r in recent]

    display.console.print("[bold]Generating predictions...[/bold]\n")

    try:
        markdown_text, usage = predictor.generate_suggestions(entries, open_todos, stats)
        display.print_suggestions(markdown_text)
        display.console.print(
            f"\n[dim]Tokens — input: {usage['input_tokens']}, "
            f"output: {usage['output_tokens']}, "
            f"cache read: {usage['cache_read_input_tokens']}, "
            f"cache write: {usage['cache_creation_input_tokens']}[/dim]"
        )
    except Exception as e:
        display.print_error(f"Claude API error: {e}")
        raise typer.Exit(1)


@app.command()
def insights() -> None:
    """Multi-week growth analysis: velocity, blockers, project momentum, work patterns."""
    if not config.ANTHROPIC_API_KEY:
        display.print_error("ANTHROPIC_API_KEY is not set. Add it to .env or export it.")
        raise typer.Exit(1)

    all_entries = db.get_all_standups()
    entry_count = len(all_entries)

    if entry_count < 3:
        noun = "entry" if entry_count == 1 else "entries"
        display.print_error(
            f"Only {entry_count} standup {noun} found. "
            "Need at least 3 for meaningful insights."
        )
        raise typer.Exit(1)

    stats = todos.get_completion_stats()
    weeks = db.get_all_weeks()
    entries = [dict(r) for r in all_entries]

    display.console.print("[bold]Generating insights...[/bold]\n")

    try:
        markdown_text, usage = predictor.generate_insights(entries, stats, weeks)
        display.print_insights(markdown_text)
        display.console.print(
            f"\n[dim]Tokens — input: {usage['input_tokens']}, "
            f"output: {usage['output_tokens']}, "
            f"cache read: {usage['cache_read_input_tokens']}, "
            f"cache write: {usage['cache_creation_input_tokens']}[/dim]"
        )
    except Exception as e:
        display.print_error(f"Claude API error: {e}")
        raise typer.Exit(1)
