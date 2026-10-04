# Generated diagrams

`mermaid/` contains the SVG and PNG render of each Phase 3 diagram in
`docs/diagrams/19-phase3-trust-and-workflows.md`. Regenerate and validate them with:

```powershell
npm.cmd --prefix apps\web run diagrams:validate
```

The 2026-09-09 acceptance run source checked Mermaid in 64 Markdown files, parsed and
rendered all 8 Phase 3 diagrams, then visually inspected every PNG for readability and
clipping. The Markdown Mermaid blocks remain the editable source.
