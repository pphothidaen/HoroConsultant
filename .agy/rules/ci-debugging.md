---
description: Low-noise local and CI failure investigation protocol.
paths:
  - ".github/workflows/**/*.yml"
  - ".github/workflows/**/*.yaml"
  - "scripts/**/*.py"
  - "scripts/**/*.sh"
  - "project/tests/**/*.py"
  - "tests/**/*.py"
---

# CI debugging and context-budget discipline

- Fetch only failed CI output with `gh run view <run-id> --log-failed`; extract
  the cited path and line, then locate context locally with `rg`.
- Check CI manually with exponential backoff (for example 30 seconds, then 60,
  then 120) rather than streaming logs or polling in a tight loop. To inspect a
  job summary, prefer `gh run view <run-id> | rg '<job-name>'`.
- Put long local reproductions in tmux and read a bounded tail:

  ```bash
  tmux new-session -d -s horo-ci 'python3 -m pytest -q <target>; exec zsh'
  tmux capture-pane -pt horo-ci -S -120
  ```

- Never paste full background-test or CI logs into the main conversation. Report
  the failing command, exit status, concise failure tail, and next action.
