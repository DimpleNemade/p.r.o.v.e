"""Validate Mermaid blocks embedded in the project's Markdown.

Checks, for every ``docs/**/*.md`` file:
  * code fences are balanced (no unclosed ```mermaid block);
  * each Mermaid block starts with a supported diagram header.

Exits non-zero on any problem. No third-party dependencies.
"""

from pathlib import Path
import re

DOCS = Path(__file__).resolve().parents[1] / "docs"
SUPPORTED = ("flowchart", "sequenceDiagram", "stateDiagram-v2", "gantt", "graph", "erDiagram")

errors: list[str] = []
files = sorted(DOCS.rglob("*.md"))

for path in files:
    rel = path.relative_to(DOCS.parent)
    text = path.read_text(encoding="utf-8")

    if text.count("```") % 2 != 0:
        errors.append(f"{rel}: unbalanced code fences (an opening ``` has no closing ```)")
        continue

    for block in re.findall(r"```mermaid[ \t]*\n(.*?)```", text, re.S):
        stripped = block.strip()
        first = stripped.splitlines()[0] if stripped else ""
        if not first:
            errors.append(f"{rel}: empty Mermaid block")
        elif not re.match(rf"^({'|'.join(SUPPORTED)})\b", first):
            errors.append(f"{rel}: unsupported diagram header {first!r}")

diagram_docs = sorted((DOCS / "diagrams").glob("*.md"))
for path in diagram_docs:
    if path.name.lower() == "readme.md":
        continue
    if "```mermaid" not in path.read_text(encoding="utf-8"):
        errors.append(f"{path.relative_to(DOCS.parent)}: no Mermaid block")

if errors:
    print("\n".join(errors))
    raise SystemExit(1)

print(f"Validated Mermaid in {len(files)} Markdown files.")
