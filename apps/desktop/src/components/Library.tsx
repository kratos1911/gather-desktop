import {
  useEffect,
  useRef,
  useState,
  useSyncExternalStore,
  type ReactNode,
} from "react";
import {
  LibraryClient,
  LibraryClientError,
  type LibrarySource,
  type SearchWindow,
} from "../services/libraryClient";
import { LibraryWorkspace } from "../services/libraryWorkspace";
import {
  libraryEndpoint,
  connectedPilot,
} from "../services/pilotConfiguration";
import { PILOT_EMAILS, signInPilot } from "../services/pilotAuth";
import { MODEL_MESSAGES } from "../services/modelAvailability";
import { TextFileImport } from "./TextFileImport";
import { ModelConnection } from "./ModelConnection";
import { PolicyPage, type PolicyKind } from "./PolicyPage";
import "./Library.css";

const messages: Record<string, string> = {
  ...MODEL_MESSAGES,
  network_unavailable:
    "The library is unreachable. Check your connection, then retry the same action.",
  service_unavailable:
    "The service could not finish this action. Try again after checking the connection.",
  library_unavailable:
    "Your saved library could not load. Refresh to try again; your files have not been removed.",
  busy: "Another action is finishing. Please wait before trying again.",
  timeout:
    "This action reached its deadline. If you were saving a file, use Retry same import to avoid duplicates.",
  session_required:
    "Your session is unavailable. Sign out, then sign in again.",
  pilot_signin_failed:
    "Sign-in failed. Check your account password, then try again.",
  source_unavailable:
    "This saved version is no longer available. Refresh your library to see its current state.",
  processing_not_eligible:
    "This attempt cannot resume yet. Refresh first; the job may be active, complete, waiting, or outside automatic processing.",
  cleanup_pending:
    "The file is hidden from search. Cleanup is still pending; use Finish cleanup to retry.",
  access_denied:
    "File import is not enabled by this server. Use the configured private Gather build.",
  invalid_request:
    "The file or request was rejected. Check the supported format, 64 KiB size limit and three-passage budget.",
  cancelled: "Request cancelled. A submitted file may still have been saved.",
  pdf_encrypted:
    "Password-protected PDFs are unsupported. Choose an unencrypted PDF you have permission to use.",
  pdf_text_required:
    "Every PDF page must have selectable text. Scanned or empty pages are unsupported in this first PDF pilot.",
  pdf_active_content:
    "This PDF contains forms or active actions that this pilot does not support.",
  pdf_page_limit: "This pilot accepts PDFs with at most 20 pages.",
  pdf_text_limit:
    "Extracted PDF text exceeds 64 KiB. No partial document was saved.",
  pdf_stream_limit:
    "A PDF content stream exceeds the processing limit. No partial document was saved.",
  pdf_invalid:
    "The PDF could not be safely parsed. Choose a valid PDF with selectable text.",
  pdf_invalid_output: "PDF validation failed. The file was not published.",
  pdf_size: "Choose a nonempty PDF of at most 64 KiB.",
  pdf_timeout:
    "PDF extraction reached its deadline. It was not retried automatically.",
  pdf_busy: "Another PDF is being checked. Wait before trying again.",
  pdf_parser_unavailable:
    "PDF extraction is unavailable on this server. TXT and Markdown remain available.",
};
const filters = ["Everything", "PDFs", "Markdown", "Text files"] as const;
type Filter = (typeof filters)[number];
type Panel = "import" | "settings" | PolicyKind | null;

function Icon({
  kind,
}: {
  kind: "add" | "grid" | "settings" | "search" | "close";
}) {
  const paths = {
    add: "M12 5v14M5 12h14",
    grid: "M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4zM14 14h6v6h-6z",
    settings: "M4 7h16M4 17h16M9 4v6M16 14v6",
    search: "M10.5 4a6.5 6.5 0 1 0 0 13 6.5 6.5 0 0 0 0-13M16 16l5 5",
    close: "M6 6l12 12M18 6 6 18",
  };
  return (
    <svg
      viewBox="0 0 24 24"
      width="20"
      height="20"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d={paths[kind]} />
    </svg>
  );
}

/** Native modal focus containment and Escape handling, with focus restored on close. */
function PanelDialog({
  title,
  children,
  dismiss,
  reader = false,
}: {
  title: string;
  children: ReactNode;
  dismiss: () => void;
  reader?: boolean;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const element = dialog.current;
    const previous = document.activeElement;
    element?.showModal();
    return () => {
      element?.close();
      if (previous instanceof HTMLElement && previous.isConnected)
        previous.focus();
    };
  }, []);
  return (
    <dialog
      ref={dialog}
      className={`library-dialog${reader ? " library-reader" : ""}`}
      aria-labelledby="library-panel-title"
      onCancel={(event) => {
        event.preventDefault();
        dismiss();
      }}
    >
      <header className="dialog-heading">
        <h2 id="library-panel-title">{title}</h2>
        <button
          className="icon-button"
          aria-label={`Close ${title}`}
          onClick={dismiss}
        >
          <Icon kind="close" />
        </button>
      </header>
      <div className="dialog-content">{children}</div>
    </dialog>
  );
}

function fileType(title: string) {
  if (/\.pdf$/i.test(title)) return "PDFs";
  return /\.(md|markdown)$/i.test(title) ? "Markdown" : "Text files";
}
function fileLabel(title: string) {
  if (fileType(title) === "PDFs") return "PDF";
  return fileType(title) === "Markdown" ? "MD" : "TXT";
}
function matches(title: string, filter: Filter) {
  return filter === "Everything" || fileType(title) === filter;
}
function statusLabel(source: LibrarySource) {
  const replacement =
    source.published_version_id &&
    source.published_version_id !== source.processing_version_id;
  if (replacement)
    return `Saved version available · replacement ${source.state ?? "pending"}`;
  if (source.published_version_id) return "Ready to search";
  if (source.state === "processing") return "Processing status: processing";
  if (source.state === "queued" && source.attempts)
    return "Waiting for explicit recovery";
  return source.state === "failed"
    ? "Processing failed"
    : source.state === "queued"
      ? "Queued for processing"
      : "No published text";
}

export default function Library() {
  const [workspace] = useState(() => {
    const endpoint = libraryEndpoint();
    return new LibraryWorkspace(
      new LibraryClient(endpoint.url, {
        allowLoopback: endpoint.allowLoopback,
      }),
    );
  });
  const state = useSyncExternalStore(
    workspace.subscribe,
    workspace.getSnapshot,
  );
  const [email, setEmail] = useState<string>(PILOT_EMAILS[0]);
  const [signingIn, setSigningIn] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [submitted, setSubmitted] = useState<string | null>(null);
  const [filter, setFilter] = useState<Filter>("Everything");
  const [readerPage, setReaderPage] = useState<number | null>(null);
  const [panel, setPanel] = useState<Panel>(null);
  const [deleting, setDeleting] = useState<{
    source_id: string;
    title: string;
  } | null>(null);
  const password = useRef<HTMLInputElement>(null);
  const search = useRef<HTMLInputElement>(null);
  const auth = useRef<AbortController | null>(null);
  const epoch = useRef(0);
  const refreshedJob = useRef<string | null>(null);
  const key = import.meta.env.VITE_GATHER_PILOT_PUBLIC_KEY as
    string | undefined;
  const textFiles =
    connectedPilot || import.meta.env.VITE_GATHER_PILOT_TEXT_FILES === "1";
  useEffect(
    () => () => {
      epoch.current++;
      auth.current?.abort();
      workspace.dispose();
    },
    [workspace],
  );
  useEffect(() => workspace.watchImport(), [workspace, state.imported]);
  useEffect(() => {
    if (state.opened?.pages && readerPage)
      document
        .getElementById(`pdf-page-${readerPage}`)
        ?.scrollIntoView?.({ block: "start" });
  }, [state.opened, readerPage]);
  useEffect(() => {
    const job = state.imported;
    if (
      !state.busy &&
      job &&
      state.processing?.state === "ready" &&
      state.processing.version_id === job.version_id &&
      refreshedJob.current !== job.job_id
    ) {
      refreshedJob.current = job.job_id;
      void workspace.loadSources();
    }
  }, [workspace, state.busy, state.imported, state.processing]);
  useEffect(() => {
    const focusSearch = (event: KeyboardEvent) => {
      if (
        event.ctrlKey &&
        event.key.toLowerCase() === "k" &&
        !panel &&
        !state.opened &&
        !deleting
      ) {
        event.preventDefault();
        search.current?.focus();
      }
    };
    document.addEventListener("keydown", focusSearch);
    return () => document.removeEventListener("keydown", focusSearch);
  }, [panel, state.opened, deleting]);

  function act(work: () => Promise<void>) {
    const started = epoch.current;
    setLocalError(null);
    void work().catch((error) => {
      if (started === epoch.current)
        setLocalError(
          error instanceof LibraryClientError ? error.code : "operation_failed",
        );
    });
  }
  async function login(event: React.FormEvent) {
    event.preventDefault();
    if (!key || signingIn) return;
    const value = password.current?.value ?? "";
    if (password.current) password.current.value = "";
    const controller = new AbortController();
    auth.current?.abort();
    auth.current = controller;
    const started = ++epoch.current;
    setSigningIn(true);
    setLocalError(null);
    try {
      const token = await signInPilot(email, value, key, controller.signal);
      if (!controller.signal.aborted && epoch.current === started) {
        workspace.setSession(token);
        await workspace.loadSources();
      }
    } catch (error) {
      if (!controller.signal.aborted && epoch.current === started)
        setLocalError(
          error instanceof LibraryClientError
            ? error.code
            : "pilot_signin_failed",
        );
    } finally {
      if (!controller.signal.aborted && epoch.current === started)
        setSigningIn(false);
    }
  }
  function logout() {
    epoch.current++;
    auth.current?.abort();
    workspace.setSession(null);
    setPanel(null);
    setDeleting(null);
    setQuery("");
    setSubmitted(null);
    setFilter("Everything");
    setLocalError(null);
    setSigningIn(false);
    refreshedJob.current = null;
  }
  function everything() {
    if (state.busy) return;
    workspace.clearSearch();
    setQuery("");
    setSubmitted(null);
    setFilter("Everything");
    setLocalError(null);
  }
  const readyImport =
    state.processing?.state === "ready" &&
    state.processing.version_id === state.imported?.version_id;
  const knownEmpty =
    !readyImport &&
    state.libraryStatus === "ready" &&
    !state.nextCursor &&
    state.sources.every((source) => !source.published_version_id);
  const error = localError ?? state.error;
  const notice = (
    <>
      {state.busy && (
        <div className="library-notice" role="status">
          Working on your request…{" "}
          <button className="quiet-button" onClick={() => workspace.cancel()}>
            Cancel request
          </button>
        </div>
      )}
      {error && (
        <p className="library-notice library-error" role="alert">
          {messages[error] ??
            "This action could not finish. Check Connection & account before trying again."}
        </p>
      )}
    </>
  );
  const grouped = new Map<string, SearchWindow[]>();
  for (const hit of state.results?.windows ?? []) {
    const id = `${hit.source_id}/${hit.version_id}`;
    grouped.set(id, [...(grouped.get(id) ?? []), hit]);
  }
  const groups = [...grouped.values()].filter(([hit]) =>
    matches(hit.title, filter),
  );
  const sources = state.sources.filter((source) =>
    matches(source.title, filter),
  );
  const showResults = state.results !== null;

  return (
    <div className="gather-library">
      <aside className="library-rail" aria-label="Workspace navigation">
        <button
          className="library-mark"
          aria-label="Gather library"
          disabled={state.busy}
          onClick={everything}
        >
          g<span>.</span>
        </button>
        <button
          className="rail-button selected"
          aria-label="Everything in your library"
          disabled={state.busy}
          onClick={everything}
        >
          <Icon kind="grid" />
        </button>
        <span className="rail-spacer" />
        <button
          className="rail-button"
          aria-label="Connection & account"
          onClick={() => setPanel("settings")}
        >
          <Icon kind="settings" />
        </button>
      </aside>
      <main className="library-main">
        <header className="library-topbar">
          <span className="library-wordmark">
            Gather<span>.</span>
          </span>
          <nav aria-label="Library navigation">
            <button
              className="top-link current"
              disabled={state.busy}
              onClick={everything}
            >
              Everything
            </button>
            <button
              className="add-file"
              disabled={
                !state.signedIn ||
                state.busy ||
                !!state.pendingImport ||
                !textFiles
              }
              onClick={() => setPanel("import")}
            >
              <Icon kind="add" />
              Add file
            </button>
          </nav>
        </header>
        <h1 className="sr-only">Your library</h1>
        <form
          className="library-search"
          onSubmit={(event) => {
            event.preventDefault();
            if (
              !state.signedIn ||
              state.busy ||
              !query.trim() ||
              knownEmpty ||
              state.modelStatus?.state === "model_budget_exhausted"
            )
              return;
            setSubmitted(query.trim());
            act(() => workspace.search(query.trim()));
          }}
        >
          <label className="sr-only" htmlFor="library-search">
            Search your library
          </label>
          <input
            id="library-search"
            ref={search}
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Find what’s on your mind…"
            autoComplete="off"
            disabled={!state.signedIn || state.busy}
            maxLength={2000}
          />
          <button
            className="search-submit"
            aria-label="Search saved files"
            disabled={
              !state.signedIn ||
              state.busy ||
              !query.trim() ||
              knownEmpty ||
              state.modelStatus?.state === "model_budget_exhausted"
            }
          >
            <Icon kind="search" />
            <span>Search</span>
          </button>
        </form>
        <div className="library-controls">
          <div className="library-filters" role="group" aria-label="File types">
            {filters
              .filter(
                (value) =>
                  value !== "PDFs" ||
                  state.pdfEnabled ||
                  state.sources.some((source) => /\.pdf$/i.test(source.title)),
              )
              .map((value) => (
                <button
                  key={value}
                  className={
                    filter === value ? "filter-chip active" : "filter-chip"
                  }
                  aria-pressed={filter === value}
                  onClick={() => setFilter(value)}
                >
                  {value}
                </button>
              ))}
          </div>
          {state.signedIn && (
            <button
              className="quiet-button"
              disabled={state.busy}
              onClick={() => {
                setSubmitted(null);
                act(() => workspace.loadSources());
              }}
            >
              Refresh library
            </button>
          )}
        </div>
        {!panel && !deleting && !state.opened && notice}
        {!state.signedIn ? (
          <section
            className="library-welcome"
            aria-labelledby="welcome-heading"
          >
            <div>
              <h2 id="welcome-heading">
                A little less searching.
                <br />A lot more finding.
              </h2>
              <p>
                Your saved files, together in one quiet place.
                <br />
                Sign in to open your private library.
              </p>
              <p className="welcome-scope">
                Private pilot · cloud processing · two existing accounts
              </p>
            </div>
            <form
              className="library-auth"
              onSubmit={(event) => void login(event)}
            >
              <label htmlFor="library-account">Account</label>
              <select
                id="library-account"
                value={email}
                disabled={signingIn}
                onChange={(event) => setEmail(event.target.value)}
              >
                {PILOT_EMAILS.map((account) => (
                  <option key={account}>{account}</option>
                ))}
              </select>
              <label htmlFor="library-password">Password</label>
              <input
                id="library-password"
                ref={password}
                type="password"
                autoComplete="current-password"
                required
                disabled={signingIn}
              />
              <button className="add-file" disabled={signingIn || !key}>
                {signingIn ? "Signing in…" : "Sign in"}
              </button>
              {!key && (
                <p role="status">
                  Public connection configuration is missing. Open the
                  configured private build.
                </p>
              )}
              <small>
                Your session stays in memory. After a refresh, sign in again.
              </small>
            </form>
          </section>
        ) : (
          <>
            <div className="library-summary">
              <p>
                {showResults ? (
                  <>
                    Results for <strong>“{submitted}”</strong>
                  </>
                ) : (
                  "Your saved collection"
                )}
              </p>
              {showResults ? (
                <button
                  className="quiet-button"
                  disabled={state.busy}
                  onClick={everything}
                >
                  Back to everything
                </button>
              ) : (
                <span>
                  {state.libraryStatus === "ready"
                    ? `${state.sources.length}${state.nextCursor ? "+" : ""} saved ${state.sources.length === 1 ? "file" : "files"}`
                    : state.libraryStatus === "loading"
                      ? "Loading…"
                      : "Library unavailable"}
                </span>
              )}
            </div>
            {state.libraryStatus === "loading" && (
              <p className="library-empty" role="status">
                Loading your saved files…
              </p>
            )}
            {state.libraryStatus === "error" && (
              <p className="library-empty" role="status">
                Your library could not load. Use Refresh library to try again.
              </p>
            )}
            <ul
              className="saved-grid"
              aria-label={showResults ? "Search results" : "Saved files"}
            >
              {showResults
                ? groups.map((windows) => {
                    const hit = windows[0];
                    return (
                      <li
                        className="saved-card result-card"
                        key={`${hit.source_id}/${hit.version_id}`}
                      >
                        <div className="card-meta">
                          <span>{fileLabel(hit.title)}</span>
                          <span className="ready-label">Matching passages</span>
                        </div>
                        <button
                          className="card-title"
                          disabled={state.busy}
                          onClick={() => {
                            setReaderPage(hit.pages?.[0] ?? null);
                            act(() =>
                              workspace.open(hit.source_id, hit.version_id),
                            );
                          }}
                        >
                          {hit.title}
                        </button>
                        {windows.map((window) => (
                          <div
                            className="passage"
                            key={`${window.start}/${window.end}`}
                          >
                            <p>{window.text}</p>
                            <small>
                              {window.pages ? (
                                <>
                                  Pages {window.pages.join(", ")} · extracted
                                  characters {window.start}–{window.end}
                                </>
                              ) : (
                                <>
                                  Characters {window.start}–{window.end}
                                </>
                              )}{" "}
                              · exact saved version
                            </small>
                          </div>
                        ))}
                        <div className="card-actions">
                          <button
                            className="quiet-button"
                            disabled={state.busy}
                            onClick={() => {
                              setReaderPage(hit.pages?.[0] ?? null);
                              act(() =>
                                workspace.open(hit.source_id, hit.version_id),
                              );
                            }}
                          >
                            Open saved text
                          </button>
                          <button
                            className="quiet-button danger-text"
                            disabled={state.busy}
                            aria-label={`Delete ${hit.title}`}
                            onClick={() => setDeleting(hit)}
                          >
                            Delete
                          </button>
                        </div>
                      </li>
                    );
                  })
                : sources.map((source) => (
                    <li
                      className={`saved-card ${source.published_version_id ? "published" : "unpublished"}`}
                      key={source.source_id}
                    >
                      <div className="card-meta">
                        <span>{fileLabel(source.title)}</span>
                        <time dateTime={source.created_at}>
                          {new Date(source.created_at).toLocaleDateString(
                            undefined,
                            { month: "short", day: "numeric" },
                          )}
                        </time>
                      </div>
                      <button
                        className="card-open"
                        aria-label={`Open ${source.title}`}
                        disabled={state.busy || !source.published_version_id}
                        onClick={() => {
                          setReaderPage(null);
                          act(() =>
                            workspace.open(
                              source.source_id,
                              source.published_version_id!,
                            ),
                          );
                        }}
                      >
                        <h2>{source.title}</h2>
                        <span
                          className={
                            source.published_version_id
                              ? "ready-label"
                              : "pending-label"
                          }
                        >
                          {statusLabel(source)}
                        </span>
                      </button>
                      {source.error_code && (
                        <p className="card-error">
                          Last attempt: {source.error_code}. {source.attempts}/3
                          attempts used.
                        </p>
                      )}
                      <div className="card-actions">
                        {source.job_id &&
                          source.attempts !== null &&
                          source.attempts < 3 &&
                          (source.state === "queued" ||
                            source.state === "processing") && (
                            <button
                              className="quiet-button"
                              disabled={state.busy}
                              aria-label={`Resume processing ${source.title}`}
                              onClick={() =>
                                act(async () => {
                                  await workspace.process(
                                    source.source_id,
                                    source.job_id!,
                                    source.attempts!,
                                  );
                                  if (!workspace.getSnapshot().error)
                                    await workspace.loadSources();
                                })
                              }
                            >
                              Resume processing
                            </button>
                          )}
                        <button
                          className="quiet-button danger-text"
                          disabled={state.busy}
                          aria-label={`Delete ${source.title}`}
                          onClick={() => setDeleting(source)}
                        >
                          Delete
                        </button>
                      </div>
                    </li>
                  ))}
            </ul>
            {state.libraryStatus === "ready" &&
              !(showResults ? groups.length : sources.length) && (
                <div className="library-empty" role="status">
                  <h2>
                    {showResults
                      ? "Nothing found this time."
                      : state.sources.length
                        ? "No files of this type yet."
                        : "Make room for your first find."}
                  </h2>
                  <p>
                    {showResults
                      ? "Try a different description, or check another file type."
                      : state.sources.length
                        ? "Choose Everything to see your other saved files."
                        : "Add a TXT or Markdown file. It will appear here while it processes."}
                  </p>
                </div>
              )}
            {knownEmpty && (
              <p className="library-footnote">
                No published files to search yet. Search becomes available after
                processing; an empty library makes no model request.
              </p>
            )}
            {!showResults && state.nextCursor && (
              <button
                className="load-more"
                disabled={state.busy}
                onClick={() => act(() => workspace.loadSources(true))}
              >
                Load more files
              </button>
            )}
            {state.imported && (
              <div className="library-notice" role="status">
                <span>
                  Saved. Processing:{" "}
                  <strong>{state.processing?.state ?? "not checked"}</strong>.{" "}
                  {state.processing?.state === "ready"
                    ? "Your file is available in this library."
                    : "Saving starts automatic processing. Failed attempts need an explicit retry."}
                </span>
                <button
                  className="quiet-button"
                  disabled={state.busy}
                  onClick={() => act(() => workspace.refreshStatus())}
                >
                  Refresh processing status
                </button>
              </div>
            )}
            {state.pendingImport && (
              <div className="library-notice" role="status">
                The save is unconfirmed. Retry the same import before selecting
                another file.
                <button
                  className="quiet-button"
                  disabled={state.busy}
                  onClick={() =>
                    act(async () => {
                      await workspace.retryImport();
                      if (!workspace.getSnapshot().error)
                        await workspace.loadSources();
                    })
                  }
                >
                  Retry same import
                </button>
              </div>
            )}
            {state.cleanupSources.length > 0 && (
              <section className="cleanup-list" aria-label="Pending cleanup">
                <h2>Cleanup pending</h2>
                <p>
                  These files are hidden from search. Stored data removal is not
                  confirmed yet.
                </p>
                {state.cleanupSources.map((id) => (
                  <div key={id}>
                    <code>{id}</code>
                    <button
                      className="quiet-button"
                      disabled={state.busy || !state.cleanupEnabled}
                      onClick={() => act(() => workspace.finishCleanup(id))}
                    >
                      Finish cleanup
                    </button>
                  </div>
                ))}
              </section>
            )}
            {state.cleanedSourceId && (
              <p className="library-footnote" role="status">
                Deletion complete. Active stored text and derived data were
                removed; a minimal retry receipt prevents an old import from
                restoring them.
              </p>
            )}
          </>
        )}
        <footer className="library-bottom">
          <span>
            {state.signedIn
              ? `Private library · ${email}`
              : "Only what you choose to save."}
          </span>
          <button className="quiet-button" onClick={() => setPanel("privacy")}>
            Privacy & processing
          </button>
        </footer>
      </main>
      {panel && (
        <PanelDialog
          title={
            panel === "import"
              ? "Add to your library"
              : panel === "settings"
                ? "Connection & account"
                : "Gather information"
          }
          dismiss={() => setPanel(null)}
        >
          {panel === "import" ? (
            <TextFileImport
              allowPdf={state.pdfEnabled}
              disabled={state.busy || !!state.pendingImport}
              onSave={async (file) => {
                const started = epoch.current;
                setLocalError(null);
                await workspace.importText(
                  file.title,
                  file.bytes,
                  file.media,
                  true,
                );
                if (started !== epoch.current) return false;
                const saved =
                  !workspace.getSnapshot().pendingImport &&
                  !workspace.getSnapshot().error;
                if (saved) {
                  setPanel(null);
                  setSubmitted(null);
                  setFilter("Everything");
                  await workspace.loadSources();
                }
                return saved;
              }}
            />
          ) : panel === "settings" ? (
            <>
              <p>
                {state.pdfEnabled
                  ? "PDF, TXT and Markdown. Text files use UTF-8;"
                  : "TXT and Markdown only, UTF-8,"}{" "}
                up to 64 KiB and three processing passages per file. This pilot
                has two source slots per account.
              </p>
              <p>
                Stored text and authentication use Supabase in Sydney.
                Embeddings use Gather’s CPU service in Mumbai. No model download
                is required.
              </p>
              {state.signedIn && (
                <>
                  <p>
                    Signed in as <strong>{email}</strong>
                  </p>
                  <button className="quiet-button" onClick={logout}>
                    Sign out
                  </button>
                  <ModelConnection
                    status={state.modelStatus}
                    busy={state.busy}
                    onCheck={() => act(() => workspace.checkModel())}
                  />
                </>
              )}
              <div className="settings-links">
                {(["privacy", "terms", "copyright"] as const).map((kind) => (
                  <button
                    className="quiet-button"
                    key={kind}
                    onClick={() => setPanel(kind)}
                  >
                    {kind === "terms"
                      ? "Pilot terms"
                      : kind === "copyright"
                        ? "Copyright"
                        : "Privacy"}
                  </button>
                ))}
              </div>
            </>
          ) : (
            <PolicyPage kind={panel} />
          )}
          {notice}
        </PanelDialog>
      )}
      {state.opened && (
        <PanelDialog
          title={state.opened.title}
          reader
          dismiss={() => workspace.closeSource()}
        >
          <p className="reader-version">Exact published version · plain text</p>
          <article className="saved-document" aria-label="Saved document text">
            {state.opened.pages
              ? state.opened.pages.map((page) => (
                  <section
                    className="pdf-page"
                    id={`pdf-page-${page.number}`}
                    key={page.number}
                  >
                    <h3>Page {page.number}</h3>
                    <div>
                      {Array.from(state.opened!.body)
                        .slice(page.start, page.end)
                        .join("")}
                    </div>
                  </section>
                ))
              : state.opened.body}
          </article>
          <div className="reader-actions">
            <button
              className="quiet-button danger-text"
              disabled={state.busy}
              onClick={() => {
                setDeleting(state.opened);
                workspace.closeSource();
              }}
            >
              Delete file
            </button>
          </div>
          {notice}
        </PanelDialog>
      )}
      {deleting && (
        <PanelDialog
          title="Delete this file?"
          dismiss={() => setDeleting(null)}
        >
          <p>
            <strong>{deleting.title}</strong> will disappear from search
            immediately. Gather will then remove its stored text and derived
            data. This cannot be undone.
          </p>
          <div className="delete-actions">
            <button
              className="quiet-button"
              disabled={state.busy}
              onClick={() => setDeleting(null)}
            >
              Keep file
            </button>
            <button
              className="add-file"
              disabled={state.busy}
              onClick={() =>
                act(async () => {
                  const started = epoch.current;
                  await workspace.delete(deleting.source_id);
                  if (started === epoch.current) setDeleting(null);
                })
              }
            >
              Delete file permanently
            </button>
          </div>
          {notice}
        </PanelDialog>
      )}
    </div>
  );
}
