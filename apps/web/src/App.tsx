import { FormEvent, ReactNode, useEffect, useMemo, useState } from "react";
import {
  Link,
  Route,
  Routes,
  useLocation,
  useNavigate,
  useParams,
} from "react-router-dom";
import {
  api,
  Artifact,
  Case,
  Evidence,
  Finding,
  Report,
  TimelineEvent,
  User,
} from "./api";

const statusLabels: Record<string, string> = {
  unverified: "Unverified",
  verified: "Verified",
  mismatch: "Hash mismatch",
  unreadable: "Unreadable",
  not_started: "Not started",
  queued: "Processing queued",
  running: "Processing",
  succeeded: "Processed",
  failed: "Processing failed",
};
const stateClass = (value: string) => value.replaceAll("_", "-");

function Login({ onLogin }: { onLogin: (user: User) => void }) {
  const [username, setUsername] = useState("admin@example.test");
  const [password, setPassword] = useState("ChangeMe-V0.1-only");
  const [error, setError] = useState("");
  async function submit(event: FormEvent) {
    event.preventDefault();
    try {
      onLogin(await api.login(username, password));
    } catch (err) {
      setError((err as Error).message);
    }
  }
  return (
    <main className="login">
      <div className="login-card">
        <span className="eyebrow">P.R.O.V.E / V0.1</span>
        <h1>Investigation workspace</h1>
        <p className="muted">
          Evidence-backed review from registered source to development report
          draft.
        </p>
        <form onSubmit={submit}>
          <label>
            Username
            <input
              aria-label="Username"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
            />
          </label>
          <label>
            Password
            <input
              aria-label="Password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </label>
          {error && (
            <div className="alert danger" role="alert">
              {error}
            </div>
          )}
          <button type="submit">Sign in</button>
        </form>
        <small>
          Development demo credentials are prefilled. Synthetic data only.
        </small>
      </div>
    </main>
  );
}

function App() {
  const [user, setUser] = useState<User | null>(null);
  useEffect(() => {
    api
      .me()
      .then(setUser)
      .catch(() => undefined);
  }, []);
  if (!user) return <Login onLogin={setUser} />;
  return (
    <Routes>
      <Route
        path="*"
        element={
          <AuthenticatedRoutes
            user={user}
            onLogout={async () => {
              await api.logout();
              setUser(null);
            }}
          />
        }
      />
    </Routes>
  );
}

function AuthenticatedRoutes({
  user,
  onLogout,
}: {
  user: User;
  onLogout: () => void;
}) {
  return (
    <Routes>
      <Route
        path="/"
        element={<CaseListPage user={user} onLogout={onLogout} />}
      />
      <Route
        path="/cases/:caseId/*"
        element={<CaseWorkspacePage user={user} onLogout={onLogout} />}
      />
    </Routes>
  );
}

function Header({ user, onLogout }: { user: User; onLogout: () => void }) {
  return (
    <header>
      <Link to="/" className="brand">
        <span className="eyebrow">P.R.O.V.E</span>
        <strong>Investigation workspace</strong>
      </Link>
      <div className="identity">
        <span>
          {user.displayName || user.username}
          <small>{user.role}</small>
        </span>
        <button className="secondary" onClick={onLogout}>
          Sign out
        </button>
      </div>
    </header>
  );
}

function CaseListPage({
  user,
  onLogout,
}: {
  user: User;
  onLogout: () => void;
}) {
  const [cases, setCases] = useState<Case[]>([]);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    reference: "CASE-0002",
    title: "",
    description: "",
  });
  const navigate = useNavigate();
  useEffect(() => {
    api
      .cases()
      .then(setCases)
      .catch((err) => setError(err.message));
  }, []);
  async function create(event: FormEvent) {
    event.preventDefault();
    try {
      const created = await api.createCase(form);
      setCases((current) => [created, ...current]);
      navigate(`/cases/${created.id}/overview`);
    } catch (err) {
      setError((err as Error).message);
    }
  }
  return (
    <div className="shell">
      <Header user={user} onLogout={onLogout} />
      <div className="case-list-layout">
        <aside>
          <div className="section-title">
            Cases <span className="count">{cases.length}</span>
          </div>
          {cases.map((item) => (
            <button
              className="case-item"
              key={item.id}
              onClick={() => navigate(`/cases/${item.id}/overview`)}
            >
              <strong>{item.reference}</strong>
              <span>{item.title}</span>
              <small>
                {item.evidence_count} evidence · {item.finding_count} findings
              </small>
            </button>
          ))}
          {!cases.length && <p className="muted">No cases available.</p>}
        </aside>
        <main className="content case-list">
          <span className="eyebrow">CASE REGISTER</span>
          <h1>Cases</h1>
          <p className="lede">
            Open a case to review integrity, processing, provenance, findings,
            and the report draft in one controlled workspace.
          </p>
          {error && (
            <div className="alert danger" role="alert">
              {error}
            </div>
          )}
          <form className="create-card" onSubmit={create}>
            <h2>Create case</h2>
            <div className="form-grid">
              <label>
                Case reference
                <input
                  required
                  value={form.reference}
                  onChange={(event) =>
                    setForm({ ...form, reference: event.target.value })
                  }
                />
              </label>
              <label>
                Case title
                <input
                  required
                  value={form.title}
                  onChange={(event) =>
                    setForm({ ...form, title: event.target.value })
                  }
                />
              </label>
              <label className="wide">
                Description
                <textarea
                  value={form.description}
                  onChange={(event) =>
                    setForm({ ...form, description: event.target.value })
                  }
                />
              </label>
            </div>
            <button type="submit">Create case</button>
          </form>
        </main>
      </div>
    </div>
  );
}

function CaseWorkspacePage({
  user,
  onLogout,
}: {
  user: User;
  onLogout: () => void;
}) {
  const { caseId } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const [caseRecord, setCaseRecord] = useState<Case | null>(null);
  const [evidence, setEvidence] = useState<Evidence[]>([]);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [reports, setReports] = useState<Report[]>([]);
  const [audit, setAudit] = useState<any[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const section =
    location.pathname.split("/").filter(Boolean).pop() || "overview";
  const load = async () => {
    if (!caseId) return;
    setLoading(true);
    try {
      const [c, e, a, t, f, r, h, globalHistory] = await Promise.all([
        api.caseDetail(caseId),
        api.evidence(caseId),
        api.artifacts(caseId),
        api.timeline(caseId),
        api.findings(caseId),
        api.reports(caseId),
        api.audit(caseId),
        api.globalAudit(),
      ]);
      setCaseRecord(c);
      setEvidence(e);
      setArtifacts(a);
      setTimeline(t);
      setFindings(f);
      setReports(r);
      setAudit([...globalHistory, ...h]);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    load();
  }, [caseId]);
  if (loading)
    return (
      <div className="shell">
        <Header user={user} onLogout={onLogout} />
        <main className="loading-state">
          <span className="spinner" />
          Loading case workspace…
        </main>
      </div>
    );
  if (!caseRecord)
    return (
      <div className="shell">
        <Header user={user} onLogout={onLogout} />
        <main className="empty">
          <h2>Case unavailable</h2>
          <p className="muted">
            This case may not exist or you may not have permission to view it.
          </p>
          <Link className="button" to="/">
            Return to cases
          </Link>
        </main>
      </div>
    );
  const tabs = [
    "overview",
    "evidence",
    "artifacts",
    "timeline",
    "findings",
    "report",
    "audit",
  ];
  return (
    <div className="shell">
      <Header user={user} onLogout={onLogout} />
      {error && (
        <div className="alert danger global" role="alert">
          {error}
          <button className="link" onClick={() => setError("")}>
            Dismiss
          </button>
        </div>
      )}
      <div className="workspace-layout">
        <aside className="case-sidebar">
          <Link to="/" className="back-link">
            ← All cases
          </Link>
          <span className="eyebrow">CASE / {caseRecord.reference}</span>
          <h2>{caseRecord.title}</h2>
          <span className="status">{caseRecord.status}</span>
          <nav aria-label="Case sections">
            {tabs.map((tab) => (
              <button
                key={tab}
                className={section === tab ? "nav-item active" : "nav-item"}
                onClick={() => navigate(`/cases/${caseRecord.id}/${tab}`)}
              >
                {tab === "overview"
                  ? "Overview"
                  : tab[0].toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </nav>
          <div className="synthetic-note">
            <strong>☑ Synthetic case</strong>
            <span>Development fixtures only. Not court-ready.</span>
          </div>
        </aside>
        <main className="content workspace-content">
          {section === "overview" && (
            <Overview
              caseRecord={caseRecord}
              evidence={evidence}
              artifacts={artifacts}
              findings={findings}
              timeline={timeline}
            />
          )}
          {section === "evidence" && (
            <EvidenceView
              caseId={caseRecord.id}
              evidence={evidence}
              onRefresh={load}
              onError={setError}
            />
          )}
          {section === "artifacts" && (
            <ArtifactView
              caseId={caseRecord.id}
              artifacts={artifacts}
              onError={setError}
            />
          )}
          {section === "timeline" && (
            <TimelineView
              caseId={caseRecord.id}
              initial={timeline}
              onError={setError}
            />
          )}
          {section === "findings" && (
            <FindingsView
              caseId={caseRecord.id}
              findings={findings}
              artifacts={artifacts}
              timeline={timeline}
              onRefresh={load}
              onError={setError}
            />
          )}
          {section === "report" && (
            <ReportView
              caseId={caseRecord.id}
              reports={reports}
              onRefresh={load}
              onError={setError}
            />
          )}
          {section === "audit" && <AuditView events={audit} />}
        </main>
      </div>
    </div>
  );
}

function Overview({
  caseRecord,
  evidence,
  artifacts,
  findings,
  timeline,
}: {
  caseRecord: Case;
  evidence: Evidence[];
  artifacts: Artifact[];
  findings: Finding[];
  timeline: TimelineEvent[];
}) {
  return (
    <>
      <div className="page-heading">
        <div>
          <span className="eyebrow">CASE OVERVIEW</span>
          <h1>
            {caseRecord.reference} · {caseRecord.title}
          </h1>
          <p>{caseRecord.description || "No case description recorded."}</p>
        </div>
        <span className="status">{caseRecord.status}</span>
      </div>
      <div className="notice">
        <strong>Progressive detail</strong>
        <span>
          Start with the evidence state. Open detail views when you need the
          hash, processor, provenance, or custody record.
        </span>
      </div>
      <div className="metric-grid">
        <Metric label="Evidence items" value={evidence.length} />
        <Metric
          label="Verified"
          value={
            evidence.filter((item) => item.verification_status === "verified")
              .length
          }
        />
        <Metric label="Artifacts" value={artifacts.length} />
        <Metric label="Timeline events" value={timeline.length} />
        <Metric label="Findings" value={findings.length} />
      </div>
      <section className="panel workflow-card">
        <div className="panel-head">
          <h2>Investigator workflow</h2>
          <span className="muted">
            Source trace remains visible at every step.
          </span>
        </div>
        <div className="workflow-steps">
          {[
            "Register evidence",
            "Verify integrity",
            "Process",
            "Inspect provenance",
            "Create finding",
            "Preview report",
          ].map((step, index) => (
            <div className="workflow-step" key={step}>
              <span>{String(index + 1).padStart(2, "0")}</span>
              <strong>{step}</strong>
              <small>
                {index === 0
                  ? `${evidence.length} registered`
                  : index === 1
                    ? `${evidence.filter((item) => item.verification_status === "verified").length} verified`
                    : index === 2
                      ? `${artifacts.length} artifacts`
                      : index === 3
                        ? "Traceable links"
                        : index === 4
                          ? `${findings.length} drafts`
                          : "Development draft"}
              </small>
            </div>
          ))}
        </div>
      </section>
    </>
  );
}
function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function EvidenceView({
  caseId,
  evidence,
  onRefresh,
  onError,
}: {
  caseId: string;
  evidence: Evidence[];
  onRefresh: () => Promise<void>;
  onError: (message: string) => void;
}) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<Evidence | null>(null);
  const [form, setForm] = useState({ display_name: "", original_path: "" });
  const [saving, setSaving] = useState(false);
  async function open(id: string) {
    try {
      setDetail(await api.evidenceDetail(id));
      setSelectedId(id);
    } catch (err) {
      onError((err as Error).message);
    }
  }
  async function register(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    try {
      await api.registerEvidence(caseId, {
        ...form,
        evidence_type: "synthetic_file",
        is_synthetic: true,
        acquisition_metadata: { source: "operator", synthetic: true },
      });
      setForm({ display_name: "", original_path: "" });
      await onRefresh();
    } catch (err) {
      onError((err as Error).message);
    } finally {
      setSaving(false);
    }
  }
  async function verify(id: string) {
    try {
      await api.verify(id);
      await onRefresh();
      await open(id);
    } catch (err) {
      onError((err as Error).message);
    }
  }
  async function process(id: string) {
    try {
      await api.submitJob(caseId, id);
      await onRefresh();
      await open(id);
    } catch (err) {
      onError((err as Error).message);
    }
  }
  return (
    <>
      <PageHeading
        eyebrow="EVIDENCE REGISTER"
        title="Registered evidence"
        description="Integrity and processing state are shown separately. Original evidence is never uploaded or modified."
      />
      <div className="notice warning">
        <strong>Hash mismatch blocks processing</strong>
        <span>
          Only verified evidence can enter the processing queue. Unreadable
          sources remain visible as failures.
        </span>
      </div>
      <div className="evidence-layout">
        <section className="panel">
          <div className="panel-head">
            <h2>Evidence register</h2>
            <span className="count">{evidence.length}</span>
          </div>
          {!evidence.length && (
            <EmptyState
              title="No evidence registered"
              text="Register a synthetic source reference to begin."
            />
          )}
          {evidence.map((item) => (
            <div
              className={`evidence-row ${selectedId === item.id ? "selected" : ""}`}
              key={item.id}
            >
              <button className="record-main" onClick={() => open(item.id)}>
                <strong>{item.display_name}</strong>
                <small>
                  {item.evidence_type} · {item.synthetic_label}
                </small>
                <small>{item.original_path}</small>
              </button>
              <span className={`badge ${stateClass(item.verification_status)}`}>
                {statusLabels[item.verification_status]}
              </span>
              <span className={`badge ${stateClass(item.processing_status)}`}>
                {statusLabels[item.processing_status]}
              </span>
              <button
                className="secondary small-button"
                onClick={() => open(item.id)}
              >
                Details
              </button>
            </div>
          ))}
        </section>
        {detail ? (
          <EvidenceDetailPanel
            detail={detail}
            onVerify={verify}
            onProcess={process}
          />
        ) : (
          <form className="panel create-card" onSubmit={register}>
            <h2>Register synthetic evidence</h2>
            <p className="muted">
              This is a source reference, not a general-purpose upload flow.
            </p>
            <label>
              Display name
              <input
                required
                value={form.display_name}
                onChange={(event) =>
                  setForm({ ...form, display_name: event.target.value })
                }
              />
            </label>
            <label>
              Original path or logical source
              <input
                required
                value={form.original_path}
                onChange={(event) =>
                  setForm({ ...form, original_path: event.target.value })
                }
              />
            </label>
            <button disabled={saving}>
              {saving ? "Registering…" : "Register evidence"}
            </button>
          </form>
        )}
      </div>
    </>
  );
}
function EvidenceDetailPanel({
  detail,
  onVerify,
  onProcess,
}: {
  detail: Evidence;
  onVerify: (id: string) => void;
  onProcess: (id: string) => void;
}) {
  const blocked = detail.verification_status !== "verified";
  return (
    <section className="panel detail-panel">
      <div className="panel-head">
        <div>
          <span className="eyebrow">EVIDENCE DETAIL</span>
          <h2>{detail.display_name}</h2>
        </div>
        <span className={`badge ${stateClass(detail.verification_status)}`}>
          {statusLabels[detail.verification_status]}
        </span>
      </div>
      <dl className="detail-list">
        <dt>Type</dt>
        <dd>{detail.evidence_type}</dd>
        <dt>Source reference</dt>
        <dd>{detail.original_path}</dd>
        <dt>Registered</dt>
        <dd>
          {new Date(detail.registered_at).toLocaleString()} by{" "}
          {detail.registered_by_name}
        </dd>
        <dt>Hash algorithm</dt>
        <dd>{detail.hash_algorithm}</dd>
        <dt>Expected hash</dt>
        <dd className="mono">{detail.expected_hash || "Not supplied"}</dd>
        <dt>Calculated hash</dt>
        <dd className="mono">{detail.calculated_hash || "Not calculated"}</dd>
        <dt>Read-only</dt>
        <dd>{detail.read_only ? "Yes" : "No"}</dd>
        <dt>Processing</dt>
        <dd>
          <span className={`badge ${stateClass(detail.processing_status)}`}>
            {statusLabels[detail.processing_status]}
          </span>
        </dd>
      </dl>
      {detail.warnings?.length > 0 && (
        <div className="subtle-warning">
          <strong>Warnings</strong>
          <ul>
            {detail.warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </div>
      )}
      {detail.limitations?.length > 0 && (
        <div className="subtle-warning">
          <strong>Limitations</strong>
          <ul>
            {detail.limitations.map((limitation) => (
              <li key={limitation}>{limitation}</li>
            ))}
          </ul>
        </div>
      )}
      <div className="button-row">
        <button className="secondary" onClick={() => onVerify(detail.id)}>
          Verify integrity
        </button>
        <button
          onClick={() => onProcess(detail.id)}
          disabled={blocked}
          title={
            blocked
              ? "Verify integrity successfully before processing"
              : "Start basic metadata processing"
          }
        >
          Start processing
        </button>
      </div>
      {blocked && (
        <p className="muted">
          Processing is unavailable until this evidence is verified
          successfully.
        </p>
      )}
    </section>
  );
}

function ArtifactView({
  caseId,
  artifacts,
  onError,
}: {
  caseId: string;
  artifacts: Artifact[];
  onError: (message: string) => void;
}) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState(artifacts);
  const [detail, setDetail] = useState<Artifact | null>(null);
  const [chain, setChain] = useState<any>(null);
  useEffect(() => setResults(artifacts), [artifacts]);
  async function search(event: FormEvent) {
    event.preventDefault();
    try {
      setResults(await api.artifacts(caseId, query));
    } catch (err) {
      onError((err as Error).message);
    }
  }
  async function open(id: string) {
    try {
      const [a, c] = await Promise.all([
        api.artifact(id),
        api.artifactProvenance(id),
      ]);
      setDetail(a);
      setChain(c);
    } catch (err) {
      onError((err as Error).message);
    }
  }
  return (
    <>
      <PageHeading
        eyebrow="ARTIFACTS"
        title="Normalized artifacts"
        description="Basic metadata is a normalized observation, not complete forensic parsing."
      />
      <div className="artifact-layout">
        <section className="panel">
          <div className="panel-head">
            <h2>Artifact results</h2>
            <span className="count">{results.length}</span>
          </div>
          <form className="inline-form" onSubmit={search}>
            <input
              aria-label="Search artifacts"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search name, type, or source"
            />
            <button>Search</button>
          </form>
          {!results.length && (
            <EmptyState
              title={query ? "No results" : "No artifacts yet"}
              text={
                query
                  ? "Try a different source or artifact term."
                  : "Process verified evidence to create normalized artifacts."
              }
            />
          )}{" "}
          {results.map((artifact) => (
            <button
              className="artifact-row"
              key={artifact.id}
              onClick={() => open(artifact.id)}
            >
              <span>
                <strong>
                  {String(artifact.content?.name || artifact.artifact_type)}
                </strong>
                <small>
                  {artifact.artifact_type} · {artifact.processing_status}
                </small>
              </span>
              <span className="badge normalized">Open detail</span>
            </button>
          ))}
        </section>
        {detail ? (
          <ArtifactDetailPanel detail={detail} chain={chain} />
        ) : (
          <div className="panel empty-panel">
            <span className="empty-icon">⌁</span>
            <h2>Select an artifact</h2>
            <p className="muted">
              The detail view shows processor, source hash, timeline, findings,
              and the provenance chain.
            </p>
          </div>
        )}
      </div>
    </>
  );
}
function ArtifactDetailPanel({
  detail,
  chain,
}: {
  detail: Artifact;
  chain: any;
}) {
  const source =
    typeof detail.source_evidence === "string"
      ? detail.source_evidence
      : detail.source_evidence.display_name;
  return (
    <section className="panel detail-panel">
      <span className="eyebrow">ARTIFACT DETAIL</span>
      <h2>{String(detail.content?.name || detail.artifact_type)}</h2>
      <span className="badge normalized">Normalized interpretation</span>
      <dl className="detail-list">
        <dt>Artifact type</dt>
        <dd>{detail.artifact_type}</dd>
        <dt>Content</dt>
        <dd>
          <pre className="json-block">
            {JSON.stringify(detail.content, null, 2)}
          </pre>
        </dd>
        <dt>Source evidence</dt>
        <dd>{source}</dd>
        <dt>Source path</dt>
        <dd>{detail.source_path}</dd>
        <dt>Source hash reference</dt>
        <dd className="mono">{detail.source_hash_reference}</dd>
        <dt>Processor</dt>
        <dd>
          {detail.processor_name} v{detail.processor_version}
        </dd>
        <dt>Processing timestamp</dt>
        <dd>{new Date(detail.processing_timestamp).toLocaleString()}</dd>
      </dl>
      <h3>Provenance chain</h3>
      <div className="provenance-chain">
        <span>Examiner finding</span>
        <b>↓</b>
        <span>Timeline event</span>
        <b>↓</b>
        <span>Artifact</span>
        <b>↓</b>
        <span>Processing run</span>
        <b>↓</b>
        <span>Original evidence</span>
        <b>↓</b>
        <span>Hash and custody</span>
      </div>
      {chain?.timeline_events?.map((event: TimelineEvent) => (
        <div className="mini-record" key={event.id}>
          <strong>{event.event_type}</strong>
          <span>{event.summary}</span>
          <small>{event.interpretation_status}</small>
        </div>
      ))}
      {detail.limitations?.length > 0 && (
        <div className="subtle-warning">
          <strong>Limitations</strong>
          <ul>
            {detail.limitations.map((limitation) => (
              <li key={limitation}>{limitation}</li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}

function TimelineView({
  caseId,
  initial,
  onError,
}: {
  caseId: string;
  initial: TimelineEvent[];
  onError: (message: string) => void;
}) {
  const [events, setEvents] = useState(initial);
  const [eventType, setEventType] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const types = useMemo(
    () => [...new Set(initial.map((event) => event.event_type))],
    [initial],
  );
  async function filter(event: FormEvent) {
    event.preventDefault();
    try {
      setEvents(
        await api.timeline(caseId, {
          ...(eventType ? { event_type: eventType } : {}),
          ...(dateFrom ? { from: dateFrom } : {}),
          ...(dateTo ? { to: dateTo } : {}),
        }),
      );
    } catch (err) {
      onError((err as Error).message);
    }
  }
  return (
    <>
      <PageHeading
        eyebrow="TIMELINE"
        title="Basic timeline"
        description="Chronological events are shown with their source artifact and interpretation status."
      />
      <section className="panel">
        <form className="filter-row" onSubmit={filter}>
          <label>
            Event type
            <select
              value={eventType}
              onChange={(event) => setEventType(event.target.value)}
            >
              <option value="">All event types</option>
              {types.map((type) => (
                <option key={type}>{type}</option>
              ))}
            </select>
          </label>
          <label>
            From
            <input
              type="datetime-local"
              value={dateFrom}
              onChange={(event) => setDateFrom(event.target.value)}
            />
          </label>
          <label>
            To
            <input
              type="datetime-local"
              value={dateTo}
              onChange={(event) => setDateTo(event.target.value)}
            />
          </label>
          <button>Filter</button>
        </form>
        {!events.length && (
          <EmptyState
            title={
              eventType || dateFrom || dateTo
                ? "No timeline results"
                : "No timeline events"
            }
            text="Broaden the filters or process verified evidence."
          />
        )}
        {events.map((event) => (
          <div className="timeline-row" key={event.id}>
            <time>{new Date(event.observed_at).toLocaleString()}</time>
            <div>
              <strong>{event.event_type}</strong>
              <p>{event.summary}</p>
              <small>
                {event.interpretation_status} · source artifact{" "}
                {event.artifact || "not linked"}
              </small>
            </div>
          </div>
        ))}
      </section>
    </>
  );
}

function FindingsView({
  caseId,
  findings,
  artifacts,
  timeline,
  onRefresh,
  onError,
}: {
  caseId: string;
  findings: Finding[];
  artifacts: Artifact[];
  timeline: TimelineEvent[];
  onRefresh: () => Promise<void>;
  onError: (message: string) => void;
}) {
  const [text, setText] = useState("");
  const [basis, setBasis] = useState("observed");
  const [selected, setSelected] = useState<Finding | null>(null);
  const [supportType, setSupportType] = useState("artifact");
  const [supportId, setSupportId] = useState("");
  async function create(event: FormEvent) {
    event.preventDefault();
    if (!text.trim()) return;
    try {
      await api.createFinding(caseId, {
        finding_text: text,
        finding_basis: basis,
      });
      setText("");
      await onRefresh();
    } catch (err) {
      onError((err as Error).message);
    }
  }
  async function attach(event: FormEvent) {
    event.preventDefault();
    if (!selected || !supportId) return;
    try {
      await api.addSupport(
        selected.id,
        supportType === "artifact"
          ? { artifact: supportId }
          : { timeline_event: supportId },
      );
      const refreshed = await api.finding(selected.id);
      setSelected(refreshed);
      await onRefresh();
    } catch (err) {
      onError((err as Error).message);
    }
  }
  return (
    <>
      <PageHeading
        eyebrow="FINDINGS"
        title="Examiner findings"
        description="Findings remain examiner-controlled. Every draft should carry an explicit support reference before report generation."
      />
      <div className="findings-layout">
        <section className="panel">
          <div className="panel-head">
            <h2>Create finding</h2>
            <span className="badge draft">Draft by default</span>
          </div>
          <form onSubmit={create}>
            <label>
              Finding text
              <textarea
                aria-label="Finding text"
                required
                value={text}
                onChange={(event) => setText(event.target.value)}
                placeholder="Describe what the evidence supports without adding an autonomous conclusion."
              />
            </label>
            <label>
              Basis
              <select
                value={basis}
                onChange={(event) => setBasis(event.target.value)}
              >
                <option value="observed">Observed evidence</option>
                <option value="interpreted">Normalized interpretation</option>
              </select>
            </label>
            <button>Create draft finding</button>
          </form>
          <div className="finding-list">
            {!findings.length && (
              <EmptyState
                title="No findings"
                text="A finding is a human-authored statement, not a machine conclusion."
              />
            )}
            {findings.map((finding) => (
              <button
                className={`finding-row ${selected?.id === finding.id ? "selected" : ""}`}
                key={finding.id}
                onClick={() => {
                  setSelected(finding);
                  setSupportId("");
                }}
              >
                <span className="badge draft">{finding.examiner_status}</span>
                <span>
                  <strong>{finding.finding_text}</strong>
                  <small>
                    {finding.finding_basis} · {finding.support_count || 0}{" "}
                    support references
                  </small>
                </span>
              </button>
            ))}
          </div>
        </section>
        {selected ? (
          <section className="panel detail-panel">
            <span className="eyebrow">FINDING REVIEW</span>
            <h2>Support references</h2>
            {(!selected.support_count || selected.support_count === 0) && (
              <div className="alert warning" role="status">
                This finding has no supporting evidence. Attach an artifact or
                timeline event before relying on it in a report.
              </div>
            )}
            <p>{selected.finding_text}</p>
            <form className="inline-form" onSubmit={attach}>
              <select
                aria-label="Support type"
                value={supportType}
                onChange={(event) => {
                  setSupportType(event.target.value);
                  setSupportId("");
                }}
              >
                <option value="artifact">Artifact</option>
                <option value="timeline">Timeline event</option>
              </select>
              <select
                aria-label="Support reference"
                value={supportId}
                onChange={(event) => setSupportId(event.target.value)}
              >
                <option value="">Select support</option>
                {supportType === "artifact"
                  ? artifacts.map((artifact) => (
                      <option value={artifact.id} key={artifact.id}>
                        {String(
                          artifact.content?.name || artifact.artifact_type,
                        )}
                      </option>
                    ))
                  : timeline.map((event) => (
                      <option value={event.id} key={event.id}>
                        {event.event_type} · {event.summary}
                      </option>
                    ))}
              </select>
              <button disabled={!supportId}>Attach support</button>
            </form>
            {selected.supports?.map((support) => (
              <div className="mini-record" key={support.id}>
                <strong>
                  {support.artifact ? "Artifact" : "Timeline event"}
                </strong>
                <span>{support.artifact || support.timeline_event}</span>
              </div>
            ))}
          </section>
        ) : (
          <div className="panel empty-panel">
            <h2>Select a finding to review</h2>
            <p className="muted">
              Review support relationships before creating a report draft.
            </p>
          </div>
        )}
      </div>
    </>
  );
}

function ReportView({
  caseId,
  reports,
  onRefresh,
  onError,
}: {
  caseId: string;
  reports: Report[];
  onRefresh: () => void;
  onError: (message: string) => void;
}) {
  const [report, setReport] = useState<Report | null>(reports[0] || null);
  async function generate() {
    try {
      const created = await api.createReport(
        caseId,
        "Development report preview",
      );
      setReport(created);
      onRefresh();
    } catch (err) {
      onError((err as Error).message);
    }
  }
  useEffect(() => {
    if (reports[0] && !report) setReport(reports[0]);
  }, [reports]);
  const body = report?.body;
  return (
    <>
      <PageHeading
        eyebrow="REPORT PREVIEW"
        title="Development report draft"
        description="A traceable snapshot for review. This is not a signed export or a court-readiness claim."
      />
      <div className="report-toolbar">
        <span className="badge draft">
          {report ? "Draft" : "Not generated"}
        </span>
        <button onClick={generate}>Generate report preview</button>
      </div>
      {!report ? (
        <div className="panel empty-panel">
          <h2>No report draft yet</h2>
          <p className="muted">
            Generate a draft after reviewing findings and support references.
          </p>
        </div>
      ) : (
        <article className="panel report-preview">
          <div className="report-title">
            <span className="eyebrow">DEVELOPMENT DRAFT</span>
            <h2>
              {body?.case?.reference} · {body?.case?.title}
            </h2>
            <p>{body?.draftNotice}</p>
          </div>
          <div className="alert warning">
            <strong>Synthetic-data warning</strong>
            <span>{body?.syntheticDataWarning}</span>
          </div>
          <div className="report-grid">
            <ReportSection title="Evidence register">
              <p>
                {body?.evidenceRegister?.length || 0} registered source items.
              </p>
              <p>
                Verified: {body?.integrityStatus?.verified || 0} · Mismatch:{" "}
                {body?.integrityStatus?.mismatch || 0} · Unreadable:{" "}
                {body?.integrityStatus?.unreadable || 0}
              </p>
            </ReportSection>
            <ReportSection title="Processing summary">
              <p>
                {body?.processingSummary?.jobs || 0} jobs ·{" "}
                {body?.processingSummary?.artifacts || 0} artifacts.
              </p>
            </ReportSection>
            <ReportSection title="Findings">
              <p>
                {body?.findings?.length || 0} examiner-authored findings
                included.
              </p>
              {body?.findings?.map((finding: any) => (
                <div className="mini-record" key={finding.id}>
                  <strong>{finding.finding_text || finding.text}</strong>
                  <small>
                    {finding.support_count ?? finding.supports?.length ?? 0}{" "}
                    support references
                  </small>
                </div>
              ))}
            </ReportSection>
            <ReportSection title="Provenance and timeline">
              <p>
                {body?.provenanceReferences?.length || 0} provenance links ·{" "}
                {body?.timelineReferences?.length || 0} timeline references.
              </p>
            </ReportSection>
            <ReportSection title="Audit summary">
              <p>{body?.auditSummary?.events || 0} recorded case events.</p>
            </ReportSection>
            <ReportSection title="Limitations">
              <ul>
                {(body?.limitations || ["No limitations recorded."]).map(
                  (item: string) => (
                    <li key={item}>{item}</li>
                  ),
                )}
              </ul>
            </ReportSection>
          </div>
        </article>
      )}
    </>
  );
}
function ReportSection({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <section className="report-section">
      <h3>{title}</h3>
      {children}
    </section>
  );
}

function AuditView({ events }: { events: any[] }) {
  return (
    <>
      <PageHeading
        eyebrow="AUDIT HISTORY"
        title="Case history"
        description="Append-only activity for the case. Sensitive evidence contents are never written to metadata."
      />
      <section className="panel audit-panel">
        {!events.length && (
          <EmptyState
            title="No audit events"
            text="Material case actions will appear here."
          />
        )}
        {events.map((event) => (
          <div className="audit-row" key={event.id}>
            <div>
              <strong>{event.action}</strong>
              <small>
                {event.actor_name || event.actor || "System"} ·{" "}
                {event.object_type} · {event.object_id || "—"}
              </small>
            </div>
            <time>{new Date(event.created_at).toLocaleString()}</time>
            <pre>{JSON.stringify(event.metadata || {})}</pre>
          </div>
        ))}
      </section>
    </>
  );
}
function PageHeading({
  eyebrow,
  title,
  description,
}: {
  eyebrow: string;
  title: string;
  description: string;
}) {
  return (
    <div className="page-heading">
      <span className="eyebrow">{eyebrow}</span>
      <h1>{title}</h1>
      <p>{description}</p>
    </div>
  );
}
function EmptyState({ title, text }: { title: string; text: string }) {
  return (
    <div className="empty-state">
      <h3>{title}</h3>
      <p className="muted">{text}</p>
    </div>
  );
}

export { Login };
export default App;
