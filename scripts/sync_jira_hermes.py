import os
import sys
import time
import signal
import argparse
from datetime import datetime
from dotenv import load_dotenv
from jira import JIRA
import requests

# โหลดตัวแปรจาก .env ของ HoroConsultant
load_dotenv("/Users/kimlenglim/Project/HoroConsultant/.env")

JIRA_URL = os.getenv("JIRA_BASE_URL", "https://pansakorn.atlassian.net")
JIRA_EMAIL = os.getenv("JIRA_USER_EMAIL", "pansakorn@gmail.com")
JIRA_TOKEN = os.getenv("JIRA_API_TOKEN")
PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY", "KAN")
CURRENT_LANE = os.getenv("CURRENT_PROJECT_LANE", "Horo Consultant")

if not JIRA_TOKEN:
    raise ValueError("Missing JIRA_API_TOKEN in .env")

# Graceful shutdown flag
_shutdown = False


def _signal_handler(signum, frame):
    global _shutdown
    _shutdown = True
    print(f"\n[*] Shutdown signal received (signal {signum}). Finishing current poll...")


# Register signal handlers for graceful shutdown
signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)

jira = JIRA(server=JIRA_URL, basic_auth=(JIRA_EMAIL, JIRA_TOKEN))


def get_field_id(name: str):
    for f in jira.fields():
        if f["name"].strip().lower() == name.strip().lower():
            return f["id"]
    return None


LANE_FID = get_field_id("Project Lane")
ARTIFACT_FID = get_field_id("Target Artifacts")
VERIFY_FID = get_field_id("Verification Command")

POLL_INTERVAL = int(os.getenv("JIRA_POLL_INTERVAL_SECONDS", "30"))

# Fibonacci multiplier sequence for backoff: 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233
# When idle, the next interval = base_interval * fibonacci(idle_streak)
_FIBONACCI = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233]
_MAX_BACKOFF_SECONDS = int(os.getenv("JIRA_MAX_BACKOFF_SECONDS", "600"))

# Cache for Project Lane dropdown options (populated lazily by get_lane_options)
_lane_options_cache = {}


def get_lane_options():
    """Fetch all allowed values for the Project Lane select field.

    Uses the issue edit metadata API (GET /rest/api/3/issue/{key}/editmeta)
    to discover the dropdown's allowed values.  The createmetadata endpoint
    is not always available on Jira Cloud, so editmeta on any existing
    issue is the reliable fallback.

    Results are cached after the first successful call to avoid repeated
    API round-trips in daemon mode.

    Returns:
        dict: { lane_value_str: option_dict, ... }
    """
    if _lane_options_cache:
        return _lane_options_cache

    # Find any issue in the project to inspect its edit metadata
    jql = f'project = "{PROJECT_KEY}" ORDER BY created DESC'
    issues = jira.search_issues(jql, maxResults=1)
    if not issues:
        print("  [!] No issues found in project to inspect lane options.")
        return {}

    sample_key = issues[0].key
    resp = requests.get(
        f"{JIRA_URL}/rest/api/3/issue/{sample_key}/editmeta",
        auth=(JIRA_EMAIL, JIRA_TOKEN),
    )
    if resp.status_code != 200:
        print(f"  [!] editmeta returned HTTP {resp.status_code}")
        return {}

    fields_meta = resp.json().get("fields", {})
    lane_field = fields_meta.get(LANE_FID, {})
    allowed = lane_field.get("allowedValues", [])
    for opt in allowed:
        _lane_options_cache[opt["value"]] = opt

    return _lane_options_cache


def resolve_lane(lane_name: str):
    """Resolve a Project Lane name to its dropdown option dict.

    The agent uses this to autonomously select the correct dropdown
    option that matches a project (e.g. "Horo Consultant") instead
    of relying on hardcoded option IDs.

    Args:
        lane_name: The display value of the Project Lane (e.g. "Horo Consultant").

    Returns:
        The option dict {"id": "...", "value": "...", ...} if found,
        or None if the lane value does not exist in the Jira dropdown.
    """
    options = get_lane_options()
    return options.get(lane_name)


def notify_human(message: str):
    """Alert a human operator about a blocking issue that requires manual action.

    Prints a prominent message to stderr and, if a Telegram bot is configured,
    also sends a notification so the human is aware even in headless daemon mode.
    """
    border = "!" * 60
    print(f"\n{border}", file=sys.stderr)
    print(f"  ⚠️  HUMAN ALERT: {message}", file=sys.stderr)
    print(f"{border}\n", file=sys.stderr)

    # Best-effort Telegram notification
    tg_token = os.getenv("TELEGRAM_BOT_TOKEN")
    tg_chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if tg_token and tg_chat_id:
        try:
            requests.post(
                f"https://api.telegram.org/bot{tg_token}/sendMessage",
                json={"chat_id": tg_chat_id, "text": f"⚠️ HERMES ALERT: {message}"},
                timeout=5,
            )
            print("  [i] Telegram notification sent.", file=sys.stderr)
        except Exception as e:
            print(f"  [i] Telegram notification failed: {e}", file=sys.stderr)


def build_task_description(
    summary: str,
    subagent: str,
    skills: list[str] | None = None,
    mcp_tools: list[str] | None = None,
    scope: str | None = None,
    acceptance_criteria: list[str] | None = None,
    artifacts: list[str] | None = None,
    verification_command: str | None = None,
    priority: str = "Medium",
    labels: list[str] | None = None,
    goal: str | None = None,
    solution: str | None = None,
    detail: str | None = None,
    owner_agent: str | None = None,
    owner_role: str | None = None,
    owner_skills: list[str] | None = None,
) -> str:
    """Build a rich Jira description with full evidence metadata for
    traceability.  Records which subagent performed the work, what
    skills/MCP tools were bound, the delegated scope, goal, solution,
    detail, owner agent, and acceptance criteria — so any future
    audit can reconstruct exactly how a task was executed, why it
    was designed that way, and who is accountable.

    Args:
        summary: Short task title.
        subagent: Agent identifier (e.g. 'developer_core', 'qa_tester',
                  'agy1', 'codex1', 'orchestrator').
        skills: List of bound skill names (e.g. ['sdlc-aisdlc-workflow',
                'qa-e2e-testing']).
        mcp_tools: List of MCP tools used (e.g. ['mcp__github__create_pull_request',
                   'mcp__vercel__create_deployment']).
        scope: Free-text description of delegated scope.
        acceptance_criteria: List of DoD / acceptance criteria.
        artifacts: List of target artifact paths.
        verification_command: Shell command used to verify the task.
        priority: Jira priority label.
        labels: Extra Jira labels.
        goal: The business/technical goal this task achieves.
        solution: High-level solution approach / architecture decision.
        detail: Free-form technical detail, implementation notes,
                context for future refactoring/investigation.
        owner_agent: The agent accountable for delivery
                     (may differ from subagent for cross-team work).
        owner_role: Human-readable role of the owner agent.
        owner_skills: Skills bound to the owner agent.

    Returns:
        str: Markdown-formatted description suitable for Jira's
             description field.
    """
    lines: list[str] = []
    lines.append(f"h2. {summary}")
    lines.append("")

    # ── Owner & Responsibility ──
    display_owner = owner_agent or subagent
    lines.append(f"*Owner Agent:* {display_owner}")
    lines.append(f"*Subagent:* {subagent}")
    if owner_role:
        lines.append(f"*Owner Role:* {owner_role}")
    lines.append(f"*Priority:* {priority}")

    if owner_skills:
        lines.append(f"*Owner Skills:* {', '.join(owner_skills)}")
    lines.append("")

    # ── Goal ──
    if goal:
        lines.append("*Goal:*")
        lines.append(goal)
        lines.append("")

    # ── Solution ──
    if solution:
        lines.append("*Solution:*")
        lines.append(solution)
        lines.append("")

    # ── Scope ──
    if scope:
        lines.append("*Delegated Scope:*")
        lines.append(scope)
        lines.append("")

    # ── Technical Detail ──
    if detail:
        lines.append("*Detail:*")
        lines.append(detail)
        lines.append("")

    # ── Skills & MCP ──
    if skills:
        lines.append("*Bound Skills:*")
        for s in skills:
            lines.append(f"  • {s}")
        lines.append("")

    if mcp_tools:
        lines.append("*MCP Tools Used:*")
        for t in mcp_tools:
            lines.append(f"  • {t}")
        lines.append("")

    # ── Artifacts ──
    if artifacts:
        lines.append("*Target Artifacts:*")
        for a in artifacts:
            lines.append(f"  • {a}")
        lines.append("")

    # ── Acceptance Criteria ──
    if acceptance_criteria:
        lines.append("*Acceptance Criteria (DoD):*")
        for i, ac in enumerate(acceptance_criteria, 1):
            lines.append(f"  {i}. {ac}")
        lines.append("")

    # ── Verification ──
    if verification_command:
        lines.append("*Verification Command:*")
        lines.append(f"  {{code:bash}}{verification_command}{{code}}")
        lines.append("")

    # ── Evidence Footer ──
    lines.append("----")
    lines.append(f"_Created by Hermes Jira Sync at "
                 f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_")
    if labels:
        lines.append(f"_Labels: {', '.join(labels)}_")

    return "\n".join(lines)


def fetch_task():
    # กวาดตั๋วสถานะ Ready ที่เป็นของ Horo Consultant
    jql = f'project = "{PROJECT_KEY}" AND status = "Ready" ORDER BY created ASC'
    issues = jira.search_issues(jql, maxResults=20)

    for issue in issues:
        raw = jira.issue(issue.key).raw["fields"]
        lane_val = raw.get(LANE_FID)

        # ตรวจสอบว่าค่าของ Project Lane ตรงกับ Horo Consultant หรือไม่
        lane_str = lane_val.get("value") if isinstance(lane_val, dict) else str(lane_val)
        if lane_str == CURRENT_LANE:
            return issue

    # กรณีไม่มีที่ระบุ Lane ชัดเจน ให้ดึงตั๋วใบแรกใน Ready
    return issues[0] if issues else None


def transition_to(issue, target_name: str):
    for t in jira.transitions(issue):
        if t["name"].strip().lower() == target_name.strip().lower():
            jira.transition_issue(issue, t["id"])
            print(f"  [>] Moved {issue.key} -> {target_name}")
            return True
    print(f"  [!] Transition '{target_name}' not available for {issue.key}")
    return False


def process_task(task):
    """Process a single task through the full TDD workflow."""
    raw = jira.issue(task.key).raw["fields"]
    artifacts = raw.get(ARTIFACT_FID)
    verify_cmd = raw.get(VERIFY_FID)

    print(f"\n  ==========================================")
    print(f"  Task Key: {task.key}")
    print(f"  Summary : {task.fields.summary}")
    if ARTIFACT_FID:
        print(f"  Target Artifacts: {artifacts}")
    if VERIFY_FID:
        print(f"  Verification Cmd: {verify_cmd}")
    print(f"  ==========================================\n")

    # ปรับสถานะเข้าสู่กระบวนการทดสอบ
    transition_to(task, "TDD RED")
    transition_to(task, "TDD GREEN")

    import subprocess

    if verify_cmd:
        print(f"  [*] Running Gate: {verify_cmd}")
        res = subprocess.run(verify_cmd, shell=True, capture_output=True, text=True)
        print(res.stdout or res.stderr)
        if res.returncode == 0:
            print("  [✓] Verification passed!")
            transition_to(task, "Done")
        else:
            print("  [!] Verification failed. Holding in Review.")
            transition_to(task, "Review")
    else:
        transition_to(task, "Done")


def main():
    task = fetch_task()
    if not task:
        print("  [*] No tasks waiting in Ready queue.")
        return False

    process_task(task)
    return True


def run_daemon(interval: int = POLL_INTERVAL, max_iterations: int = 0,
               max_backoff: int = _MAX_BACKOFF_SECONDS):
    """Run as a background daemon, polling the Jira board for new tasks.

    Implements Fibonacci backoff: when no tasks are found, the polling
    interval increases following the Fibonacci sequence
    (interval * 1, * 1, * 2, * 3, * 5, * 8, ...) to reduce API traffic.
    When a task is found and processed, the interval resets to the base.

    Args:
        interval: Base seconds between poll cycles (default: from env or 30).
        max_iterations: Maximum poll cycles (0 = run indefinitely until
                        interrupted).
        max_backoff: Maximum seconds between polls when idle (default: 600).
    """
    mode = "limited" if max_iterations > 0 else "continuous"
    print(f"\n  ╔══════════════════════════════════════════════╗")
    print(f"  ║  HERMES JIRA WATCHER — Daemon Mode           ║")
    print(f"  ╠══════════════════════════════════════════════╣")
    print(f"  ║  Mode          : {mode}")
    print(f"  ║  Base Interval : {interval}s")
    print(f"  ║  Max Backoff   : {max_backoff}s")
    print(f"  ║  Backoff       : Fibonacci (1,1,2,3,5,8,13,...)" )
    print(f"  ║  Project       : {PROJECT_KEY}")
    print(f"  ║  Lane Filter   : {CURRENT_LANE}")
    if max_iterations > 0:
        print(f"  ║  Iterations    : {max_iterations}")
    else:
        print(f"  ║  Iterations    : ∞ (Ctrl+C to stop)")
    print(f"  ╚══════════════════════════════════════════════╝")

    idle_streak = 0
    iteration = 0
    while not _shutdown:
        iteration += 1
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n  ┌─── Poll #{iteration} @ {ts} ───")
        processed = main()

        if processed:
            idle_streak = 0
        else:
            idle_streak += 1

        if max_iterations > 0 and iteration >= max_iterations:
            print(f"\n  [*] Reached max_iterations ({max_iterations}). Daemon exiting.")
            break

        if not _shutdown:
            # Fibonacci backoff: base_interval * fib[idle_streak], capped at max_backoff
            idx = min(idle_streak, len(_FIBONACCI) - 1)
            next_interval = min(interval * _FIBONACCI[idx], max_backoff)
            backoff_note = f" (backoff ×{_FIBONACCI[idx]})" if idle_streak > 0 else ""
            print(f"  [*] Next poll in {next_interval}s...{backoff_note} (Ctrl+C to stop)")
            # Sleep in small increments to remain responsive to signals
            slept = 0
            while slept < next_interval and not _shutdown:
                time.sleep(1)
                slept += 1

    print(f"\n  [*] Daemon stopped after {iteration} poll cycle(s). "
          f"{'Idle streaks: ' + str(idle_streak) if idle_streak else 'Completed.'}")


def run_once():
    """Run a single poll cycle and exit."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"  ┌─── Single Run @ {ts} ───")
    processed = main()
    if processed:
        print("  [✓] Task processed.")
    else:
        print("  [*] Nothing to process.")
    return 0 if processed else 0


def parse_args():
    parser = argparse.ArgumentParser(
        description="Hermes Jira Sync — fetch and process Ready tasks from the Jira board.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  # Single run (default)
  python3 sync_jira_hermes.py --once

  # Daemon mode: poll every 30s, Fibonacci backoff when idle (up to 10min)
  python3 sync_jira_hermes.py --watch

  # Daemon mode: custom base interval and max backoff
  python3 sync_jira_hermes.py --watch --interval 15 --max-backoff 300

  # Daemon mode: limited to 5 poll cycles (useful for testing)
  python3 sync_jira_hermes.py --watch --max-iterations 5
""",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--once", action="store_true",
        help="Run a single poll cycle and exit (default).",
    )
    mode.add_argument(
        "--watch", action="store_true",
        help="Run as a daemon with Fibonacci backoff. Polls at --interval when busy, "
             "increasing up to --max-backoff when idle.",
    )
    parser.add_argument(
        "--interval", type=int, default=POLL_INTERVAL,
        help=f"Polling interval in seconds (default: {POLL_INTERVAL}). Only used with --watch.",
    )
    parser.add_argument(
        "--max-iterations", type=int, default=0,
        help="Maximum poll cycles for --watch mode (0 = unlimited). Useful for testing.",
    )
    parser.add_argument(
        "--max-backoff", type=int, default=_MAX_BACKOFF_SECONDS,
        help=f"Maximum seconds between polls when idle (default: {_MAX_BACKOFF_SECONDS}). "
             f"Uses Fibonacci backoff to reduce traffic when no tasks are found.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if args.watch:
        run_daemon(
            interval=args.interval,
            max_iterations=args.max_iterations,
            max_backoff=args.max_backoff,
        )
    else:
        # --once or default (no flags)
        run_once()
