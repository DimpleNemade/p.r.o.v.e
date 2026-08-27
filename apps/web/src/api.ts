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
  created_at: string;
};
export type Evidence = {
  id: string;
  display_name: string;
  original_path: string;
  expected_hash: string;
  calculated_hash: string;
  verification_status: string;
  evidence_type: string;
  acquisition_metadata?: Record<string, unknown>;
};

let csrfToken = "";

async function request<T>(url: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  if (
    options.method &&
    !["GET", "HEAD", "OPTIONS"].includes(options.method.toUpperCase()) &&
    csrfToken
  ) {
    headers.set("X-CSRFToken", csrfToken);
  }
  const response = await fetch(url, {
    ...options,
    headers,
    credentials: "include",
  });
  if (!response.ok)
    throw new Error(
      (await response.json().catch(() => ({}))).detail ||
        `Request failed (${response.status})`,
    );
  return response.status === 204 ? (undefined as T) : response.json();
}
export const api = {
  csrf: async () => {
    const response = await request<{ csrfToken: string }>("/api/auth/csrf/");
    csrfToken = response.csrfToken;
    return response;
  },
  login: async (username: string, password: string) => {
    await api.csrf();
    return request<User>("/api/auth/login/", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
  },
  logout: () => request<void>("/api/auth/logout/", { method: "POST" }),
  me: () => request<User>("/api/auth/me/"),
  cases: () => request<Case[]>("/api/cases/"),
  createCase: (body: {
    reference: string;
    title: string;
    description: string;
  }) =>
    request<Case>("/api/cases/", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  evidence: (id: string) => request<Evidence[]>(`/api/cases/${id}/evidence/`),
  registerEvidence: (id: string, body: Partial<Evidence>) =>
    request<Evidence>(`/api/cases/${id}/evidence/`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  verify: (id: string) =>
    request<Evidence>(`/api/evidence/${id}/verify/`, { method: "POST" }),
  jobs: (id: string) => request<any[]>(`/api/cases/${id}/jobs/`),
  submitJob: (id: string, evidence: string) =>
    request<any>(`/api/cases/${id}/jobs/`, {
      method: "POST",
      body: JSON.stringify({ evidence }),
    }),
  artifacts: (id: string, q = "") =>
    request<any[]>(`/api/cases/${id}/artifacts/?q=${encodeURIComponent(q)}`),
  provenance: (id: string) => request<any[]>(`/api/cases/${id}/provenance/`),
  findings: (id: string) => request<any[]>(`/api/cases/${id}/findings/`),
  createFinding: (id: string, finding_text: string) =>
    request<any>(`/api/cases/${id}/findings/`, {
      method: "POST",
      body: JSON.stringify({ finding_text }),
    }),
  reports: (id: string) => request<any[]>(`/api/cases/${id}/reports/`),
  createReport: (id: string, title: string) =>
    request<any>(`/api/cases/${id}/reports/`, {
      method: "POST",
      body: JSON.stringify({ title }),
    }),
  audit: (id: string) => request<any[]>(`/api/cases/${id}/audit/`),
};
