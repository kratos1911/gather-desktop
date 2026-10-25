import { useEffect, useRef, useState, useSyncExternalStore } from "react";
import { LibraryClient, LibraryClientError } from "../services/libraryClient";
import { LibraryWorkspace } from "../services/libraryWorkspace";
import {
  PILOT_EMAILS,
  PILOT_NOTE,
  PILOT_QUERY,
  signInPilot,
} from "../services/pilotAuth";
import "./OperatorPilot.css";

const messages: Record<string, string> = {
  network_unavailable:
    "The local API is unavailable. Start the operator server, then retry the same action.",
  service_unavailable:
    "The backend could not complete this action. Inspect the operator output before retrying.",
  model_unavailable:
    "The model service or its operator token is unavailable. Restart the API server and check Cloud Run readiness before trying again.",
  library_unavailable:
    "The search database could not complete the request. Check the operator output.",
  busy: "An operation is still finishing. Wait before trying again.",
  timeout:
    "The deadline was reached. An import may still have been saved; use Retry same import.",
  session_required:
    "Your session is unavailable. Disconnect and sign in again.",
  source_unavailable:
    "This exact source version is no longer available to this session.",
  pilot_signin_failed:
    "Sign-in failed. Check the test account password and configuration.",
  cancelled: "Request cancelled. A submitted import may still have been saved.",
};

export default function OperatorPilot() {
  const [workspace] = useState(
    () =>
      new LibraryWorkspace(
        new LibraryClient("http://127.0.0.1:8765", { allowLoopback: true }),
      ),
  );
  const state = useSyncExternalStore(
    workspace.subscribe,
    workspace.getSnapshot,
  );
  const [email, setEmail] = useState<string>(PILOT_EMAILS[0]);
  const [signingIn, setSigningIn] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const password = useRef<HTMLInputElement>(null);
  const auth = useRef<AbortController | null>(null);
  const readerHeading = useRef<HTMLHeadingElement>(null);
  const key = import.meta.env.VITE_GATHER_PILOT_PUBLIC_KEY as
    string | undefined;
  useEffect(
    () => () => {
      auth.current?.abort();
      workspace.dispose();
    },
    [workspace],
  );
  useEffect(() => {
    if (state.opened) readerHeading.current?.focus();
  }, [state.opened]);
  function act(work: () => Promise<void>) {
    setLocalError(null);
    void work().catch((error) =>
      setLocalError(
        error instanceof LibraryClientError ? error.code : "operation_failed",
      ),
    );
  }
  async function login(event: React.FormEvent) {
    event.preventDefault();
    if (!key || signingIn) return;
    const value = password.current?.value ?? "";
    if (password.current) password.current.value = "";
    const controller = new AbortController();
    auth.current?.abort();
    auth.current = controller;
    setSigningIn(true);
    setLocalError(null);
    try {
      const token = await signInPilot(email, value, key, controller.signal);
      if (!controller.signal.aborted) workspace.setSession(token);
    } catch (error) {
      if (!controller.signal.aborted)
        setLocalError(
          error instanceof LibraryClientError
            ? error.code
            : "pilot_signin_failed",
        );
    } finally {
      if (!controller.signal.aborted) setSigningIn(false);
    }
  }
  const error = localError ?? state.error;
  return (
    <section className="content operator-pilot">
      <div className="screen-heading">
        <h1>Operator pilot</h1>
        <p className="subtitle">
          Two test accounts. One synthetic note. Explicit actions use the hosted
          database and cloud model; the sample library stays separate.
        </p>
      </div>
      <p className="pilot-disclosure">
        Authentication and stored test text use Supabase in Sydney. Embeddings
        use Gather’s private CPU service in Mumbai. No personal files or signup
        in this screen. Model calls count toward the pilot budget.
      </p>
      {!state.signedIn ? (
        <form className="pilot-form" onSubmit={(event) => void login(event)}>
          <label htmlFor="pilot-account">Test account</label>
          <select
            id="pilot-account"
            value={email}
            disabled={signingIn}
            onChange={(event) => setEmail(event.target.value)}
          >
            {PILOT_EMAILS.map((value) => (
              <option key={value}>{value}</option>
            ))}
          </select>
          <label htmlFor="pilot-password">Test account password</label>
          <input
            id="pilot-password"
            ref={password}
            type="password"
            autoComplete="current-password"
            required
            disabled={signingIn}
          />
          <button className="pilot-action" disabled={signingIn || !key}>
            {signingIn ? "Signing in…" : "Sign in to pilot"}
          </button>
          {!key && (
            <p role="status">
              The operator public configuration is missing. Follow the local
              pilot setup guide before signing in.
            </p>
          )}
        </form>
      ) : (
        <>
          <div className="pilot-toolbar">
            <span>Connected as {email}</span>
            <button
              className="back"
              onClick={() => {
                workspace.setSession(null);
                setLocalError(null);
              }}
            >
              Disconnect
            </button>
          </div>
          <section className="pilot-step">
            <h2>1. Import the test note</h2>
            <p>{PILOT_NOTE}</p>
            <button
              className="pilot-action"
              disabled={
                state.busy ||
                !!state.pendingImport ||
                !!state.imported ||
                !!state.cleanupSourceId
              }
              onClick={() =>
                act(() =>
                  workspace.importText(
                    "Synthetic Gather pilot",
                    new TextEncoder().encode(PILOT_NOTE),
                    "text/plain",
                  ),
                )
              }
            >
              Import synthetic note
            </button>
            {state.pendingImport && (
              <button
                className="back"
                disabled={state.busy}
                onClick={() => act(() => workspace.retryImport())}
              >
                Retry same import
              </button>
            )}
            {state.imported && (
              <div className="pilot-job">
                <p>
                  Saved. Processing state:{" "}
                  <strong>{state.processing?.state ?? "not checked"}</strong>
                </p>
                <p>
                  Run the worker once in another terminal, then refresh status:
                </p>
                <code>
                  .\scripts\library.ps1 -Action worker -JobId{" "}
                  {state.imported.job_id}
                </code>
                <p>
                  Source: <code>{state.imported.source_id}</code>
                </p>
                {state.processing?.error_code && (
                  <p>
                    Processing could not finish: {state.processing.error_code}.
                  </p>
                )}
                <button
                  className="back"
                  disabled={state.busy}
                  onClick={() => act(() => workspace.refreshStatus())}
                >
                  Refresh status
                </button>
              </div>
            )}
          </section>
          <section className="pilot-step">
            <h2>2. Search and open</h2>
            <p>{PILOT_QUERY}</p>
            <button
              className="pilot-action"
              disabled={state.busy}
              onClick={() => act(() => workspace.search(PILOT_QUERY))}
            >
              Search saved notes
            </button>
            {state.results && !state.results.windows.length && (
              <p role="status">
                No matching published source is visible to this account.
              </p>
            )}
            <ul className="pilot-results">
              {state.results?.windows.map((hit) => (
                <li key={`${hit.source_id}/${hit.version_id}`}>
                  <h3>{hit.title}</h3>
                  <p>{hit.text}</p>
                  <small>
                    Source characters {hit.start}–{hit.end} · exact saved
                    version
                  </small>
                  <button
                    className="back"
                    disabled={state.busy}
                    onClick={() =>
                      act(() => workspace.open(hit.source_id, hit.version_id))
                    }
                  >
                    Open saved text
                  </button>
                </li>
              ))}
            </ul>
            {state.opened && (
              <article className="paper pilot-reader">
                <h3 ref={readerHeading} tabIndex={-1}>
                  {state.opened.title}
                </h3>
                <p>{state.opened.body}</p>
              </article>
            )}
          </section>
          {state.imported && (
            <section className="pilot-step">
              <h2>3. Delete the test note</h2>
              <p>
                Deletion hides it immediately. The operator still finalizes
                physical cleanup in the database. Keep the source ID until
                cleanup is confirmed.
              </p>
              <button
                className="back"
                disabled={state.busy}
                onClick={() => {
                  const source = state.imported;
                  if (source) act(() => workspace.delete(source.source_id));
                }}
              >
                Delete synthetic note
              </button>
            </section>
          )}
          <p className="pilot-disclosure">
            This view keeps state only for the current connection. Disconnecting
            clears local results; it does not delete server data or revoke other
            sessions. No automatic model requests or processing retries.
          </p>
        </>
      )}
      {state.cleanupSourceId && (
        <div role="status" className="notice">
          Removed from search. Physical cleanup remains pending for source{" "}
          <code>{state.cleanupSourceId}</code>. Keep this ID for the operator
          cleanup step.
        </div>
      )}
      {state.busy && (
        <div role="status" className="notice">
          Waiting for the backend…{" "}
          <button onClick={() => workspace.cancel()}>Cancel request</button>
        </div>
      )}
      {error && (
        <p role="alert" className="notice">
          {messages[error] ??
            "The action could not complete. Check the operator setup and try again when resolved."}
        </p>
      )}
    </section>
  );
}
