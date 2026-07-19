# SQLearner

An interactive console app for learning SQL. The AI invents a task on the fly
(prompt + tables + data + reference query), you write your own query, and the system
runs it against a real database and checks whether the result matches.

> Portfolio project built in "learning mode" — the focus is on understanding the
> architecture, not on generating code quickly.

## How it works

1. **The AI generates a task.** The model (`claude-sonnet-4-6`) returns a structured
   response (Pydantic `Task`): `CREATE TABLE` statements, `INSERT`s, the task prompt,
   the reference query, and an `order_matters` flag.
2. **The database is the source of truth — not the AI.** The AI does not return a
   ready-made result (models hallucinate numbers). Instead, the system **runs the
   reference query** against a freshly built in-memory SQLite (`:memory:`) sandbox,
   and that is the correct result.
3. **Task validation (fail-fast + retry).** Before a task reaches the user, the system
   builds the sandbox and runs the reference query. If the AI produced invalid SQL,
   the task is discarded and regenerated, with a hard attempt limit.
4. **The user writes a query.** The result is compared to the reference: `==` when
   ordering matters (`order_matters=True`), and `sorted() == sorted()` when it does not.
5. **Read-only sandbox.** A SQLite authorizer blocks mutating operations
   (`INSERT`/`UPDATE`/`DELETE`/`DROP`/`CREATE`/`ALTER`), so the user cannot corrupt the
   task data. Read queries (including aggregate functions) work normally. A query that
   returns no result set at all is rejected with a `NoResultSetError` and an explanatory
   message, instead of crashing the session.

## Stack

- **Python** ≥ 3.12
- **SQLite** (`sqlite3` from the standard library) — `:memory:` sandbox
- **Anthropic SDK** — task generation via structured output (`messages.parse`)
- **Pydantic** — contract for the shape of the AI response
- **uv** — dependency management and running

## Requirements

An Anthropic API key in an environment variable (never in the code):

```bash
export ANTHROPIC_API_KEY="sk-ant-..."   # e.g. in ~/.zshrc
```

`anthropic.Anthropic()` reads it automatically.

## Running

```bash
uv sync        # install dependencies from uv.lock
uv run main.py # start the app
```

During a session:
- type a SQL query and confirm with Enter,
- type `exit` to quit.

## Project structure

```
main.py           # entry point / conductor: user loop, presentation, answer validation
app/
├── __init__.py
├── ai.py         # task generation: Task model, system prompt, retry
└── database.py   # engine: sandbox, query execution, comparison, authorizer
```

- **`main.py`** — the entry point, kept at the root and deliberately separate from the
  `app` package: it ties everything together, shows the tables and the task prompt, takes
  the user's query, handles errors, and compares the result.
- **`app/ai.py`** — the `Task` model (Pydantic), `generate_task()`, and `generate_valid_task()`
  (generation with validation and an attempt limit; returns a validated task + a ready sandbox).
- **`app/database.py`** — `build_sandbox()`, `run_query()`, `compare_results()`,
  `print_table()`, `clear_terminal()`, `authorizer()` (write blocking), and the
  `NoResultSetError` exception raised when a query returns no result set.

## Key architectural decisions

- **Database = source of truth.** The AI generates a *reference query*, not a final result.
- **Fresh sandbox per task.** `:memory:` gives isolation for free; every generation
  attempt gets its own connection.
- **Structured output as a contract.** The `Task` class + `messages.parse` guarantee the
  shape of the AI response.
- **Separation of concerns.** `database.py` (engine) / `ai.py` (generation) /
  `main.py` (conductor) — the conductor knows the *what*, not the *how*.
- **Sandbox safety via an authorizer**, not via string parsing.

## Roadmap

- [x] `input()` mode for a real user
- [ ] Difficulty adaptation based on answer performance
- [ ] Persistent progress storage (separate SQLite file)
- [ ] Deliberate migration path to PostgreSQL at larger scale
