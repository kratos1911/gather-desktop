/** HTTP contract only. No UI activation, credential persistence or automatic retries. */
export type ImportReceipt = {
  source_id: string;
  version_id: string;
  job_id: string;
};
export type ProcessingStatus = {
  job_id: string;
  version_id: string;
  state: string;
  attempts: number;
  error_code: string | null;
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
    this.send = options.fetch ?? fetch;
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
    return {
      source_id: id(result.source_id),
      version_id: id(result.version_id),
      job_id: id(result.job_id),
    };
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
      if (!response.ok)
        throw new LibraryClientError(
          (
            {
              400: "invalid_request",
              401: "session_required",
              403: "access_denied",
              408: "timeout",
              429: "busy",
              504: "timeout",
            } as Record<number, string>
          )[response.status] ?? "service_unavailable",
        );
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
