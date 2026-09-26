import { useState } from "react";
import {
  FilterControl,
  ReadingPane,
  OrbPreview,
} from "./components/Interactions";
import { PolicyPage, type PolicyKind } from "./components/PolicyPage";
import { samples, models, type Sample } from "./fixtures";
import "./App.css";

type Screen = "library" | "models" | PolicyKind;
const filters = ["All files", "Documents", "Presentations", "Photos"];

export default function App() {
  const [screen, setScreen] = useState<Screen>("library");
  const [filter, setFilter] = useState("All files");
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<Sample | null>(null);
  const [notice, setNotice] = useState("");
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
            onClick={() => navigate("library")}
          >
            Library <span className="count">{samples.length}</span>
          </button>
          <button
            className={screen === "models" ? "nav active" : "nav"}
            onClick={() => navigate("models")}
          >
            Models & setup
          </button>
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
            Design preview<small>Synthetic files · no cloud connection</small>
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
                : selected
                  ? "Document reader"
                  : "Library"}
          </span>
          <span className="preview-label">Sample workspace</span>
        </header>
        {["privacy", "terms", "copyright"].includes(screen) ? (
          <PolicyPage kind={screen as PolicyKind} />
        ) : screen === "models" ? (
          <section className="content">
            <div className="screen-heading">
              <h1>Models & setup</h1>
              <p className="subtitle">
                Our recommended starting lineup. Downloads and benchmarking come
                next.
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
                  <span className="tag">Not installed</span>
                </article>
              ))}
            </div>
            <OrbPreview />
            <div className="info-panel">
              <p>
                Models run locally. Supabase stores the searchable index in the
                cloud, so search still needs internet. No model downloads or
                account connections happen in this preview.
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
                <h1>{selected.title}</h1>
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
                  onClick={() => setSelected(file)}
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
          <button onClick={() => navigate("copyright")}>Copyright procedure</button>
        </footer>
      </main>
    </div>
  );
}
