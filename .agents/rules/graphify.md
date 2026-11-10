---
trigger: always_on
description: Consult the graphify knowledge graph at graphify-out/ for codebase and architecture questions.
---

# Graphify Codebase Knowledge Rule

- For codebase, architecture, and dependency questions: when `graphify-out/graph.json` exists, first run `graphify query "<question>"` (CLI) or use graph tools.
- Use `graphify path "<A>" "<B>"` for module relationships and `graphify explain "<concept>"` for focused concepts.
- When `graphify-out/wiki/index.md` exists, consult it for structured module overviews before deep file exploration.
- After substantial code or structural refactoring in the session, run `/graphify` or `graphify update .` to keep the knowledge graph in sync.

