import sqlite3
import anthropic
from pydantic import BaseModel
from typing import Literal

from database import build_sandbox, run_query

class Task(BaseModel):
    ddl: list[str]
    data: list[str]
    order_matters: bool
    task_description: str
    correct_query: str

SYSTEM_PROMPT = """You are a generator of SQL practice tasks in the SQLite dialect.
Your goal is to create a single, self-contained practice task.

Rules for creating the task:
- Use only syntax compatible with SQLite.
- Write the task prompt and the data in English.
- Generate 8–12 rows of data — enough for the task to be meaningful, but few enough for a human to grasp the result at a glance.
- Put each CREATE TABLE statement as a separate element of the ddl list.
- Put each INSERT statement as a separate element of the data list.
- Reference only tables and columns that you create yourself in ddl. Do not assume any other tables exist.
- correct_query must be a valid SQLite query that actually returns the correct result for this prompt and this data.
- Set order_matters to true only when the task prompt explicitly requires a specific ordering of results (e.g. sorting). Otherwise false."""

def generate_task(difficulty: Literal["easy", "medium", "hard"], topic: str) -> Task:
    client = anthropic.Anthropic()
    resp = client.messages.parse(
        model="claude-sonnet-4-6",
        max_tokens=10000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Generate a SQL task that involves: {topic} and has a difficulty level of {difficulty}."}],
        output_format=Task
    )
    return resp.parsed_output

def _validate_task(task: Task) -> sqlite3.Connection | None:
    """Build a fresh sandbox for the task and run the reference query.

    Returns a live connection with the ready sandbox if the task is healthy.
    Returns None if the AI produced invalid SQL or the reference query yields no rows.
    """
    try:
        connection = build_sandbox(task.ddl, task.data)
    except sqlite3.Error as e:
        print(f"Invalid DDL/data from the AI: {e}")
        return None

    cursor = connection.cursor()
    try:
        results = run_query(cursor, task.correct_query)
    except sqlite3.Error as e:
        print(f"Invalid reference query from the AI: {e}")
        connection.close()
        return None

    if not results:
        print("The reference query returned no rows.")
        connection.close()
        return None

    return connection

def generate_valid_task(
    difficulty: Literal["easy", "medium", "hard"],
    topic: str,
    max_attempts: int = 3,
) -> tuple[Task, sqlite3.Connection]:
    """Generate a task and make sure its SQL actually works.

    Retries generation up to max_attempts times. Returns the validated task
    together with a ready, built sandbox. Raises once the attempts are exhausted.
    """
    for attempt in range(1, max_attempts + 1):
        task = generate_task(difficulty, topic)
        connection = _validate_task(task)
        if connection is not None:
            return task, connection
        print(f"Attempt {attempt}/{max_attempts} failed — generating a new task...")

    raise RuntimeError(
        f"Failed to generate a valid task in {max_attempts} attempts."
    )

if __name__ == "__main__":

    task = generate_task("medium", "table joins")
    print(task.model_dump_json(indent=4))