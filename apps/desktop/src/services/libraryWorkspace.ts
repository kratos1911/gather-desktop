/** Session-scoped UI state. Consumers render text; no fixtures or credentials are stored here. */
import {
  LibraryClient,
  LibraryClientError,
  type ImportReceipt,
  type PreparedImport,
  type ProcessingStatus,
  type SearchResult,
  type SourceText,
  type LibrarySource,
} from "./libraryClient";

export type LibraryState = Readonly<{
  signedIn: boolean;
  busy: boolean;
  error: string | null;
  pendingImport: PreparedImport | null;
  imported: ImportReceipt | null;
  processing: ProcessingStatus | null;
  results: SearchResult | null;
  opened: SourceText | null;
  cleanupSourceId: string | null;
  sources: LibrarySource[];
  nextCursor: string | null;
  libraryStatus: "idle" | "loading" | "ready" | "error";
}>;
const initial = (): LibraryState => ({
  signedIn: false,
  busy: false,
  error: null,
  pendingImport: null,
  imported: null,
  processing: null,
  results: null,
  opened: null,
  cleanupSourceId: null,
  sources: [],
  nextCursor: null,
  libraryStatus: "idle",
});

export class LibraryWorkspace {
  private state = initial();
  private listeners = new Set<() => void>();
  private generation = 0;
  private request: AbortController | null = null;
  constructor(private readonly client: LibraryClient) {}
  getSnapshot = (): LibraryState => this.state;
  subscribe = (listener: () => void): (() => void) => {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  };
  private update(value: Partial<LibraryState>) {
    this.state = Object.freeze({ ...this.state, ...value });
    this.listeners.forEach((listener) => listener());
  }
  setSession(token: string | null) {
    this.client.setSession(token);
    this.request?.abort();
    this.generation++;
    this.state = initial();
    this.update({ signedIn: token !== null });
  }
  cancel() {
    this.request?.abort();
  }
  dispose() {
    this.setSession(null);
    this.listeners.clear();
  }

  private async perform<T>(
    action: (signal: AbortSignal) => Promise<T>,
    commit: (result: T) => void,
    failed?: () => void,
  ): Promise<void> {
    if (this.state.busy) throw new LibraryClientError("busy");
    if (!this.state.signedIn) throw new LibraryClientError("session_required");
    const controller = new AbortController(),
      generation = this.generation;
    this.request = controller;
    this.update({ busy: true, error: null });
    try {
      const value = await action(controller.signal);
      if (generation === this.generation && !controller.signal.aborted)
        commit(value);
    } catch (error) {
      if (generation === this.generation) {
        this.update({
          error:
            error instanceof LibraryClientError
              ? error.code
              : "operation_failed",
        });
        failed?.();
      }
    } finally {
      if (generation === this.generation) {
        this.request = null;
        this.update({ busy: false });
      }
    }
  }

  async importText(
    title: string,
    bytes: Uint8Array,
    media: PreparedImport["media"],
  ): Promise<void> {
    if (this.state.busy) throw new LibraryClientError("busy");
    if (this.state.pendingImport)
      throw new LibraryClientError("pending_import_requires_resolution");
    const prepared = this.client.prepareImport(title, bytes, media);
    this.update({ pendingImport: prepared });
    await this.retryImport();
  }
  async retryImport(): Promise<void> {
    const prepared = this.state.pendingImport;
    if (!prepared) throw new LibraryClientError("no_pending_import");
    await this.perform(
      (signal) => this.client.importText(prepared, signal),
      (receipt) => {
        this.update({
          pendingImport: null,
          imported: receipt,
          processing: null,
        });
      },
    );
  }
  async refreshStatus(): Promise<void> {
    const source = this.state.imported;
    if (!source) throw new LibraryClientError("no_imported_source");
    await this.perform(
      (signal) => this.client.status(source.source_id, signal),
      (rows) => this.update({ processing: rows[0] ?? null }),
    );
  }
  async loadSources(append = false): Promise<void> {
    if (this.state.busy) throw new LibraryClientError("busy");
    if (!this.state.signedIn) throw new LibraryClientError("session_required");
    const cursor = append ? this.state.nextCursor : null;
    if (append && cursor === null) return;
    this.update({
      libraryStatus: "loading",
      ...(append
        ? {}
        : {
            sources: [],
            nextCursor: null,
            opened: null,
            results: null,
          }),
    });
    await this.perform(
      (signal) => this.client.listSources(cursor, signal),
      (page) => {
        const existing = append ? this.state.sources : [];
        const known = new Set(existing.map((source) => source.source_id));
        this.update({
          sources: [
            ...existing,
            ...page.items.filter((source) => !known.has(source.source_id)),
          ],
          nextCursor: page.next_cursor,
          libraryStatus: "ready",
        });
      },
      () => this.update({ libraryStatus: "error" }),
    );
  }
  async search(query: string): Promise<void> {
    // Clear previous results immediately; do not display old hits under a new query.
    if (this.state.busy) throw new LibraryClientError("busy");
    this.update({ results: null, opened: null });
    await this.perform(
      (signal) => this.client.search(query, signal),
      (results) => this.update({ results }),
    );
  }
  async open(sourceId: string, versionId: string): Promise<void> {
    if (this.state.busy) throw new LibraryClientError("busy");
    this.update({ opened: null });
    await this.perform(
      (signal) => this.client.open(sourceId, versionId, signal),
      (opened) =>
        this.update({ opened, error: opened ? null : "source_unavailable" }),
    );
  }
  async delete(sourceId: string): Promise<void> {
    await this.perform(
      (signal) => this.client.delete(sourceId, signal),
      (deleted) => {
        if (!deleted) {
          this.update({ error: "source_unavailable" });
          return;
        }
        // Discard affected result set (byte/citation totals cannot be left stale).
        this.update({
          cleanupSourceId: sourceId,
          sources: this.state.sources.filter(
            (source) => source.source_id !== sourceId,
          ),
          results: this.state.results?.windows.some(
            (w) => w.source_id === sourceId,
          )
            ? null
            : this.state.results,
          opened:
            this.state.opened?.source_id === sourceId
              ? null
              : this.state.opened,
          imported:
            this.state.imported?.source_id === sourceId
              ? null
              : this.state.imported,
          processing:
            this.state.imported?.source_id === sourceId
              ? null
              : this.state.processing,
        });
      },
    );
  }
}
