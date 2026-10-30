/** HTTP contract only. No UI activation, credential persistence or automatic retries. */
import { MODEL_HTTP, type ModelStatus } from "./modelAvailability";
export type ImportReceipt = {
  source_id: string;
  version_id: string;
  job_id: string;
  automatic_processing?: boolean;
};
export type ProcessingStatus = {
  job_id: string;
  version_id: string;
  state: string;
  attempts: number;
  error_code: string | null;
};
export type LibrarySource = {
  source_id: string;
  title: string;
  kind: "file" | "bookmark";
  created_at: string;
  published_version_id: string | null;
  processing_version_id: string | null;
  job_id: string | null;
  state: "queued" | "processing" | "ready" | "failed" | "cancelled" | null;
  attempts: number | null;
  error_code: string | null;
};
export type SourcePage = {
  items: LibrarySource[];
  next_cursor: string | null;
  cleanup_source_ids?: string[];
};
export type SearchWindow = {
  source_id: string;
  version_id: string;
  source_sha256: string;
  title: string;
  text: string;
  start: number;
  end: number;
  offset_unit: "unicode_code_point";
  passage_ids: string[];
  seed_rank: number;
  similarity: number;
};
export type SearchResult = {
  version: string;
  windows: SearchWindow[];
  utf8_bytes: number;
  omitted_sources: { source_id: string; reason: string }[];
};
export type SourceText = {
  source_id: string;
  version_id: string;
  source_sha256: string;
  title: string;
  body: string;
  model_id: string;
  model_revision: string;
  dimensions: number;
  passages: { id: string; start: number; end: number }[];
};
export type PreparedImport = Readonly<{
  request_id: string;
  title: string;
  media: "text/plain" | "text/markdown";
  content_base64: string;
  source_id?: string;
  confirm_cloud_storage?: true;
}>;

const MAX_REPLY = 512 * 1024;
const uuidPattern =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
const hashPattern = /^[0-9a-f]{64}$/;
const encoder = new TextEncoder();
function record(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value))
    throw new LibraryClientError("invalid_response");
  return value as Record<string, unknown>;
}
function id(value: unknown): string {
  if (typeof value !== "string" || !uuidPattern.test(value))
    throw new LibraryClientError("invalid_identifier");
  return value;
}
function text(value: unknown): string {
  if (typeof value !== "string")
    throw new LibraryClientError("invalid_response");
  return value;
}
function number(value: unknown): number {
  if (typeof value !== "number" || !Number.isFinite(value))
    throw new LibraryClientError("invalid_response");
  return value;
}
function integer(value: unknown): number {
  const n = number(value);
  if (!Number.isSafeInteger(n) || n < 0)
    throw new LibraryClientError("invalid_response");
  return n;
}
function array(value: unknown, max: number): unknown[] {
  if (!Array.isArray(value) || value.length > max)
    throw new LibraryClientError("invalid_response");
  return value;
}
function hash(value: unknown): string {
  const s = text(value);
  if (!hashPattern.test(s)) throw new LibraryClientError("invalid_response");
  return s;
}
function identity(value: Record<string, unknown>) {
  return {
    source_id: id(value.source_id),
    version_id: id(value.version_id),
    source_sha256: hash(value.source_sha256),
    title: text(value.title),
  };
}
function offsets(value: Record<string, unknown>, body: string) {
  const start = integer(value.start),
    end = integer(value.end);
  if (end <= start || end - start !== Array.from(body).length)
    throw new LibraryClientError("invalid_response");
  return { start, end };
}
export class LibraryClientError extends Error {
  constructor(public readonly code: string) {
    super(code);
    this.name = "LibraryClientError";
  }
}

export class LibraryClient {
  private readonly base: string;
  private readonly send: typeof fetch;
  private token: string | null = null;
  private generation = 0;
  private active: AbortController | null = null;
  private prepared = new WeakMap<PreparedImport, number>();

  constructor(
    base: string,
    options: { fetch?: typeof fetch; allowLoopback?: boolean } = {},
  ) {
    const url = new URL(base);
    if (
      url.username ||
      url.password ||
      url.search ||
      url.hash ||
      url.pathname !== "/" ||
      (url.protocol !== "https:" &&
        !(
          options.allowLoopback === true &&
          url.protocol === "http:" &&
          url.hostname === "127.0.0.1"
        ))
    ) {
      throw new LibraryClientError("invalid_configuration");
    }
    this.base = url.origin;
    // Keep native fetch as a plain function call. Calling it as this.send()
    // with a LibraryClient receiver causes Illegal invocation in Chromium.
    const transport = options.fetch ?? fetch;
    this.send = (input, init) => transport(input, init);
  }

  setSession(token: string | null): void {
    if (
      token !== null &&
      (!token || token.length > 8192 || /[^\x21-\x7e]/.test(token))
    )
      throw new LibraryClientError("invalid_session");
    this.active?.abort();
    this.generation++;
    this.prepared = new WeakMap();
    this.token = token;
  }

  prepareImport(
    title: string,
    bytes: Uint8Array,
    media: PreparedImport["media"],
    sourceId?: string,
    confirmCloudStorage = false,
  ): PreparedImport {
    if (!this.token) throw new LibraryClientError("session_required");
    if (
      !title.trim() ||
      Array.from(title).length > 500 ||
      bytes.byteLength < 1 ||
      bytes.byteLength > 65536 ||
      !["text/plain", "text/markdown"].includes(media)
    )
      throw new LibraryClientError("invalid_import");
    try {
      new TextDecoder("utf-8", { fatal: true }).decode(bytes);
    } catch {
      throw new LibraryClientError("invalid_import");
    }
    let binary = "";
    for (const byte of bytes) binary += String.fromCharCode(byte);
    const value = Object.freeze({
      request_id: crypto.randomUUID(),
      title,
      media,
      content_base64: btoa(binary),
      ...(sourceId ? { source_id: id(sourceId) } : {}),
      ...(confirmCloudStorage ? { confirm_cloud_storage: true as const } : {}),
    });
    this.prepared.set(value, this.generation);
    return value;
  }

  async importText(
    value: PreparedImport,
    signal?: AbortSignal,
  ): Promise<ImportReceipt> {
    if (this.prepared.get(value) !== this.generation)
      throw new LibraryClientError("stale_import");
    const result = record(await this.request("import", value, signal));
    if (
      result.automatic_processing !== undefined &&
      typeof result.automatic_processing !== "boolean"
    )
      throw new LibraryClientError("invalid_response");
    return {
      source_id: id(result.source_id),
      version_id: id(result.version_id),
      job_id: id(result.job_id),
      ...(result.automatic_processing === undefined
        ? {}
        : { automatic_processing: result.automatic_processing }),
    };
  }

  async process(
    sourceId: string,
    jobId: string,
    expectedAttempts: number,
    signal?: AbortSignal,
  ): Promise<boolean> {
    if (
      !Number.isInteger(expectedAttempts) ||
      expectedAttempts < 0 ||
      expectedAttempts > 2
    )
      throw new LibraryClientError("invalid_request");
    const result = await this.request(
      "process",
      {
        source_id: id(sourceId),
        job_id: id(jobId),
        expected_attempts: expectedAttempts,
      },
      signal,
    );
    if (typeof result !== "boolean")
      throw new LibraryClientError("invalid_response");
    return result;
  }

  async cleanup(sourceId: string, signal?: AbortSignal): Promise<boolean> {
    const result = await this.request(
      "cleanup",
      { source_id: id(sourceId) },
      signal,
    );
    if (typeof result !== "boolean")
      throw new LibraryClientError("invalid_response");
    return result;
  }

  async status(
    sourceId: string,
    signal?: AbortSignal,
  ): Promise<ProcessingStatus[]> {
    return array(
      await this.request("status", { source_id: id(sourceId) }, signal),
      1,
    ).map((row) => {
      const value = record(row),
        state = text(value.state),
        attempts = integer(value.attempts);
      if (
        !["queued", "processing", "ready", "failed", "cancelled"].includes(
          state,
        ) ||
        attempts > 3
      )
        throw new LibraryClientError("invalid_response");
      return {
        job_id: id(value.job_id),
        version_id: id(value.version_id),
        state,
        attempts,
        error_code: value.error_code === null ? null : text(value.error_code),
      };
    });
  }

  async listSources(
    cursor: string | null = null,
    signal?: AbortSignal,
  ): Promise<SourcePage> {
    if (
      cursor !== null &&
      (!/^[A-Za-z0-9_-]+$/.test(cursor) || cursor.length > 256)
    )
      throw new LibraryClientError("invalid_cursor");
    const result = record(
      await this.request("list", { limit: 20, cursor }, signal),
    );
    const next = result.next_cursor;
    if (
      next !== null &&
      (typeof next !== "string" ||
        next.length > 256 ||
        !/^[A-Za-z0-9_-]+$/.test(next) ||
        next === cursor)
    )
      throw new LibraryClientError("invalid_response");
    const items = array(result.items, 20).map((row): LibrarySource => {
      const value = record(row);
      const title = text(value.title),
        created = text(value.created_at);
      const state = value.state as LibrarySource["state"];
      if (
        !title.trim() ||
        Array.from(title).length > 500 ||
        !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z$/.test(created) ||
        !Number.isFinite(Date.parse(created)) ||
        !["file", "bookmark"].includes(text(value.kind)) ||
        (state !== null &&
          !["queued", "processing", "ready", "failed", "cancelled"].includes(
            state,
          ))
      )
        throw new LibraryClientError("invalid_response");
      const source: LibrarySource = {
        source_id: id(value.source_id),
        title,
        kind: value.kind as LibrarySource["kind"],
        created_at: created,
        published_version_id:
          value.published_version_id === null
            ? null
            : id(value.published_version_id),
        processing_version_id:
          value.processing_version_id === null
            ? null
            : id(value.processing_version_id),
        job_id: value.job_id === null ? null : id(value.job_id),
        state,
        attempts: value.attempts === null ? null : integer(value.attempts),
        error_code: value.error_code === null ? null : text(value.error_code),
      };
      if (
        (source.job_id === null
          ? [
              source.processing_version_id,
              state,
              source.attempts,
              source.error_code,
            ].some((v) => v !== null)
          : source.processing_version_id === null ||
            state === null ||
            source.attempts === null ||
            source.attempts > 3) ||
        (state === "ready" &&
          source.published_version_id !== source.processing_version_id)
      )
        throw new LibraryClientError("invalid_response");
      return source;
    });
    if (
      new Set(items.map((item) => item.source_id)).size !== items.length ||
      (next !== null && items.length !== 20)
    )
      throw new LibraryClientError("invalid_response");
    const cleanup =
      result.cleanup_source_ids === undefined
        ? undefined
        : array(result.cleanup_source_ids, 20).map(id);
    if (cleanup && new Set(cleanup).size !== cleanup.length)
      throw new LibraryClientError("invalid_response");
    return {
      items,
      next_cursor: next,
      ...(cleanup === undefined ? {} : { cleanup_source_ids: cleanup }),
    };
  }

  async search(query: string, signal?: AbortSignal): Promise<SearchResult> {
    if (!query.trim() || encoder.encode(query).length > 8192)
      throw new LibraryClientError("invalid_query");
    const result = record(
      await this.request("search", { query, limit: 20 }, signal),
    );
    if (result.version !== "source-neighbors-v1")
      throw new LibraryClientError("invalid_response");
    const windows = array(result.windows, 5).map((row) => {
      const value = record(row),
        body = text(value.text);
      if (
        value.offset_unit !== "unicode_code_point" ||
        encoder.encode(body).length > 8192
      )
        throw new LibraryClientError("invalid_response");
      return {
        ...identity(value),
        ...offsets(value, body),
        text: body,
        offset_unit: "unicode_code_point" as const,
        passage_ids: array(value.passage_ids, 256).map(text),
        seed_rank: integer(value.seed_rank),
        similarity: number(value.similarity),
      };
    });
    const size = integer(result.utf8_bytes);
    if (
      size > 32768 ||
      size !== windows.reduce((n, w) => n + encoder.encode(w.text).length, 0)
    )
      throw new LibraryClientError("invalid_response");
    return {
      version: result.version,
      windows,
      utf8_bytes: size,
      omitted_sources: array(result.omitted_sources, 100).map((row) => {
        const value = record(row);
        return { source_id: id(value.source_id), reason: text(value.reason) };
      }),
    };
  }

  async open(
    sourceId: string,
    versionId: string,
    signal?: AbortSignal,
  ): Promise<SourceText | null> {
    const rows = array(
      await this.request(
        "open",
        { source_id: id(sourceId), version_id: id(versionId) },
        signal,
      ),
      1,
    );
    if (!rows.length) return null;
    const value = record(rows[0]),
      body = text(value.body),
      length = Array.from(body).length;
    if (
      value.source_id !== sourceId ||
      value.version_id !== versionId ||
      encoder.encode(body).length > 65536
    )
      throw new LibraryClientError("invalid_response");
    const passages = array(value.passages, 256).map((row) => {
      const passage = record(row),
        start = integer(passage.start),
        end = integer(passage.end);
      if (end <= start || end > length)
        throw new LibraryClientError("invalid_response");
      return { id: text(passage.id), start, end };
    });
    return {
      ...identity(value),
      body,
      passages,
      model_id: text(value.model_id),
      model_revision: text(value.model_revision),
      dimensions: integer(value.dimensions),
    };
  }

  async delete(sourceId: string, signal?: AbortSignal): Promise<boolean> {
    const value = await this.request(
      "delete",
      { source_id: id(sourceId) },
      signal,
    );
    if (typeof value !== "boolean")
      throw new LibraryClientError("invalid_response");
    return value;
  }

  async modelStatus(signal?: AbortSignal): Promise<ModelStatus> {
    const value = record(await this.request("model-status", {}, signal));
    const state = text(value.state),
      used = integer(value.used);
    if (
      Object.keys(value).length !== 3 ||
      value.limit !== 3 ||
      used > 3 ||
      (state !== "ready" &&
        !Object.prototype.hasOwnProperty.call(MODEL_HTTP, state)) ||
      (state === "model_budget_exhausted") !== (used === 3)
    )
      throw new LibraryClientError("invalid_response");
    return { state, used, limit: 3 };
  }

  private async request(
    route: string,
    payload: unknown,
    signal?: AbortSignal,
  ): Promise<unknown> {
    if (!this.token) throw new LibraryClientError("session_required");
    if (this.active) throw new LibraryClientError("busy");
    if (signal?.aborted) throw new LibraryClientError("cancelled");
    const controller = new AbortController(),
      generation = this.generation;
    this.active = controller;
    let timedOut = false;
    const timeout = setTimeout(() => {
      timedOut = true;
      controller.abort();
    }, 30000);
    const abort = () => controller.abort();
    signal?.addEventListener("abort", abort, { once: true });
    let reader: ReadableStreamDefaultReader<Uint8Array> | undefined;
    try {
      const response = await this.send(`${this.base}/v1/${route}`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${this.token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
        signal: controller.signal,
        credentials: "omit",
        redirect: "error",
        cache: "no-store",
      });
      if (generation !== this.generation)
        throw new LibraryClientError("session_changed");
      if (controller.signal.aborted)
        throw new LibraryClientError(timedOut ? "timeout" : "cancelled");
      if (!response.ok) {
        let specific: string | null = null;
        // Error details are bounded separately and accepted only as exact,
        // known code/status pairs. Unknown/error-page content never reaches UI.
        try {
          if (
            response.headers.get("content-type")?.split(";")[0] ===
              "application/json" &&
            response.body
          ) {
            reader = response.body.getReader();
            const chunks: Uint8Array[] = [];
            let size = 0;
            while (true) {
              const part = await reader.read();
              if (part.done) break;
              size += part.value.byteLength;
              if (size > 4096) throw new Error();
              chunks.push(part.value);
            }
            const bytes = new Uint8Array(size);
            let offset = 0;
            for (const chunk of chunks) {
              bytes.set(chunk, offset);
              offset += chunk.byteLength;
            }
            const value = record(
              JSON.parse(
                new TextDecoder("utf-8", { fatal: true }).decode(bytes),
              ),
            );
            if (
              Object.keys(value).length === 1 &&
              typeof value.error === "string" &&
              Object.prototype.hasOwnProperty.call(MODEL_HTTP, value.error) &&
              MODEL_HTTP[value.error] === response.status
            )
              specific = value.error;
          }
        } catch {
          /* Keep the fixed HTTP fallback, never raw body text. */
        }
        if (specific) throw new LibraryClientError(specific);
        throw new LibraryClientError(
          (
            {
              400: "invalid_request",
              401: "session_required",
              403: "access_denied",
              408: "timeout",
              429: "busy",
              502: "model_unavailable",
              503: "library_unavailable",
              504: "timeout",
            } as Record<number, string>
          )[response.status] ?? "service_unavailable",
        );
      }
      if (
        response.status !== (route === "import" ? 202 : 200) ||
        response.headers.get("content-type")?.split(";")[0] !==
          "application/json" ||
        !response.body
      )
        throw new LibraryClientError("invalid_response");
      reader = response.body.getReader();
      const chunks: Uint8Array[] = [];
      let size = 0;
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        size += value.byteLength;
        if (size > MAX_REPLY) throw new LibraryClientError("invalid_response");
        chunks.push(value);
      }
      if (generation !== this.generation)
        throw new LibraryClientError("session_changed");
      if (controller.signal.aborted)
        throw new LibraryClientError(timedOut ? "timeout" : "cancelled");
      const raw = new Uint8Array(size);
      let cursor = 0;
      for (const chunk of chunks) {
        raw.set(chunk, cursor);
        cursor += chunk.byteLength;
      }
      try {
        return JSON.parse(
          new TextDecoder("utf-8", { fatal: true }).decode(raw),
        );
      } catch {
        throw new LibraryClientError("invalid_response");
      }
    } catch (error) {
      if (generation !== this.generation)
        throw new LibraryClientError("session_changed");
      if (controller.signal.aborted)
        throw new LibraryClientError(timedOut ? "timeout" : "cancelled");
      if (error instanceof LibraryClientError) throw error;
      throw new LibraryClientError("network_unavailable");
    } finally {
      controller.abort();
      void reader?.cancel().catch(() => {});
      clearTimeout(timeout);
      signal?.removeEventListener("abort", abort);
      if (this.active === controller) this.active = null;
    }
  }
}
