# Anti-StandupBot

A zero-fluff async standup logger for developers, PMs, and founders. Log your daily standups from the terminal, get Claude AI weekly digests, track todos with completion stats, and let the AI predict what you'll work on tomorrow based on your own behavioral patterns.

---

## Why

Standups are overhead. This tool makes them take 30 seconds, stores them locally, and uses Claude AI to turn a week of noise into a clean digest — without a calendar invite, a Slack message, or a meeting.

The smart todo system goes further: it watches your standup history, detects carry-over work, notices when blockers clear, and surfaces what you're *most likely* to do tomorrow. Not what you *should* do — what you *will* do.

---

## Commands

```
standup log         Log today's standup (yesterday / today / blockers)
standup show        Show today's entry
standup show -w     Show the full current week as a table
standup digest      Generate a Claude AI weekly digest (streamed)
standup history     List all weeks with entry counts

standup add <text>  Add a todo item
standup todos       List all todos with status and inferred project
standup done <id>   Mark a todo as done
standup skip <id>   Skip / dismiss a todo

standup suggest     Predict tomorrow's probable todos (needs ≥3 standups)
standup insights    Multi-week growth analysis: velocity, blockers, momentum
```

---

## Setup

**Requirements:** Python 3.10+, an [Anthropic API key](https://console.anthropic.com/)

```bash
# Clone the repo
git clone https://github.com/justanotheraryan-code/standup.git
cd standup

# Create a virtual environment and install
python -m venv .venv
source .venv/bin/activate
pip install -e .

# Add your API key
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY=sk-ant-...
```

Everything is stored locally in `~/.standup/standup.db` (SQLite). No cloud sync, no account.

---

## Usage

### Daily standup

```
$ standup log
What did you do yesterday? Finished the auth refactor, opened PR #42
What are you doing today? Review feedback on PR #42, start on rate limiter
Any blockers? Waiting on Lena to review before merge
✓ Logged standup for 2025-04-16
```

### View your week

```
$ standup show -w
╭──────────────────────────────── This Week's Standups ────────────────────────────────╮
│ Date         Yesterday                 Today                    Blockers             │
│ 2025-04-14   Fixed login redirect bug  Auth refactor            —                    │
│ 2025-04-15   Auth refactor             Finished auth, opened PR Waiting on Lena      │
│ 2025-04-16   PR #42, rate limiter      Merge auth, finish rate  —                    │
╰──────────────────────────────────────────────────────────────────────────────────────╯
```

### Weekly digest

```
$ standup digest
Generating weekly digest...

╭──────────────────── Weekly Digest ────────────────────╮
│                                                        │
│ ## Week of 2025-04-14                                  │
│                                                        │
│ **Shipped:** Auth refactor (PR #42), login redirect    │
│ **In Progress:** Rate limiter design                   │
│ **Blockers resolved:** Lena's review unblocked merge   │
│                                                        │
╰────────────────────────────────────────────────────────╯

Tokens — input: 1842, output: 312, cache read: 1680, cache write: 162
```

### Todos

```
$ standup add "Write rate limiter tests"
✓ Todo #3 added: Write rate limiter tests

$ standup todos
╭──────────────────────────── Todos ────────────────────────────────╮
│  ID  Text                          Status    Project      Added    │
│   1  Auth refactor PR review       done      auth         Apr 14   │
│   2  Design rate limiter API       open      backend      Apr 15   │
│   3  Write rate limiter tests      open      backend      Apr 16   │
│   4  Update onboarding docs        skipped   docs         Apr 14   │
╰───────────────────────────────────────────────────────────────────╯
```

Projects are inferred automatically from your standup text — no manual tagging.

### AI predictions

```
$ standup suggest
Generating predictions...

╭────────────── Tomorrow's Predicted Todos ──────────────╮
│                                                         │
│ ### Probable (high confidence)                          │
│ - Merge PR #42 after Lena's review clears               │
│   *Signal: blocker appeared Apr 15, likely resolved*    │
│ - Continue rate limiter implementation                  │
│   *Signal: mentioned in "today" 2 days running*         │
│                                                         │
│ ### Possible                                            │
│ - Write rate limiter tests                              │
│   *Signal: open todo, adjacent to active work thread*   │
│                                                         │
│ ### Unlikely                                            │
│ - Update onboarding docs                                │
│   *Signal: skipped once, no recent standup mention*     │
│                                                         │
╰─────────────────────────────────────────────────────────╯
```

### Growth insights

```
$ standup insights
Generating insights...

╭──────────────────── Work Insights ─────────────────────╮
│                                                         │
│ ## Velocity Trend                                       │
│ | Week      | Entries | Key themes            |         │
│ | 2025-W14  | 4       | auth, login           |         │
│ | 2025-W15  | 5       | auth, rate limiting   |         │
│                                                         │
│ ## Project Momentum                                     │
│ **auth** — shipped. **backend** — active thread.        │
│                                                         │
│ ## Blocker Patterns                                     │
│ External review dependencies appear weekly.             │
│                                                         │
│ ## Growth Signals                                       │
│ Consistent 4-5 entry weeks. Blockers resolve within     │
│ 1-2 days. Backend complexity is ramping up.             │
│                                                         │
╰─────────────────────────────────────────────────────────╯
```

---

## How it works

**Storage:** SQLite at `~/.standup/standup.db`. Two tables: `standups` (one row per day) and `todos`. No external services beyond the Anthropic API.

**AI features:** All three AI commands (`digest`, `suggest`, `insights`) stream tokens live to the terminal. Each uses a dedicated system prompt with [prompt caching](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching) — the static prompt prefix is cached on Anthropic's servers, so repeated runs cost significantly less.

**Prediction engine:** `suggest` reads your 14 most recent standups plus open todos. It detects carry-over work (things in "today" that never appeared in "yesterday"), blocker-cleared patterns, and weekly rhythms to rank predictions into Probable / Possible / Unlikely tiers.

**Project inference:** Claude infers project labels (`auth`, `backend`, `docs`, etc.) from your standup text. No tags, no config — it reads the words you already use.

---

## Project structure

```
standup/
├── cli.py          Typer CLI — all commands wired here
├── config.py       Paths, env vars, model name
├── db.py           SQLite layer for standups table
├── todos.py        SQLite layer for todos table
├── ai.py           digest — Claude streaming + prompt caching
├── predictor.py    suggest + insights — prediction engine
└── display.py      Rich terminal output (panels, tables, colors)
```

---

## Dependencies

| Package | Purpose |
|---|---|
| `typer` | CLI framework |
| `rich` | Terminal UI (panels, tables, markdown rendering) |
| `anthropic` | Claude API client |
| `python-dotenv` | `.env` file loading |

---

## License

MIT
