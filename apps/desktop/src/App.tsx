import { lazy, Suspense, useEffect, useRef, useState } from "react";
import {
  FilterControl,
  ReadingPane,
  OrbPreview,
} from "./components/Interactions";
import { PolicyPage, type PolicyKind } from "./components/PolicyPage";
import { samples, models, type Sample } from "./fixtures";
import "./App.css";

// Removed from production builds; controlled operator pilot is browser-dev only.
const OperatorPilot = import.meta.env.DEV
  ? lazy(() => import("./components/OperatorPilot"))
  : null;
type Screen = "library" | "models" | "pilot" | PolicyKind;
const filters = ["All files", "Documents", "Presentations", "Photos"];

export default function App() {
  const [screen, setScreen] = useState<Screen>("library");
  const [filter, setFilter] = useState("All files");
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<Sample | null>(null);
  const [notice, setNotice] = useState("");
  const readerTitle = useRef<HTMLHeadingElement>(null);
  const sourceButton = useRef<HTMLButtonElement | null>(null);
  const sourceId = useRef<string | null>(null);
  const wasReading = useRef(false);
  useEffect(() => {
    if (selected) readerTitle.current?.focus();
    else if (wasReading.current) sourceButton.current?.focus();
    wasReading.current = !!selected;
  }, [selected]);
  const visible = samples.filter(
    (file) =>
      (filter === "All files" || file.category === filter) &&
      `${file.title} ${file.description} ${file.content}`
        .toLowerCase()
        .includes(query.toLowerCase().trim()),
  );
  function navigate(next: Screen) {
    setScreen(next);
    setSelected(null);
    setNotice("");
  }
  return (
    <div className="app">
      <aside className="sidebar">
        <button className="brand" onClick={() => navigate("library")}>
          <span className="brand-icon" aria-hidden="true">
            g
          </span>{" "}
          Gather<span className="brand-dot">.</span>
        </button>
        <p className="workspace-label">YOUR WORKSPACE</p>
        <nav aria-label="Main navigation">
          <button
            className={screen === "library" ? "nav active" : "nav"}
            aria-current={screen === "library" ? "page" : undefined}
            onClick={() => navigate("library")}
          >
            Library <span className="count">{samples.length}</span>
          </button>
          <button
            className={screen === "models" ? "nav active" : "nav"}
            aria-current={screen === "models" ? "page" : undefined}
            onClick={() => navigate("models")}
          >
            Models & setup
          </button>
          {OperatorPilot && (
            <button
              className={screen === "pilot" ? "nav active" : "nav"}
              aria-current={screen === "pilot" ? "page" : undefined}
              onClick={() => navigate("pilot")}
            >
              Operator pilot
            </button>
          )}
        </nav>
        <div className="sidebar-note">
          <p>
            Keep the source.
            <br />
            Find the detail.
          </p>
        </div>
        <div className="local-state">
          <span className="status-dot" />
          <div>
            {screen === "pilot" ? (
              <>
                Operator pilot<small>Restricted synthetic test workspace</small>
              </>
            ) : (
              <>
                Design preview
                <small>Synthetic files · no cloud connection</small>
              </>
            )}
          </div>
        </div>
        <nav className="policy-links" aria-label="Policies">
          <button onClick={() => navigate("privacy")}>Privacy</button>
          <button onClick={() => navigate("terms")}>Terms</button>
          <button onClick={() => navigate("copyright")}>Copyright</button>
        </nav>
        <div className="profile">
          <span className="avatar">G</span>
          <div>
            Your personal library<small>Working name: Gather</small>
          </div>
        </div>
      </aside>
      <main>
        <header className="topbar">
          <span>
            Workspace <span className="slash">/</span>{" "}
            {["privacy", "terms", "copyright"].includes(screen)
              ? "Policies"
              : screen === "models"
                ? "Models & setup"
                : screen === "pilot"
                  ? "Operator pilot"
                  : selected
                    ? "Document reader"
                    : "Library"}
          </span>
          <span className="preview-label">
            {screen === "pilot" ? "Restricted pilot" : "Sample workspace"}
          </span>
        </header>
        {["privacy", "terms", "copyright"].includes(screen) ? (
          <PolicyPage kind={screen as PolicyKind} />
        ) : screen === "pilot" && OperatorPilot ? (
          <Suspense
            fallback={
              <p className="content" role="status">
                Opening operator workspace…
              </p>
            }
          >
            <OperatorPilot />
          </Suspense>
        ) : screen === "models" ? (
          <section className="content">
            <div className="screen-heading">
              <h1>Models & setup</h1>
              <p className="subtitle">
                Cloud processing candidates. Local text benchmarks are complete;
                these services are not connected to this preview.
              </p>
            </div>
            <div className="model-list">
              {models.map((model) => (
                <article className="model-card" key={model.id}>
                  <div>
                    <span className="eyebrow">{model.role}</span>
                    <h2>{model.name}</h2>
                    <p>{model.description}</p>
                    <code>{model.id}</code>
                  </div>
                  <span className="tag">Not connected</span>
                </article>
              ))}
            </div>
            <OrbPreview />
            <div className="info-panel">
              <p>
                AI processing is planned for the cloud, with no model downloads
                required on your device. Hosting and Supabase are not connected
                in this preview. Provider and usage limits are still being
                decided.
              </p>
            </div>
          </section>
        ) : selected ? (
          <section className="reader-layout">
            <ReadingPane>
              <button className="back" onClick={() => setSelected(null)}>
                Back to library
              </button>
              <div className="reader-heading">
                <span className="tag">{selected.extension} · SAMPLE</span>
                <h1 ref={readerTitle} tabIndex={-1}>
                  {selected.title}
                </h1>
                <button className="back" onClick={() => navigate("copyright")}>
                  Copyright information
                </button>
                <p>{selected.description}</p>
              </div>
              <article className="paper">
                <span className="eyebrow">
                  SYNTHETIC CONTENT / {selected.location}
                </span>
                <h2>{selected.heading}</h2>
                {selected.content.split("\n\n").map((p) => (
                  <p key={p}>{p}</p>
                ))}
              </article>
            </ReadingPane>
            <aside className="chat">
              <div className="chat-title">
                <h2>Ask this document</h2>
              </div>
              <p className="scope">Source: {selected.title}</p>
              <div className="chat-empty">
                <h3>Questions about this file</h3>
                <p>
                  Answers will use this file, with citations you can follow back
                  to the source.
                </p>
                <span className="tag">Chat is not connected yet</span>
              </div>
              <div className="suggestions">
                <span>QUESTIONS YOU COULD ASK</span>
                <p>What are the main takeaways?</p>
                <p>Explain the important details.</p>
              </div>
            </aside>
          </section>
        ) : (
          <section className="content">
            <div className="page-heading">
              <div>
                <h1>Your library</h1>
                <p className="subtitle">
                  Search your documents, slides and photos from one place.
                </p>
              </div>
              <button
                className="primary"
                onClick={() =>
                  setNotice(
                    "Import is the next integration step. This preview does not read, upload or index your files.",
                  )
                }
              >
                Import files
              </button>
            </div>
            <div className="search-box">
              <span className="search-symbol" aria-hidden="true" />
              <input
                aria-label="Filter sample files"
                placeholder="Find a document, a photo, a half-remembered idea…"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
              {query && (
                <button className="clear" onClick={() => setQuery("")}>
                  Clear
                </button>
              )}
            </div>
            <p className="search-caption">
              Preview search matches sample text. Semantic search will arrive
              with the model connection.
            </p>
            <div className="section-bar">
              <FilterControl
                items={filters}
                value={filter}
                onChange={setFilter}
              />
              <span className="result-count" aria-live="polite">
                {visible.length} sample files
              </span>
            </div>
            {notice && (
              <div className="notice" role="status">
                <span>{notice}</span>
                <button
                  onClick={() => setNotice("")}
                  aria-label="Dismiss notification"
                >
                  ×
                </button>
              </div>
            )}
            <div className="file-grid">
              {visible.map((file) => (
                <button
                  className="file-card"
                  key={file.id}
                  ref={(element) => {
                    if (file.id === sourceId.current)
                      sourceButton.current = element;
                  }}
                  onClick={(event) => {
                    sourceId.current = file.id;
                    sourceButton.current = event.currentTarget;
                    setSelected(file);
                  }}
                >
                  <div className={`thumbnail ${file.art}`} aria-hidden="true">
                    <div className="mock-page">
                      <span className="file-format">{file.extension}</span>
                      <span>{file.cover}</span>
                      <i />
                      <i />
                      <i />
                    </div>
                    <span className="thumbnail-tag">{file.extension}</span>
                  </div>
                  <div className="card-body">
                    <span className="card-category">{file.category}</span>
                    <h2>{file.title}</h2>
                    <p>{file.description}</p>
                    <div className="card-footer">
                      <span>{file.location}</span>
                      <span className="open-cue" aria-hidden="true">
                        Open sample ↗
                      </span>
                    </div>
                  </div>
                </button>
              ))}
            </div>
            {visible.length === 0 && (
              <div className="empty">
                <h2>No sample files match.</h2>
                <p>Try “research”, “coast” or another file type.</p>
                <button
                  className="back"
                  onClick={() => {
                    setQuery("");
                    setFilter("All files");
                  }}
                >
                  Reset filters
                </button>
              </div>
            )}
            <footer className="library-footer">
              <span>
                Documents, slides, photos. One place to rediscover them.
              </span>
              <span>All content shown is fictional.</span>
            </footer>
          </section>
        )}
        <footer className="policy-footer" aria-label="Policy information">
          <button onClick={() => navigate("privacy")}>Privacy notice</button>
          <button onClick={() => navigate("terms")}>Preview terms</button>
          <button onClick={() => navigate("copyright")}>
            Copyright procedure
          </button>
        </footer>
      </main>
    </div>
  );
}
