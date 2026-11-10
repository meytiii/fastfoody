---
trigger: always_on
description: Mandatory automated Git commit and push protocol requiring comprehensive commit summary, detailed body description, and pushing to the main branch of https://github.com/meytiii/fastfoody.
---

# Automated Git Commit & Push Protocol

Whenever a task, milestone, feature, bugfix, or refactoring request is completed, you MUST automatically commit and push the changes according to the following mandatory process:

## Mandatory Workflow Steps

### 1. Write a Comprehensive Commit Summary & Description
Before committing, compose a structured, professional Git commit message using Conventional Commits format:
- **Header Line (Summary):** `<type>(<scope>): <concise imperative summary>` (maximum 72 characters).
  - Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`.
- **Message Body (Comprehensive Description):**
  - **Context & Motivation:** Explain the problem solved or requirement fulfilled.
  - **Detailed List of Changes:** Explicitly itemize each modified, added, or removed file and component.
  - **Compliance Check:** Note verification against `frontend/DESIGN_SYSTEM.md`, accessibility (WCAG AA), RTL layout, and architecture standards.

### 2. Stage & Commit
- Verify `git status` and `git diff --staged` to ensure no sensitive files (`.env`, credentials, local temporary files) are staged.
- Stage relevant files with `git add <files>` (or `git add -A` for whole-task deliverables).
- Execute the commit:
  ```bash
  git commit -m "<Summary>" -m "<Comprehensive description...>"
  ```

### 3. Push to the Main Branch
- Push the committed changes directly to the `main` branch of the remote repository:
  ```bash
  git push origin main
  ```
- Target repository: `https://github.com/meytiii/fastfoody`
- Confirm that the push succeeds without errors. If a remote rejection or conflict occurs, inspect, resolve cleanly, and re-push.
