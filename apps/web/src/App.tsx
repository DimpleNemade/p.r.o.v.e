import { FormEvent, useEffect, useState } from "react";
import { api, Case, Evidence, User } from "./api";

function Login({ onLogin }: { onLogin: (u: User) => void }) {
  const [username, setUsername] = useState("admin@example.test");
  const [password, setPassword] = useState("ChangeMe-V0.1-only");
  const [error, setError] = useState("");
  async function submit(e: FormEvent) {
    e.preventDefault();
    try {
      await api.csrf();
      onLogin(await api.login(username, password));
    } catch (err) {
      setError((err as Error).message);
    }
  }
  return (
    <main className="login">
      <div className="login-card">
        <span className="eyebrow">PROVENANCE-FIRST / V0.1</span>
        <h1>Investigation workspace</h1>
        <p className="muted">
          Move from acquired evidence to traceable findings with examiner
          control.
        </p>
        <form onSubmit={submit}>
          <label>
            Username
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          </label>
          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </label>
          {error && <div className="alert danger">{error}</div>}
          <button>Sign in</button>
        </form>
        <small>Development demo credentials are prefilled.</small>
      </div>
    </main>
  );
}

function App() {
  const [user, setUser] = useState<User | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    api
      .me()
      .then(setUser)
      .catch(() => undefined);
  }, []);
  if (!user) return <Login onLogin={setUser} />;
  return (
    <Workspace
      user={user}
      onLogout={async () => {
        await api.logout();
        setUser(null);
      }}
      error={error}
      setError={setError}
    />
  );
}

function Workspace({
  user,
  onLogout,
  error,
  setError,
}: {
  user: User;
  onLogout: () => void;
  error: string;
  setError: (s: string) => void;
}) {
  const [cases, setCases] = useState<Case[]>([]);
  const [selected, setSelected] = useState<Case | null>(null);
  const [evidence, setEvidence] = useState<Evidence[]>([]);
  const [artifacts, setArtifacts] = useState<any[]>([]);
  const [provenance, setProvenance] = useState<any[]>([]);
  const [findings, setFindings] = useState<any[]>([]);
  const [audit, setAudit] = useState<any[]>([]);
  const [jobs, setJobs] = useState<any[]>([]);
  const [query, setQuery] = useState("");
  const [findingText, setFindingText] = useState("");
  const [newCase, setNewCase] = useState({
    reference: "CASE-0002",
    title: "",
    description: "",
  });
  const load = async (c: Case) => {
    setSelected(c);
    try {
      const [e, a, p, f, h, j] = await Promise.all([
        api.evidence(c.id),
        api.artifacts(c.id),
        api.provenance(c.id),
        api.findings(c.id),
        api.audit(c.id),
        api.jobs(c.id),
      ]);
      setEvidence(e);
      setArtifacts(a);
      setProvenance(p);
      setFindings(f);
      setAudit(h);
      setJobs(j);
    } catch (e) {
      setError((e as Error).message);
    }
  };
  useEffect(() => {
    api
      .cases()
      .then(setCases)
      .catch((e) => setError(e.message));
  }, [setError]);
  async function createCase(e: FormEvent) {
    e.preventDefault();
    try {
      const c = await api.createCase(newCase);
      setCases([c, ...cases]);
      setNewCase({ reference: "CASE-0002", title: "", description: "" });
      await load(c);
    } catch (e) {
      setError((e as Error).message);
    }
  }
  async function register(e: FormEvent) {
    e.preventDefault();
    if (!selected) return;
    const form = new FormData(e.target as HTMLFormElement);
    try {
      const item = await api.registerEvidence(selected.id, {
        display_name: String(form.get("displayName")),
        original_path: String(form.get("path")),
        evidence_type: "synthetic_file",
        acquisition_metadata: { source: "operator" },
      });
      setEvidence([...evidence, item]);
    } catch (e) {
      setError((e as Error).message);
    }
  }
  async function verify(item: Evidence) {
    try {
      const updated = await api.verify(item.id);
      setEvidence(evidence.map((x) => (x.id === item.id ? updated : x)));
    } catch (e) {
      setError((e as Error).message);
    }
  }
  async function process(item: Evidence) {
    if (!selected) return;
    try {
      const job = await api.submitJob(selected.id, item.id);
      setJobs((current) => [job, ...current]);
      await load(selected);
    } catch (e) {
      setError((e as Error).message);
    }
  }
  async function find(e: FormEvent) {
    e.preventDefault();
    if (selected) setArtifacts(await api.artifacts(selected.id, query));
  }
  async function addFinding(e: FormEvent) {
    e.preventDefault();
    if (selected && findingText.trim()) {
      setFindings([
        ...findings,
        await api.createFinding(selected.id, findingText),
      ]);
      setFindingText("");
    }
  }
  async function report() {
    if (selected) {
      await api.createReport(
        selected.id,
        `Draft report: ${selected.reference}`,
      );
      setError("Report draft generated and recorded in audit history.");
    }
  }
  return (
    <div className="shell">
      <header>
        <div>
          <span className="eyebrow">FORENSIC WORKSPACE</span>
          <h1>Evidence to findings</h1>
        </div>
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
      {error && (
        <div className="alert danger global">
          {error}
          <button className="link" onClick={() => setError("")}>
            dismiss
          </button>
        </div>
      )}
      <div className="layout">
        <aside>
          <div className="section-title">
            <span>Cases</span>
            <span className="count">{cases.length}</span>
          </div>
          {cases.map((c) => (
            <button
              key={c.id}
              className={`case-item ${selected?.id === c.id ? "active" : ""}`}
              onClick={() => load(c)}
            >
              <strong>{c.reference}</strong>
              <span>{c.title}</span>
            </button>
          ))}
          {!cases.length && <p className="muted">No cases yet.</p>}
          <form className="new-case" onSubmit={createCase}>
            <h3>Create case</h3>
            <input
              aria-label="Case reference"
              placeholder="Reference"
              value={newCase.reference}
              onChange={(e) =>
                setNewCase({ ...newCase, reference: e.target.value })
              }
            />
            <input
              aria-label="Case title"
              placeholder="Title"
              required
              value={newCase.title}
              onChange={(e) =>
                setNewCase({ ...newCase, title: e.target.value })
              }
            />
            <button>Create</button>
          </form>
        </aside>
        <main className="content">
          {!selected ? (
            <div className="empty">
              <span className="empty-icon">⌁</span>
              <h2>Select a case to begin</h2>
              <p>
                Register evidence, verify its hash, and follow the provenance
                chain through to a report draft.
              </p>
            </div>
          ) : (
            <>
              <div className="case-heading">
                <div>
                  <span className="eyebrow">CASE / {selected.reference}</span>
                  <h2>{selected.title}</h2>
                  <p>
                    {selected.description || "No case description recorded."}
                  </p>
                </div>
                <span className="status">{selected.status}</span>
              </div>
              <div className="grid">
                <section className="panel">
                  <div className="panel-head">
                    <h3>Evidence register</h3>
                    <span className="count">{evidence.length}</span>
                  </div>
                  <form className="inline-form" onSubmit={register}>
                    <input
                      name="displayName"
                      required
                      placeholder="Display name"
                    />
                    <input
                      name="path"
                      required
                      placeholder="Read-only source path"
                    />
                    <button>Register</button>
                  </form>
                  {!evidence.length && (
                    <p className="muted">
                      No evidence registered. Use synthetic evidence for
                      development.
                    </p>
                  )}
                  {evidence.map((item) => (
                    <div className="record" key={item.id}>
                      <div>
                        <strong>{item.display_name}</strong>
                        <small>{item.original_path}</small>
                        <small>
                          SHA-256: {item.calculated_hash || "unverified"}
                        </small>
                      </div>
                      <span className={`badge ${item.verification_status}`}>
                        {item.verification_status}
                      </span>
                      <button
                        className="secondary"
                        onClick={() => verify(item)}
                      >
                        Verify
                      </button>
                      <button
                        className="secondary"
                        onClick={() => process(item)}
                        disabled={item.verification_status === "mismatch"}
                      >
                        Process
                      </button>
                    </div>
                  ))}
                  {jobs.length > 0 && (
                    <small className="muted">
                      Latest processing job: {jobs[0].status}
                    </small>
                  )}
                </section>
                <section className="panel">
                  <div className="panel-head">
                    <h3>Artifact search</h3>
                    <span className="count">{artifacts.length}</span>
                  </div>
                  <form className="inline-form" onSubmit={find}>
                    <input
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                      placeholder="Search normalized artifacts"
                    />
                    <button>Search</button>
                  </form>
                  {!artifacts.length && (
                    <p className="muted">
                      No artifacts yet. Processing results will appear here.
                    </p>
                  )}
                  {artifacts.map((a) => (
                    <div className="record" key={a.id}>
                      <div>
                        <strong>{a.content?.name || a.artifact_type}</strong>
                        <small>
                          {a.content?.sizeBytes ?? "?"} bytes ·{" "}
                          {a.processing_status}
                        </small>
                        <small>Source: {a.source_evidence}</small>
                      </div>
                      <span className="badge normalized">
                        provenance linked
                      </span>
                    </div>
                  ))}
                </section>
                <section className="panel">
                  <div className="panel-head">
                    <h3>Provenance chain</h3>
                    <span className="count">{provenance.length}</span>
                  </div>
                  {!provenance.length ? (
                    <p className="muted">
                      Missing provenance is surfaced as a review state.
                    </p>
                  ) : (
                    provenance.map((p) => (
                      <div className="chain" key={p.id}>
                        <span>Evidence</span>
                        <b>→</b>
                        <span>Artifact</span>
                        <small>{p.rationale}</small>
                      </div>
                    ))
                  )}
                </section>
                <section className="panel">
                  <div className="panel-head">
                    <h3>Examiner findings</h3>
                    <span className="count">{findings.length}</span>
                  </div>
                  <form onSubmit={addFinding}>
                    <textarea
                      value={findingText}
                      onChange={(e) => setFindingText(e.target.value)}
                      placeholder="Record an observed, source-supported finding..."
                    />
                    <button>Add draft finding</button>
                  </form>
                  {!findings.length && (
                    <p className="muted">No findings recorded.</p>
                  )}
                  {findings.map((f) => (
                    <div className="finding" key={f.id}>
                      <span className="badge draft">draft</span>
                      <p>{f.finding_text}</p>
                      <small>
                        Examiner-controlled conclusion ·{" "}
                        {new Date(f.created_at).toLocaleString()}
                      </small>
                    </div>
                  ))}
                </section>
                <section className="panel compact">
                  <div className="panel-head">
                    <h3>Report draft</h3>
                  </div>
                  <p className="muted">
                    Generate a traceable draft from current findings and
                    provenance. This is not a court-readiness claim.
                  </p>
                  <button onClick={report}>Generate draft</button>
                </section>
                <section className="panel compact">
                  <div className="panel-head">
                    <h3>Audit history</h3>
                    <span className="count">{audit.length}</span>
                  </div>
                  {audit.slice(0, 5).map((a) => (
                    <div className="audit" key={a.id}>
                      <span>{a.action}</span>
                      <small>{new Date(a.created_at).toLocaleString()}</small>
                    </div>
                  ))}
                </section>
              </div>
            </>
          )}
        </main>
      </div>
    </div>
  );
}
export default App;
