#!/usr/bin/env python3
"""
fibonacci_backoff.py — Fibonacci backoff with jitter for idle polling.

When no tasks are found, the next poll interval follows Fibonacci:
1, 1, 2, 3, 5, 8, 13, 21, 34, 55 minutes

With ±15% jitter to prevent thundering herd.
"""

import json
import os
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

FIBONACCI_MINUTES = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55]
JITTER_FRACTION = 0.15
STATE_FILE = Path(__file__).parent / ".orchestrator_state.json"


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"idle_streak": 0, "last_poll": None}


def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def next_interval_minutes(idle_streak: int) -> float:
    idx = min(idle_streak, len(FIBONACCI_MINUTES) - 1)
    fib = FIBONACCI_MINUTES[idx]
    jitter = random.uniform(-JITTER_FRACTION, JITTER_FRACTION)
    return round(fib * (1 + jitter), 1)


def main():
    state = load_state()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--reset":
        state["idle_streak"] = 0
        save_state(state)
        print("Idle streak reset")
        return
    
    idle_streak = state.get("idle_streak", 0)
    interval = next_interval_minutes(idle_streak)
    next_poll = datetime.now() + timedelta(minutes=interval)
    
    print(f"Idle streak: {idle_streak}")
    print(f"Next poll in: {interval} min")
    print(f"Next poll at: {next_poll.strftime('%H:%M:%S')}")
    
    # Output for GitHub Actions
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"interval_minutes={interval}\n")
            f.write(f"next_poll={next_poll.isoformat()}\n")


if __name__ == "__main__":
    main()
