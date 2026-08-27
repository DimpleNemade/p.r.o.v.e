from pathlib import Path
import re

root = Path(__file__).resolve().parents[1] / "docs" / "diagrams"
files = sorted(p for p in root.glob("*.md") if p.name.lower() != "readme.md")
errors = []
for path in files:
    text = path.read_text(encoding="utf-8")
    blocks = re.findall(r"```mermaid\s*\n(.*?)```", text, re.S)
    if not blocks:
        errors.append(f"{path}: no Mermaid block")
    for block in blocks:
        first = block.strip().splitlines()[0] if block.strip() else ""
        if not re.match(r"^(flowchart|sequenceDiagram|stateDiagram-v2|gantt|graph|erDiagram)\b", first):
            errors.append(f"{path}: unsupported diagram header {first!r}")
if errors:
    print("\n".join(errors)); raise SystemExit(1)
print(f"Validated {len(files)} Mermaid source documents.")
