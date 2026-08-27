# Mermaid diagrams

Diagram sources are Markdown files with embedded Mermaid code blocks, cross-linked from
the engineering documents. They are the single source of truth for the pictures in this
repo.

## Index

| # | Diagram | Type |
| --- | --- | --- |
| 01 | [System architecture](01-system-architecture.md) | flowchart |
| 02 | [User investigation workflow](02-user-investigation-workflow.md) | flowchart |
| 03 | [Evidence lifecycle](03-evidence-lifecycle.md) | flowchart |
| 04 | [Authentication and authorization flow](04-authentication-authorization-flow.md) | sequence |
| 05 | [Processing-job sequence](05-processing-job-sequence.md) | sequence |
| 06 | [Provenance chain](06-provenance-chain.md) | flowchart |
| 07 | [Chain-of-custody event flow](07-chain-of-custody-event-flow.md) | flowchart |
| 08 | [Case permission model](08-case-permission-model.md) | flowchart |
| 09 | [Report-generation flow](09-report-generation-flow.md) | flowchart |
| 10 | [Deployment topology](10-deployment-topology.md) | flowchart |
| 11 | [V0.1 scope boundary](11-v0.1-scope-boundary.md) | flowchart |
| 12 | [Future expansion roadmap](12-future-expansion-roadmap.md) | flowchart |

## Validation

```bash
python scripts/validate_mermaid.py
```

The validator checks every `docs/**/*.md` file for a supported diagram header
(`flowchart`, `sequenceDiagram`, `stateDiagram-v2`, `gantt`, `graph`, `erDiagram`) and
a **balanced closing fence** for each block. SVG/PNG export is deferred until Mermaid CLI
is part of the toolchain; GitHub renders the source blocks directly.
