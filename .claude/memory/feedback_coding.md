---
name: Coding preferences
description: How the user likes code written and presented in this project
type: feedback
originSessionId: 4c9d9065-af85-4cb9-9746-d9481ea820c9
---
- Prefers **step-by-step guidance** — explain before doing, confirm understanding at each step
- Likes **verbose but clean output** — rolling progress with segment filters, counts, page numbers
- Wants **warnings to stand out** — use red ANSI color for any data loss / cap warnings
- Prefers **incremental CSV writes** — don't buffer all results in memory, write as you go
- Likes **logically grouped fields** in CSV (not alphabetical or insertion order)
- Wants **timestamped output filenames** to avoid overwriting previous runs
- Prefers `requests` + direct API calls over browser automation whenever possible
- Keep comments/docstrings in code minimal and purposeful — no excessive inline commentary

**Why:** User is methodical and wants to understand what the code is doing at each stage, not just get a working script.
