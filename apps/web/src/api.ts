export type User = {
  id: string;
  username: string;
  displayName: string;
  role: string;
};
export type Case = {
  id: string;
  reference: string;
  title: string;
  description: string;
  status: string;
  owner: string;
  created_at: string;
  updated_at: string;
  actions: Record<string, boolean>;
  evidence_count: number;
  finding_count: number;
};
export type Evidence = {
  id: string;
  case: string;
  display_name: string;
  evidence_type: string;
  source_locator: string;
  baseline_hash: string;
  baseline_origin: string;
  baseline_reason: string;
  acquisition_metadata: Record<string, unknown>;
  hash_algorithm: string;
  expected_hash: string;
  calculated_hash: string;
  verification_status: string;
  read_only: boolean;
  is_synthetic: boolean;
  synthetic_label: string;
  warnings: string[];
  limitations: string[];
  registered_by: string;
  registered_by_name: string;
  registered_at: string;
  processing_status: string;
};
export type TimelineEvent = {
  id: string;
  case: string;
  artifact: string | null;
  observed_at: string | null;
  timestamp_meaning: string;
  event_type: string;
  summary: string;
  interpretation_status: string;
  created_at: string;
};
export type Finding = {
  id: string;
  case: string;
  author: string;
  finding_text: string;
  finding_basis: string;
  examiner_status: string;
  review_status: string;
  reviewer_comments: string;
  reviewed_at: string | null;
  created_at: string;
  updated_at: string;
  version: number;
  integrity_impact: string;
  revisions: {
    id: string;
    number: number;
    status: string;
    snapshot_hash: string;
  }[];
  support_count: number;
  supports?: Support[];
};
export type Support = {
  id: string;
  finding: string;
  artifact: string | null;
  timeline_event: string | null;
  created_at: string;
};
export type Artifact = {
  id: string;
  case: string;
  source_evidence: string | Evidence;
  source_path: string;
  source_hash_reference: string;
  processing_run: string | Record<string, unknown>;
  processor_name: string;
  processor_version: string;
  processing_timestamp: string;
  processing_status: string;
  artifact_type: string;
  content: Record<string, unknown>;
  limitations: string[];
  warnings: string[];
  created_at: string;
  timeline_events?: TimelineEvent[];
  related_findings?: Finding[];
};
export type Report = {
  id: string;
  case: string;
  title: string;
  status: string;
  body: Record<string, any>;
  created_by: string;
  created_at: string;
  updated_at: string;
};
export type AuditEvent = {
  id: string;
  case: string | null;
  actor: string | null;
  actor_name: string;
  action: string;
  object_type: string;
  object_id: string;
  metadata: Record<string, unknown>;
  created_at: string;
};

const API_ROOT = "/api/v1";
let csrfToken = "";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  const method = (options.method || "GET").toUpperCase();
  if (!["GET", "HEAD", "OPTIONS"].includes(method) && csrfToken)
    headers.set("X-CSRFToken", csrfToken);
  const response = await fetch(`${API_ROOT}${path}`, {
    ...options,
    headers,
    credentials: "include",
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    const error = new Error(
      payload.detail ||
        JSON.stringify(payload) ||
        `Request failed (${response.status})`,
    ) as Error & { code?: string; status?: number };
    error.code = payload.code;
    error.status = response.status;
    throw error;
  }
  return response.status === 204 ? (undefined as T) : response.json();
}

type Page<T> = { count: number; limit: number; offset: number; results: T[] };
async function requestAll<T>(path: string): Promise<T[]> {
  const separator = path.includes("?") ? "&" : "?";
  const first = await request<Page<T>>(`${path}${separator}limit=100&offset=0`);
  const results = [...first.results];
  for (let offset = first.results.length; offset < first.count; offset += 100) {
    const page = await request<Page<T>>(
      `${path}${separator}limit=100&offset=${offset}`,
    );
    results.push(...page.results);
  }
  return results;
}

export const api = {
  csrf: async () => {
    const response = await request<{ csrfToken: string }>("/auth/csrf/");
    csrfToken = response.csrfToken;
    return response;
  },
  login: async (username: string, password: string) => {
    await api.csrf();
    const user = await request<User>("/auth/login/", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
    await api.csrf();
    return user;
  },
  logout: () => request<void>("/auth/logout/", { method: "POST" }),
  me: () => request<User>("/auth/me/"),
  cases: () => requestAll<Case>("/cases/"),
  caseDetail: (id: string) => request<Case>(`/cases/${id}/`),
  createCase: (body: {
    reference: string;
    title: string;
    description: string;
  }) =>
    request<Case>("/cases/", { method: "POST", body: JSON.stringify(body) }),
  participants: (id: string) => requestAll<any>(`/cases/${id}/participants/`),
  evidence: (id: string) => requestAll<Evidence>(`/cases/${id}/evidence/`),
  evidenceDetail: (id: string) => request<Evidence>(`/evidence/${id}/`),
  registerEvidence: (id: string, body: Record<string, unknown>) =>
    request<Evidence>(`/cases/${id}/evidence/`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  acceptBaseline: (id: string, reason: string) =>
    request<Evidence>(`/evidence/${id}/accept-baseline/`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    }),
  transition: (id: string, action: string, version: number, comments: string) =>
    request<Finding>(`/findings/${id}/transition/`, {
      method: "POST",
      body: JSON.stringify({ action, version, comments }),
    }),
  createExport: (id: string, report?: string) =>
    request<{
      status: string;
      content_digest: string;
      download_url: string | null;
    }>(`/cases/${id}/exports/`, {
      method: "POST",
      body: JSON.stringify({ report }),
    }),
  verifyStatus: (id: string) => request<any>(`/evidence/${id}/verify/`),
  verify: (id: string) =>
    request<Evidence>(`/evidence/${id}/verify/`, { method: "POST" }),
  jobs: (id: string) => requestAll<any>(`/cases/${id}/jobs/`),
  jobDetail: (id: string) => request<any>(`/jobs/${id}/`),
  submitJob: (id: string, evidence: string) =>
    request<any>(`/cases/${id}/jobs/`, {
      method: "POST",
      body: JSON.stringify({ evidence }),
    }),
  artifacts: (id: string, q = "") =>
    requestAll<Artifact>(`/cases/${id}/artifacts/?q=${encodeURIComponent(q)}`),
  artifact: (id: string) => request<Artifact>(`/artifacts/${id}/`),
  artifactProvenance: (id: string) =>
    request<any>(`/artifacts/${id}/provenance/`),
  provenance: (id: string) => requestAll<any>(`/cases/${id}/provenance/`),
  timeline: (id: string, params: Record<string, string> = {}) =>
    requestAll<TimelineEvent>(
      `/cases/${id}/timeline/?${new URLSearchParams(params)}`,
    ),
  findings: (id: string) => requestAll<Finding>(`/cases/${id}/findings/`),
  createFinding: (
    id: string,
    body: { finding_text: string; finding_basis: string },
  ) =>
    request<Finding>(`/cases/${id}/findings/`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  finding: (id: string) => request<Finding>(`/findings/${id}/`),
  supports: (id: string) => requestAll<Support>(`/findings/${id}/support/`),
  addSupport: (
    id: string,
    body: { artifact?: string; timeline_event?: string },
  ) =>
    request<Support>(`/findings/${id}/support/`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  reports: (id: string) => requestAll<Report>(`/cases/${id}/reports/`),
  createReport: (id: string, title: string) =>
    request<Report>(`/cases/${id}/reports/`, {
      method: "POST",
      body: JSON.stringify({ title }),
    }),
  report: (id: string) => request<Report>(`/reports/${id}/`),
  audit: (id: string) => requestAll<AuditEvent>(`/cases/${id}/audit/`),
  globalAudit: () => requestAll<AuditEvent>("/audit/"),
  bookmarks: (id: string) => requestAll<any>(`/cases/${id}/bookmarks/`),
  notes: (id: string) => requestAll<any>(`/cases/${id}/notes/`),
};
