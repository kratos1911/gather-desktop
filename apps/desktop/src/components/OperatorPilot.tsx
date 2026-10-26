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
import { TextFileImport } from "./TextFileImport";
import { ModelConnection } from "./ModelConnection";
import { MODEL_MESSAGES } from "../services/modelAvailability";

const messages: Record<string, string> = {
  ...MODEL_MESSAGES,
  network_unavailable:
    "The local API is unavailable. Start the operator server, then retry the same action.",
  service_unavailable:
    "The backend could not complete this action. Inspect the operator output before retrying.",
  library_unavailable:
    "The library database could not complete the request. Check the operator output; source listing also requires the approved listing migration.",
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
  access_denied:
    "This action is not enabled for the private pilot. The server and frontend both need the explicit -TextFiles option for reviewed file imports.",
  invalid_request:
    "The file or request was rejected before saving. Check UTF-8, size and content. Files must also fit the pilot's three-passage processing budget.",
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
  const [query, setQuery] = useState(PILOT_QUERY);
  const textFiles = import.meta.env.VITE_GATHER_PILOT_TEXT_FILES === "1";
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
      if (!controller.signal.aborted) {
        workspace.setSession(token);
        await workspace.loadSources();
      }
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
  const readyImport =
    state.imported !== null &&
    state.processing?.state === "ready" &&
    state.processing.version_id === state.imported.version_id;
  const noPublishedSources =
    !readyImport &&
    state.libraryStatus === "ready" &&
    state.nextCursor === null &&
    state.sources.every((source) => source.published_version_id === null);
  return (
    <section className="content operator-pilot">
      <div className="screen-heading">
        <h1>Operator pilot</h1>
        <p className="subtitle">
          {textFiles
            ? "Private TXT/Markdown testing with two existing accounts. Review each file before cloud storage; processing is a separate action."
            : "Two test accounts. One synthetic note. Explicit actions use the hosted database and cloud model; the sample library stays separate."}
        </p>
      </div>
      <p className="pilot-disclosure">
        Authentication and stored test text use Supabase in Sydney. Embeddings
        use Gather’s private CPU service in Mumbai.{" "}
        {textFiles
          ? "No public signup or general uploads. Use only your own nonsensitive test files."
          : "No personal files or signup in this screen."}{" "}
        Model calls count toward the pilot budget.
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
                setQuery(PILOT_QUERY);
                setLocalError(null);
              }}
            >
              Disconnect
            </button>
          </div>
          <ModelConnection
            status={state.modelStatus}
            busy={state.busy}
            onCheck={() => act(() => workspace.checkModel())}
          />
          <section
            className="pilot-step"
            aria-labelledby="saved-library-heading"
          >
            <h2 id="saved-library-heading">Saved library</h2>
            <p>
              Saved sources reload after sign-in. Refreshing this list makes no
              model requests.
            </p>
            <button
              className="back"
              disabled={state.busy}
              onClick={() => act(() => workspace.loadSources())}
            >
              Refresh saved library
            </button>
            {state.libraryStatus === "loading" && (
              <p role="status">Loading saved sources…</p>
            )}
            {state.libraryStatus === "error" && (
              <p role="status">
                The library could not load.{" "}
                {state.nextCursor
                  ? "Use Load more saved sources to retry this page, or refresh the library to start over."
                  : "Use Refresh saved library to retry."}
              </p>
            )}
            {state.libraryStatus === "ready" && !state.sources.length && (
              <p role="status">No saved sources are visible to this account.</p>
            )}
            <ul className="pilot-results" aria-label="Saved sources">
              {state.sources.map((source) => (
                <li key={source.source_id}>
                  <h3>{source.title}</h3>
                  <p>
                    {source.published_version_id
                      ? "Published text available. "
                      : "No published text. "}
                    {source.published_version_id &&
                    source.published_version_id !== source.processing_version_id
                      ? "Replacement processing: "
                      : "Processing: "}
                    {source.state ?? "not started"}
                    {source.attempts !== null &&
                      ` · attempts ${source.attempts}/3`}
                    {source.error_code && ` · ${source.error_code}`}
                  </p>
                  {source.job_id &&
                    (source.state === "queued" ||
                      source.state === "processing") && (
                      <p>
                        Operator job: <code>{source.job_id}</code>. Refresh the
                        saved library before deciding whether to run a worker.
                      </p>
                    )}
                  {source.published_version_id && (
                    <button
                      className="back"
                      disabled={state.busy}
                      aria-label={`Open saved ${source.title}`}
                      onClick={() =>
                        act(() =>
                          workspace.open(
                            source.source_id,
                            source.published_version_id!,
                          ),
                        )
                      }
                    >
                      Open published text
                    </button>
                  )}
                  <button
                    className="back"
                    disabled={state.busy}
                    aria-label={`Delete saved ${source.title}`}
                    onClick={() =>
                      act(() => workspace.delete(source.source_id))
                    }
                  >
                    Delete source
                  </button>
                </li>
              ))}
            </ul>
            {state.nextCursor && (
              <button
                className="back"
                disabled={state.busy}
                onClick={() => act(() => workspace.loadSources(true))}
              >
                Load more saved sources
              </button>
            )}
          </section>
          <section className="pilot-step">
            <h2>
              {textFiles
                ? "1. Import TXT or Markdown"
                : "1. Import the test note"}
            </h2>
            {textFiles && (
              <TextFileImport
                disabled={
                  state.busy ||
                  !!state.pendingImport ||
                  !!state.imported ||
                  !!state.cleanupSourceId
                }
                onSave={async (file) => {
                  setLocalError(null);
                  await workspace.importText(
                    file.title,
                    file.bytes,
                    file.media,
                    true,
                  );
                  const current = workspace.getSnapshot();
                  return (
                    current.pendingImport === null &&
                    current.imported !== null &&
                    current.error === null
                  );
                }}
              />
            )}
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
                  {textFiles && " -TextFiles"}
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
            {textFiles ? (
              <>
                <label htmlFor="pilot-query">Search your saved text</label>
                <input
                  id="pilot-query"
                  className="pilot-query"
                  value={query}
                  disabled={state.busy}
                  onChange={(event) => setQuery(event.target.value)}
                />
              </>
            ) : (
              <p>{PILOT_QUERY}</p>
            )}
            <button
              className="pilot-action"
              disabled={
                state.busy ||
                noPublishedSources ||
                state.modelStatus?.state === "model_budget_exhausted" ||
                (textFiles && !query.trim())
              }
              onClick={() =>
                act(() => workspace.search(textFiles ? query : PILOT_QUERY))
              }
            >
              Search saved notes
            </button>
            {noPublishedSources && (
              <p role="status">
                No published documents are available to search. Import a file
                and finish processing it, then refresh its status or the saved
                library. No model request is needed for an empty library.
              </p>
            )}
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
                  <button
                    className="back"
                    aria-label={`Delete ${hit.title}`}
                    disabled={state.busy}
                    onClick={() => act(() => workspace.delete(hit.source_id))}
                  >
                    Delete saved note
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
              <h2>
                {textFiles
                  ? "3. Delete the imported source"
                  : "3. Delete the test note"}
              </h2>
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
                {textFiles ? "Delete imported source" : "Delete synthetic note"}
              </button>
            </section>
          )}
          <p className="pilot-disclosure">
            Credentials and results stay in memory. After refresh, sign in again
            to reload saved sources. Disconnecting clears local data; it does
            not delete server data or revoke other sessions. No automatic model
            requests or processing retries.
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
