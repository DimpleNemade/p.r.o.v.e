import { createContext, useContext, useState } from "react";
import { api, Evidence, Finding } from "./api";

export const Actions = createContext<Record<string, boolean>>({});
export const useAction = (action: string) =>
  Boolean(useContext(Actions)[action]);

export function BaselineAcceptance({
  evidence,
  onDone,
  onError,
}: {
  evidence: Evidence;
  onDone: () => Promise<void>;
  onError: (message: string) => void;
}) {
  const [reason, setReason] = useState("");
  const permitted = useAction("evidence");
  if (evidence.verification_status !== "baseline_pending") return null;
  return (
    <form
      onSubmit={async (event) => {
        event.preventDefault();
        try {
          await api.acceptBaseline(evidence.id, reason);
          await onDone();
        } catch (error) {
          onError((error as Error).message);
        }
      }}
    >
      <p>
        Local hash observed. Accepting a baseline does not verify acquisition
        authenticity.
      </p>
      <label>
        Baseline acceptance reason
        <input
          required
          value={reason}
          onChange={(event) => setReason(event.target.value)}
        />
      </label>
      <button disabled={!permitted || !reason.trim()}>
        Accept local baseline
      </button>
    </form>
  );
}

export function ReviewActions({
  finding,
  onDone,
  onError,
}: {
  finding: Finding;
  onDone: () => Promise<void>;
  onError: (message: string) => void;
}) {
  const [comments, setComments] = useState("");
  const edit = useAction("finding"),
    review = useAction("review");
  const [busy, setBusy] = useState(false);
  async function act(action: string) {
    setBusy(true);
    try {
      await api.transition(finding.id, action, finding.version, comments);
      await onDone();
    } catch (error) {
      onError((error as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <section>
      <h3>Revision review</h3>
      <p>
        State: <strong>{finding.examiner_status}</strong> · Version{" "}
        {finding.version}
      </p>
      <p>{finding.integrity_impact}</p>
      <label>
        Review comments or revision reason
        <textarea
          value={comments}
          onChange={(event) => setComments(event.target.value)}
        />
      </label>
      {edit && finding.examiner_status === "draft" && (
        <button
          disabled={busy || !finding.support_count}
          onClick={() => act("submit")}
        >
          Submit revision
        </button>
      )}
      {review && finding.examiner_status === "submitted" && (
        <button
          disabled={busy || !comments.trim()}
          onClick={() => act("start_review")}
        >
          Start independent review
        </button>
      )}
      {review && finding.examiner_status === "in_review" && (
        <>
          <button
            disabled={busy || !comments.trim()}
            onClick={() => act("approve")}
          >
            Approve revision
          </button>
          <button
            disabled={busy || !comments.trim()}
            onClick={() => act("request_changes")}
          >
            Request changes
          </button>
        </>
      )}
      {edit && finding.examiner_status !== "draft" && (
        <>
          <button
            disabled={busy || !comments.trim()}
            onClick={() => act("supersede")}
          >
            Create superseding draft
          </button>
          <button
            disabled={busy || !comments.trim()}
            onClick={() => act("withdraw")}
          >
            Withdraw revision
          </button>
        </>
      )}
      {(finding.revisions || []).map((revision) => (
        <p key={revision.id}>
          Revision {revision.number}: {revision.status} ·{" "}
          {revision.snapshot_hash}
        </p>
      ))}
    </section>
  );
}

export function ExportControl({
  caseId,
  reportId,
  onError,
}: {
  caseId: string;
  reportId?: string;
  onError: (message: string) => void;
}) {
  const permitted = useAction("export");
  const [result, setResult] = useState<{
    status: string;
    content_digest: string;
    download_url: string | null;
  } | null>(null);
  return (
    <section>
      <h3>Controlled handoff</h3>
      <p>
        Original evidence excluded. The package contains a captured snapshot and
        its audit cutoff.
      </p>
      <button
        disabled={!permitted}
        onClick={async () => {
          try {
            setResult(await api.createExport(caseId, reportId));
          } catch (error) {
            onError((error as Error).message);
          }
        }}
      >
        Create export package
      </button>
      {result && (
        <p>
          {result.status} · {result.content_digest}{" "}
          {result.download_url && (
            <a href={result.download_url} download>
              Download verified package
            </a>
          )}
        </p>
      )}
    </section>
  );
}
