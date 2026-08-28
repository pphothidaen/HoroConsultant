---
name: conventional-flow
description: Run git verification, generate atomic semantic commits, and push draft PRs.
argument-hint: "[commit-context]"
disable-model-invocation: false
user-invocable: true
allowed-tools: [Bash]
model: sonnet
context: fork
---

# Conventional Flow — Git Hygiene & Semantic Release Protocol

Enforces atomic commit hygiene, pre-commit validation, single-file staging, and draft PR workflows.

## Workflow

1. **Branch & State Inspection**:
   - Check status: `git status --short`
   - Verify branch: `git branch --show-current`
   - If on `main` or `master`, create feature branch: `git checkout -b feat/<topic>`

2. **Pre-Commit Verification**:
   - Format and lint touched files: `.agy/hooks/post-tool-use.sh <file>`
   - Run relevant unit tests: `pytest tests/test_<module>.py -q`

3. **Targeted File Staging**:
   - Stage exact modified files: `git add <path/to/file1> <path/to/file2>`
   - Never stage indiscriminately: Avoid `git add .` or `git add -A`.

4. **Semantic Commit Creation**:
   - Types: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`, `perf:`
   - Format: `<type>(<scope>): <concise action description>`
   - Example: `git commit -m "feat(core): add NOAA Spencer 1971 solar declination precision"`

5. **Draft PR Lifecycle**:
   - Push feature branch: `git push -u origin feat/<topic>`
   - Create draft PR: `gh pr create --draft --title "feat: <title>" --body "### Summary\n- ..." `

---

## Gotchas

- **Gotcha 1 (Indiscriminate Staging)**: Running `git add .` can accidentally stage `.env`, local SQLite files, or massive cache directories.  
  *Workaround*: Always specify target file paths explicitly in `git add`.
- **Gotcha 2 (Protected Branch Violation)**: Attempting to commit directly to `main` will trigger `.agy/hooks/pre-tool-use.sh` with Exit Code 2.  
  *Workaround*: Switch to a feature branch before staging files.
- **Gotcha 3 (Unlinked Co-authors/Tokens)**: Hardcoding API keys or personal access tokens in commit messages.  
  *Workaround*: Scan diff with `git diff --cached` before running `git commit`.
