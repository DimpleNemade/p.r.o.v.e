<div align="center">

# P.R.O.V.E

**Provenance-first digital forensic investigation platform**

*From acquired evidence to a defensible finding — without ever losing the thread back to the source.*

![status](https://img.shields.io/badge/status-V0.1%20foundation-orange)
![python](https://img.shields.io/badge/python-3.12%2B-3776AB)
![node](https://img.shields.io/badge/node-20%2B-3C873A)
![api](https://img.shields.io/badge/API-Django%205.1%20%2B%20DRF-092E20)
![web](https://img.shields.io/badge/web-React%2018%20%2B%20Vite-61DAFB)
![license](https://img.shields.io/badge/license-All%20rights%20reserved-lightgrey)

</div>

---

P.R.O.V.E is one workspace that carries a digital investigation through its whole arc — register evidence, verify its integrity, process it, review what came out, write findings, and produce a report — while keeping **every artifact, timeline entry, finding, and sentence in the report linked to the evidence it came from, the processing that produced it, and the examiner who decided about it.**

It is an early, honest **V0.1 foundation**: the workflow, data model, API, web interface, and worker boundary all exist and are exercised by tests, but the deep parsers, acquisition integrations, and formal validation do not. It is **not court-ready and not forensically validated.** See the [disclaimer](#disclaimer).

## Why I built this

I spent time in the Cyber Cell of a state Forensic Science Laboratory in India, imaging hard drives and phones, holding chain-of-custody discipline, and writing the technical reports that went on to be used in court. Later, during my MSc in Cybersecurity and Forensics, I built a lightweight forensic triage tool for my dissertation and lived the reproducibility problem from the other side.

The same friction showed up everywhere. The heavy tools — imagers, parsers, carvers — are genuinely good at what they do. But at the end of every case a human still sits down and stitches together exports from four or five different tools into a single story that a reviewer has to be able to *trust and reproduce*. Provenance and chain of custody were things we maintained by hand and by habit, in spreadsheets and notes, not something the tooling enforced. When a reviewer asked "where exactly did this line in the report come from?", answering it was manual archaeology.

P.R.O.V.E is the workspace I wanted then: put provenance first, make traceability the default instead of the chore, and keep the examiner — not the automation — in control of every conclusion.

## The problem

- **Fragmented outputs.** Evidence goes through several specialised tools; each produces its own format. Correlating them into one coherent picture is slow, manual, and error-prone.
- **Provenance is an afterthought.** Most workflows can *show* you an artifact but can't cheaply prove the chain from that artifact back to a specific offset in a specific verified image, through a named parser at a named version.
- **Observation and interpretation blur together.** "The file existed" and "the suspect downloaded the file" get recorded the same way, and the distinction has to be reconstructed later.
- **Reproducibility is expensive.** A second examiner should be able to rerun the method and get materially the same result. In practice that often means re-doing the work from scratch.

## What P.R.O.V.E does

One connected workspace for the core investigation loop, with an append-only audit trail underneath it. The name is the pipeline:

| | Stage | In the platform |
|---|---|---|
| **P** | **Provenance** | every artifact and finding links back to source evidence, processor, version, and actor — as first-class records, not UI decoration |
| **R** | **Register** | evidence intake, SHA-256 hashing, and an append-only chain of custody |
| **O** | **Observe** | normalized artifacts, explicitly marked as *observations* rather than conclusions |
| **V** | **Verify** | integrity checking at registration and on demand; a hash mismatch is **blocking and visible**, never silent |
| **E** | **Examine** | examiner findings with review states, supporting-evidence links, report drafts, and a controlled export package |

Everything an examiner does — register, verify, process, conclude, export — is written to an audit trail that the application never lets you quietly rewrite.

## Who it's for

- **Digital forensic practitioners** who want the narrative-assembly and provenance layer without a six-figure suite.
- **Reviewers and QA** who need to reach the source behind any finding and see the method and its limitations.
- **Students and trainees** learning a disciplined workflow on synthetic or authorised evidence.
- **Small labs and researchers** who want an open, self-hostable base where evidence never leaves the environment.

### What it deliberately is *not*

It does not replace acquisition hardware or validated imaging tools. It does not do mobile, cloud, memory, or network forensics. It does not reach broad parser coverage. It does not draw autonomous conclusions or sign off reports. It makes no claim of legal admissibility or "court-ready" status. Those boundaries are intentional and documented in [`docs/02-v0.1-scope.md`](docs/02-v0.1-scope.md).

## Architecture

A modular monolith for the case workflow, with processing pushed to a separate worker so that untrusted evidence is handled at arm's length.

```mermaid
flowchart TB
    subgraph Client
      UI["React + TypeScript SPA<br/>investigator workspace"]
      Desktop["Tauri 2 shell<br/>optional · restricted permissions"]
    end

    subgraph Server["API — Django + DRF"]
      Auth["Session auth + CSRF<br/>case-level authorization"]
      Core["Cases · Evidence · Processing<br/>Artifacts · Findings · Reports"]
      Ledger["Append-only ledger<br/>audit · custody · provenance"]
    end

    subgraph Processing
      Queue["Celery + Redis<br/>eager mode for local dev"]
      Worker["Forensic worker<br/>SHA-256 · metadata · provenance"]
    end

    DB[("PostgreSQL / SQLite")]
    Evidence[["Read-only evidence source"]]

    Desktop --> UI
    UI -->|REST over session cookie| Auth
    Auth --> Core --> Ledger
    Core -->|enqueue job| Queue --> Worker
    Worker -->|read-only hash + inspect| Evidence
    Worker -->|artifacts + provenance links| Core
    Core --- DB
    Ledger --- DB
```

The worker never writes to original evidence and never logs raw evidence contents. Search and any future index are treated as derived and rebuildable; the database is the authoritative record.

## The investigation workflow

```mermaid
flowchart LR
    A["Create case"] --> B["Register evidence<br/>+ chain of custody"]
    B --> C{"Verify SHA-256"}
    C -->|match| D["Start processing job"]
    C -->|mismatch| X["Blocked<br/>recorded in custody + audit"]
    D --> E["Normalized artifacts<br/>marked as observations"]
    E --> F["Search artifacts"]
    F --> G["Inspect provenance<br/>artifact to source evidence"]
    G --> H["Create examiner finding<br/>+ attach supporting evidence"]
    H --> I["Generate report draft"]
    I --> J["Export auditable package"]

    B -.-> K[("Append-only audit trail")]
    D -.-> K
    H -.-> K
    I -.-> K
```

The full lifecycle, permission model, and provenance chain are drawn out in [`docs/diagrams/`](docs/diagrams/README.md).

## Try it in five minutes

The default development mode uses **SQLite** and runs processing **synchronously**, so you do not need PostgreSQL, Redis, or Docker to see the whole workflow.

### Prerequisites

| Tool | Version | Needed for |
|---|---|---|
| Python | 3.12+ | API + worker |
| Node.js | 20+ (22 recommended) | web app |
| Git | any recent | cloning |
| PostgreSQL + Redis | optional | team mode / async processing |
| Rust + Cargo | optional | desktop shell build |

### 1. Get the code

```bash
git clone https://github.com/DimpleNemade/p.r.o.v.e.git
cd p.r.o.v.e
```

### 2. Run the API

<details open>
<summary><b>macOS / Linux</b></summary>

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r apps/api/requirements.txt
cp .env.example .env
python apps/api/manage.py migrate
python apps/api/manage.py seed_demo
python apps/api/manage.py runserver
```

</details>

<details>
<summary><b>Windows — PowerShell</b></summary>

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r apps\api\requirements.txt
Copy-Item .env.example .env
python apps\api\manage.py migrate
python apps\api\manage.py seed_demo
python apps\api\manage.py runserver
```

If `npm` or scripts are blocked by execution policy, prefix with
`powershell.exe -ExecutionPolicy Bypass -File <script>` or use `npm.cmd`.

</details>

<details>
<summary><b>Windows — Command Prompt</b></summary>

```bat
py -3.12 -m venv .venv
.venv\Scripts\activate.bat
pip install -r apps\api\requirements.txt
copy .env.example .env
python apps\api\manage.py migrate
python apps\api\manage.py seed_demo
python apps\api\manage.py runserver
```

</details>

The API is now on `http://127.0.0.1:8000` (OpenAPI docs at `/api/docs/`).

### 3. Run the web app

In a second terminal:

```bash
cd apps/web
npm install
npm run dev
```

Open `http://localhost:5173` and sign in with the development demo account:

```
admin@example.test  /  ChangeMe-V0.1-only
```

### 4. Walk the workflow

The seed created a synthetic case, **`DEMO-0001`**, with one synthetic evidence file. From the workspace:

1. Open `DEMO-0001` and **Verify** the evidence — watch the SHA-256 and status update.
2. **Process** it — a normalized artifact, a timeline event, and a provenance link appear.
3. Open the **Provenance chain** panel and follow the artifact back to its source evidence.
4. Add a **draft finding** and generate a **report draft**.
5. Check **Audit history** — every step you just took is there, in order.

To see failure handling, the backend tests cover it directly: a deliberately wrong `expected_hash` makes verification report `mismatch`, and the processing job then fails and is recorded in both the custody and audit trails (`apps/api/cases/tests.py`).

### 5. Run the tests

```bash
# Backend API + provenance + audit tests (from repo root)
python apps/api/manage.py test

# Worker tests
python -m pytest services/forensic-worker/tests

# Frontend
cd apps/web && npm test

# Mermaid diagram sources
python scripts/validate_mermaid.py
```

Windows users have two convenience wrappers: `scripts/check_environment.ps1` (toolchain report) and `scripts/run_backend_tests.ps1` (API then worker tests).

### Optional: PostgreSQL + Redis (team mode)

```bash
docker compose -f infra/compose/docker-compose.yml up -d postgres redis
# in .env, set:
#   DATABASE_URL=postgresql://forensic:forensic@localhost:5432/forensic
#   CELERY_TASK_ALWAYS_EAGER=False
python apps/api/manage.py migrate
# then, from apps/api:
celery -A config worker -l INFO
```

### Optional: desktop shell

```bash
cd apps/desktop
npm install
npm run tauri dev   # requires Rust/Cargo + platform build tools
```

The Tauri shell just hosts the web UI with narrow permissions — no filesystem plugin, no bundled Python. The browser app is the supported path.

## Use cases

**Casework triage and narrative assembly.** Register the images you have, verify them, run the processors, and build the finding-by-finding story with each claim already wired to its source. The report draft is assembled *from* those linked findings, not typed separately.

**Training and education.** A safe place to teach the disciplined loop — verify before you process, separate what you observed from what you concluded, keep custody intact — on synthetic evidence, with the audit trail making mistakes visible and recoverable.

**Method and QA review.** A reviewer opens a finding, walks straight to the source artifact and the processing run behind it, sees the recorded limitations, and disagrees on the record — without needing database access or the original examiner's machine.

**Research substrate.** An open, readable base for experimenting with provenance models, canonical schemas (CASE/UCO-style), or wrapping mature engines (The Sleuth Kit, libewf, Plaso) behind auditable contracts.

## Where this fits

The forensic tooling landscape is mature where it counts. **Autopsy, X-Ways, EnCase, Magnet AXIOM, and Cellebrite** own acquisition and deep parsing. **Timesketch and Hansken** show what timeline analysis and collaboration look like at scale.

P.R.O.V.E is not trying to out-parse any of them. It aims at the layer above: the **provenance, review, and reporting fabric** that ties heterogeneous outputs together and keeps them defensible — designed from the first commit around traceability, examiner authority, and an append-only history, rather than having those bolted on. Open, self-hostable, and built so evidence and case data never have to leave your environment.

The long-term intent is to wrap trusted open engines behind stable contracts that capture input hashes, versions, parameters, outputs, and errors — so the platform gets parsing depth without becoming a black box.

## Tech stack

| Layer | Choice |
|---|---|
| API | Python 3.12, Django 5.1, Django REST Framework, drf-spectacular |
| Auth | Django sessions, CSRF, case-level permissions, custom user model with roles |
| Data | PostgreSQL (team) / SQLite (local dev) |
| Processing | Separate Python worker, Celery + Redis, synchronous mode for local dev |
| Web | React 18, TypeScript, Vite, custom CSS; Vitest + Testing Library + Playwright |
| Desktop | Tauri 2 shell (optional) |
| Docs | 18 engineering documents, 9 ADRs, 12 Mermaid diagrams with a validator |

Architecture rationale is recorded as ADRs in [`docs/decisions/`](docs/decisions/README.md).

## Repository layout

```
apps/
  api/         Django + DRF: identity, cases, evidence, processing,
               investigations, reporting, audit
  web/         React + TypeScript investigator workspace
  desktop/     Tauri 2 shell (optional)
services/
  forensic-worker/   dependency-light worker boundary + Celery task
infra/         PostgreSQL + Redis compose topology, API Dockerfile
docs/          engineering docs, ADRs, Mermaid diagram sources
scripts/       environment check, backend test runner, Mermaid validator
demo/          synthetic evidence fixture
```

## Security & evidence-handling posture

- Configuration is environment-based; secrets stay out of version control (`.env.example` holds placeholders only).
- Session authentication, CSRF protection, an explicit CORS allowlist, secure-cookie flags, and security headers.
- Case-level authorization on every endpoint; audit, custody, and provenance records are append-only through the application surface.
- Original evidence is read-only by policy. No API exposes raw evidence content. No raw evidence is written to logs.
- A hash mismatch stops processing and records a failure. Unsupported evidence is reported as a limitation, not silently parsed.
- No external AI calls are made.

Threat model and data-protection notes: [`docs/10-security-threat-model.md`](docs/10-security-threat-model.md), [`docs/11-data-protection-and-privacy.md`](docs/11-data-protection-and-privacy.md).

## Documentation

| Topic | Document |
|---|---|
| Programme overview | [`docs/00-programme-overview.md`](docs/00-programme-overview.md) |
| Product constitution | [`docs/01-product-constitution.md`](docs/01-product-constitution.md) |
| V0.1 scope and boundaries | [`docs/02-v0.1-scope.md`](docs/02-v0.1-scope.md) |
| System architecture | [`docs/03-system-architecture.md`](docs/03-system-architecture.md) |
| Domain model | [`docs/04-domain-model.md`](docs/04-domain-model.md) |
| Evidence lifecycle | [`docs/05-evidence-lifecycle.md`](docs/05-evidence-lifecycle.md) |
| Provenance & chain of custody | [`docs/06-provenance-and-chain-of-custody.md`](docs/06-provenance-and-chain-of-custody.md) |
| Auth & authorization | [`docs/07-authentication-and-authorization.md`](docs/07-authentication-and-authorization.md) |
| Processing jobs | [`docs/08-processing-jobs.md`](docs/08-processing-jobs.md) |
| API contract | [`docs/09-api-contract.md`](docs/09-api-contract.md) |
| Validation & testing | [`docs/12-validation-and-testing.md`](docs/12-validation-and-testing.md) |
| AI governance boundary | [`docs/14-ai-governance-boundary.md`](docs/14-ai-governance-boundary.md) |
| User workflows | [`docs/15-user-workflows.md`](docs/15-user-workflows.md) |
| Glossary | [`docs/16-glossary.md`](docs/16-glossary.md) |
| Architecture decisions | [`docs/decisions/README.md`](docs/decisions/README.md) |
| Diagrams | [`docs/diagrams/README.md`](docs/diagrams/README.md) |

## Disclaimer

This is a development and evaluation scaffold. It is **not court-ready, not production-forensic validated**, and not a substitute for validated acquisition and parsing tooling. Any operational or evidential use is the responsibility of the deploying organisation and requires its own validation, competence, and legal review. See [`LICENSE`](LICENSE).

## Author

**Dimple Nemade** — MSc Cybersecurity and Forensics (University of Westminster), with hands-on digital forensics experience from the Cyber Cell of a state Forensic Science Laboratory in India. P.R.O.V.E grew out of that casework: the conviction that provenance and reproducibility should be the default state of a forensic workspace, not the part you assemble by hand at the end.
