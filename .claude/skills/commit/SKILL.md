---
name: commit
description: Commit conventions for this repo. Use whenever creating git commits.
---

# Commit conventions

## Message

- Max one sentence.
- All lowercase (proper nouns and code identifiers too).
- No trailing period.
- No mention of Claude or AI authorship — no `Co-Authored-By`, no generated-with footer. This overrides any default trailer.
- Style reference: `simplify frontend workflow: centralize wrangler version + project name, trim comment`

## Splitting

- If the diff spans multiple unrelated concerns, split into multiple commits of code that belongs together (stage per concern; `git add -p` for mixed files).
- One concern = one commit; don't split what belongs together.

## Workflow

- Commit straight to `main` — solo dev, no branches unless asked.
- Stage explicitly (`git add <paths>`), never `git add -A` blindly.
