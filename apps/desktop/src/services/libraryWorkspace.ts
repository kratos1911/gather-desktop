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
import type { ModelStatus } from "./modelAvailability";

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
  cleanupSources: string[];
  cleanupEnabled: boolean;
  cleanedSourceId: string | null;
  modelStatus: ModelStatus | null;
  sources: LibrarySource[];
  nextCursor: string | null;
  libraryStatus: "idle" | "loading" | "ready" | "error";
  pdfEnabled: boolean;
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
  cleanupSources: [],
  cleanupEnabled: false,
  cleanedSourceId: null,
  modelStatus: null,
  sources: [],
  nextCursor: null,
  libraryStatus: "idle",
  pdfEnabled: false,
});

export class LibraryWorkspace {
  private state = initial();
  private listeners = new Set<() => void>();
  private generation = 0;
  private request: AbortController | null = null;
  private importUncertain = false;
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
    this.importUncertain = false;
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
    confirmCloudStorage = false,
  ): Promise<void> {
    if (this.state.busy) throw new LibraryClientError("busy");
    if (this.state.pendingImport)
      throw new LibraryClientError("pending_import_requires_resolution");
    const prepared = this.client.prepareImport(
      title,
      bytes,
      media,
      undefined,
      confirmCloudStorage,
    );
    this.importUncertain = false;
    this.update({ pendingImport: prepared });
    await this.retryImport();
  }
  async retryImport(): Promise<void> {
    const prepared = this.state.pendingImport;
    if (!prepared) throw new LibraryClientError("no_pending_import");
    await this.perform(
      (signal) => this.client.importText(prepared, signal),
      (receipt) => {
        this.importUncertain = false;
        this.update({
          pendingImport: null,
          imported: receipt,
          processing: null,
        });
      },
      () => {
        // A first, definite pre-admission refusal can be corrected. Never
        // discard an ID after an earlier ambiguous send, even if a retry is refused.
        if (
          !this.importUncertain &&
          [
            "invalid_request",
            "access_denied",
            "session_required",
            "busy",
            "pdf_size",
            "pdf_invalid",
            "pdf_invalid_output",
            "pdf_encrypted",
            "pdf_active_content",
            "pdf_page_limit",
            "pdf_text_required",
            "pdf_stream_limit",
            "pdf_text_limit",
            "pdf_parser_unavailable",
            "pdf_busy",
            "pdf_timeout",
          ].includes(this.state.error ?? "")
        ) {
          this.update({ pendingImport: null });
        } else {
          this.importUncertain = true;
        }
      },
    );
  }
  async refreshStatus(): Promise<void> {
    const source = this.state.imported;
    if (!source) throw new LibraryClientError("no_imported_source");
    await this.perform(
      (signal) => this.client.status(source.source_id, signal),
      (rows) => {
        const processing =
          rows.find(
            (row) =>
              row.job_id === source.job_id &&
              row.version_id === source.version_id,
          ) ?? null;
        this.update({
          processing,
          // Reuse the owned status read so recovery never uses an older
          // attempt from the initial library page. Ready still reloads the
          // publication metadata instead of guessing its active version.
          sources: this.state.sources.map((row) =>
            processing &&
            processing.state !== "ready" &&
            row.state !== "ready" &&
            row.source_id === source.source_id &&
            row.job_id === processing.job_id &&
            row.processing_version_id === processing.version_id &&
            processing.attempts >= (row.attempts ?? 0)
              ? {
                  ...row,
                  state: processing.state,
                  attempts: processing.attempts,
                  error_code: processing.error_code,
                  ...(processing.can_resume === undefined
                    ? {}
                    : { can_resume: processing.can_resume }),
                }
              : row,
          ),
        });
      },
    );
  }
  async process(
    sourceId: string,
    jobId: string,
    attempts: number,
  ): Promise<boolean> {
    const generation = this.generation;
    let rejected = false;
    let acceptedResult = false;
    await this.perform(
      (signal) => this.client.process(sourceId, jobId, attempts, signal),
      (accepted) => {
        acceptedResult = accepted;
        rejected = !accepted;
        const target = this.state.sources.find(
          (row) => row.source_id === sourceId && row.job_id === jobId,
        );
        const resumed = target?.processing_version_id
          ? {
              source_id: sourceId,
              job_id: jobId,
              version_id: target.processing_version_id,
              automatic_processing: true,
            }
          : this.state.imported?.job_id === jobId
            ? { ...this.state.imported }
            : null;
        this.update({
          error: null,
          ...(accepted && resumed
            ? {
                imported: resumed,
                processing: null,
              }
            : {}),
        });
      },
    );
    // A lease/job may change after rendering. Refresh metadata, never replay
    // processing or keep a misleading actionable card after a refusal.
    if (rejected && generation === this.generation && this.state.signedIn)
      await this.loadSources();
    return acceptedResult;
  }

  /** Bounded metadata refreshes only. Never submit/retry inference in a timer. */
  watchImport(): () => void {
    const source = this.state.imported;
    if (!source?.automatic_processing) return () => {};
    const generation = this.generation;
    let remaining = 30;
    const deadline = Date.now() + 300000;
    let stopped = false;
    let timer: ReturnType<typeof setTimeout>;
    const tick = async () => {
      if (
        stopped ||
        generation !== this.generation ||
        this.state.imported?.job_id !== source.job_id ||
        remaining-- <= 0 ||
        Date.now() >= deadline
      )
        return;
      if (this.state.busy) {
        timer = setTimeout(() => void tick(), 10000);
        return;
      }
      await this.refreshStatus();
      if (
        stopped ||
        generation !== this.generation ||
        this.state.imported?.job_id !== source.job_id
      )
        return;
      const status = this.state.processing;
      if (
        (this.state.error && this.state.error !== "busy") ||
        !status ||
        status.state === "ready" ||
        status.state === "failed" ||
        status.state === "cancelled" ||
        (status.state === "queued" && status.attempts > 0)
      )
        return;
      timer = setTimeout(() => void tick(), 10000);
    };
    timer = setTimeout(() => void tick(), 1000);
    return () => {
      stopped = true;
      clearTimeout(timer);
    };
  }
  async checkModel(): Promise<void> {
    await this.perform(
      (signal) => this.client.modelStatus(signal),
      (modelStatus) => this.update({ modelStatus }),
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
          cleanupSources: page.cleanup_source_ids ?? [],
          cleanupEnabled: page.cleanup_source_ids !== undefined,
          pdfEnabled: page.pdf_enabled === true,
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
  clearSearch(): void {
    if (this.state.busy) throw new LibraryClientError("busy");
    this.update({ results: null, opened: null, error: null });
  }
  closeSource(): void {
    this.update({ opened: null });
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
    const generation = this.generation;
    let hidden = false;
    await this.perform(
      (signal) => this.client.delete(sourceId, signal),
      (deleted) => {
        if (!deleted) {
          this.update({ error: "source_unavailable" });
          return;
        }
        // Discard affected result set (byte/citation totals cannot be left stale).
        hidden = true;
        this.update({
          cleanupSourceId: sourceId,
          cleanedSourceId: null,
          cleanupSources: [
            ...new Set([...this.state.cleanupSources, sourceId]),
          ],
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
    if (hidden && generation === this.generation && this.state.cleanupEnabled)
      await this.finishCleanup(sourceId);
  }

  async finishCleanup(sourceId: string): Promise<void> {
    await this.perform(
      (signal) => this.client.cleanup(sourceId, signal),
      (complete) => {
        if (!complete) {
          this.update({ error: "cleanup_pending" });
          return;
        }
        this.update({
          cleanupSources: this.state.cleanupSources.filter(
            (id) => id !== sourceId,
          ),
          cleanupSourceId:
            this.state.cleanupSourceId === sourceId
              ? null
              : this.state.cleanupSourceId,
          cleanedSourceId: sourceId,
        });
      },
    );
  }
}
