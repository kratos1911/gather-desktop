/** HTTP contract only. No UI activation, credential persistence or automatic retries. */
import { MODEL_HTTP, type ModelStatus } from "./modelAvailability";
export const DOCX_MEDIA =
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document" as const;
export type ImageMedia = "image/png" | "image/jpeg";
export type OCRRegion = {
  number: number;
  start: number;
  end: number;
  x: number;
  y: number;
  width: number;
  height: number;
  confidence: number;
};
export function isImageMedia(value: unknown): value is ImageMedia {
  return value === "image/png" || value === "image/jpeg";
}
export function imageDataURL(media: ImageMedia, bytes: Uint8Array): string {
  let binary = "";
  for (let i = 0; i < bytes.length; i += 8192)
    binary += String.fromCharCode(...bytes.subarray(i, i + 8192));
  return `data:${media};base64,${btoa(binary)}`;
}
export type DocumentMedia =
  | "text/plain"
  | "text/markdown"
  | "application/pdf"
  | typeof DOCX_MEDIA
  | ImageMedia;
export type SavedOriginal = {
  title: string;
  media: DocumentMedia;
  bytes: Uint8Array<ArrayBuffer>;
};
export type ImportReceipt = {
  source_id: string;
  version_id: string;
  job_id: string;
  automatic_processing?: boolean;
};
export type ProcessingStatus = {
  job_id: string;
  version_id: string;
  state: NonNullable<LibrarySource["state"]>;
  attempts: number;
  error_code: string | null;
  can_resume?: boolean;
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
  can_resume?: boolean;
  preview?: string | null;
};
export type SourcePage = {
  items: LibrarySource[];
  next_cursor: string | null;
  cleanup_source_ids?: string[];
  pdf_enabled?: boolean;
  docx_enabled?: boolean;
  image_enabled?: boolean;
  search_previews_enabled?: boolean;
  original_open_enabled?: boolean;
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
  media_type?: "application/pdf" | typeof DOCX_MEDIA | ImageMedia;
  pages?: number[];
  paragraphs?: number[];
  ocr_regions?: number[];
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
  media_type?: "application/pdf" | typeof DOCX_MEDIA | ImageMedia;
  text_sha256?: string;
  pages?: { number: number; start: number; end: number }[];
  paragraphs?: { number: number; start: number; end: number }[];
  regions?: OCRRegion[];
  width?: number;
  height?: number;
  image_base64?: string;
  engine?: string;
  ocr_model_sha256?: string;
  language?: string;
};
export type PreparedImport = Readonly<{
  request_id: string;
  title: string;
  media: DocumentMedia;
  content_base64: string;
  source_id?: string;
  confirm_cloud_storage?: true;
}>;

const MAX_REPLY = 512 * 1024;
const ERROR_HTTP: Record<string, number> = {
  ...MODEL_HTTP,
  image_size: 400,
  image_invalid: 400,
  image_dimensions: 400,
  image_animated: 400,
  image_text_required: 400,
  image_text_limit: 400,
  image_region_limit: 400,
  image_invalid_output: 400,
  image_parser_unavailable: 503,
  image_busy: 429,
  image_timeout: 504,
  image_cancelled: 400,
  docx_size: 400,
  docx_invalid: 400,
  docx_invalid_output: 400,
  docx_archive_limit: 400,
  docx_active_content: 400,
  docx_unsupported_content: 400,
  docx_text_required: 400,
  docx_text_limit: 400,
  docx_paragraph_limit: 400,
  docx_parser_unavailable: 503,
  docx_busy: 429,
  docx_timeout: 504,
  docx_cancelled: 400,
  pdf_size: 400,
  pdf_invalid: 400,
  pdf_invalid_output: 400,
  pdf_encrypted: 400,
  pdf_active_content: 400,
  pdf_page_limit: 400,
  pdf_text_required: 400,
  pdf_stream_limit: 400,
  pdf_text_limit: 400,
  pdf_parser_unavailable: 503,
  pdf_busy: 429,
  pdf_timeout: 504,
  pdf_cancelled: 400,
};
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
export function validImageBytes(bytes: Uint8Array, media: ImageMedia): boolean {
  const bounded = (w: number, h: number) =>
    w > 0 && h > 0 && w <= 4096 && h <= 4096 && w * h <= 1048576;
  if (!bytes.length || bytes.length > 65536) return false;
  if (media === "image/png") {
    if (
      bytes.length < 33 ||
      String.fromCharCode(...bytes.slice(0, 8)) !== "\x89PNG\r\n\x1a\n"
    )
      return false;
    const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
    if (
      view.getUint32(8) !== 13 ||
      String.fromCharCode(...bytes.slice(12, 16)) !== "IHDR" ||
      !bounded(view.getUint32(16), view.getUint32(20))
    )
      return false;
    let position = 8,
      chunks = 0;
    while (position + 12 <= bytes.length && chunks++ < 128) {
      const size = view.getUint32(position),
        kind = String.fromCharCode(...bytes.slice(position + 4, position + 8));
      if (size > bytes.length - position - 12 || kind === "acTL") return false;
      position += size + 12;
      if (kind === "IEND") return size === 0 && position === bytes.length;
    }
    return false;
  }
  if (
    bytes[0] !== 255 ||
    bytes[1] !== 216 ||
    bytes[bytes.length - 2] !== 255 ||
    bytes[bytes.length - 1] !== 217
  )
    return false;
  let position = 2;
  while (position + 4 <= bytes.length) {
    if (bytes[position++] !== 255) return false;
    while (bytes[position] === 255) position++;
    const marker = bytes[position++],
      size = bytes[position] * 256 + bytes[position + 1];
    if (size < 2 || position + size > bytes.length) return false;
    if (marker >= 192 && marker <= 207 && ![196, 200, 204].includes(marker))
      return (
        size >= 8 &&
        bounded(
          bytes[position + 5] * 256 + bytes[position + 6],
          bytes[position + 3] * 256 + bytes[position + 4],
        )
      );
    if (marker === 218 || marker === 217) return false;
    position += size;
  }
  return false;
}
function imageMetadata(
  value: Record<string, unknown>,
  body: string,
): Partial<SourceText> {
  const width = integer(value.width),
    height = integer(value.height),
    length = Array.from(body).length;
  if (
    !width ||
    !height ||
    width > 4096 ||
    height > 4096 ||
    width * height > 1048576 ||
    value.engine !== "tesseract-5.5.0-lstm" ||
    value.language !== "eng" ||
    value.ocr_model_sha256 !==
      "7d4322bd2a7749724879683fc3912cb542f19906c83bcc1a52132556427170b2" ||
    value.pages !== undefined ||
    value.paragraphs !== undefined
  )
    throw new LibraryClientError("invalid_response");
  let previous = 0;
  const regions = array(value.regions, 128).map((row, index): OCRRegion => {
    const r = record(row);
    const region = {
      number: integer(r.number),
      start: integer(r.start),
      end: integer(r.end),
      x: integer(r.x),
      y: integer(r.y),
      width: integer(r.width),
      height: integer(r.height),
      confidence: number(r.confidence),
    };
    if (
      region.number !== index + 1 ||
      region.start !== previous ||
      region.end <= previous ||
      region.end > length ||
      !region.width ||
      !region.height ||
      region.x + region.width > width ||
      region.y + region.height > height ||
      region.confidence < 0 ||
      region.confidence > 100 ||
      !Array.from(body).slice(region.start, region.end).join("").trim()
    )
      throw new LibraryClientError("invalid_response");
    previous = region.end;
    return region;
  });
  const encoded = text(value.image_base64);
  if (
    !regions.length ||
    previous !== length ||
    !encoded ||
    encoded.length > 87384 ||
    encoded.length % 4 ||
    !/^[A-Za-z0-9+/]+={0,2}$/.test(encoded)
  )
    throw new LibraryClientError("invalid_response");
  return {
    media_type: value.media_type as ImageMedia,
    text_sha256: hash(value.text_sha256),
    regions,
    width,
    height,
    image_base64: encoded,
    engine: text(value.engine),
    ocr_model_sha256: text(value.ocr_model_sha256),
    language: "eng",
  };
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
      ![
        "text/plain",
        "text/markdown",
        "application/pdf",
        DOCX_MEDIA,
        "image/png",
        "image/jpeg",
      ].includes(media)
    )
      throw new LibraryClientError("invalid_import");
    try {
      if (isImageMedia(media)) {
        if (!validImageBytes(bytes, media)) throw new Error();
      } else if (media === DOCX_MEDIA) {
        if (String.fromCharCode(...bytes.slice(0, 4)) !== "PK\x03\x04")
          throw new Error();
      } else if (media !== "application/pdf")
        new TextDecoder("utf-8", { fatal: true }).decode(bytes);
      else if (String.fromCharCode(...bytes.slice(0, 5)) !== "%PDF-")
        throw new Error();
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
        attempts > 3 ||
        (value.can_resume !== undefined &&
          typeof value.can_resume !== "boolean") ||
        (value.can_resume === true &&
          (attempts >= 3 || !["queued", "processing"].includes(state)))
      )
        throw new LibraryClientError("invalid_response");
      return {
        job_id: id(value.job_id),
        version_id: id(value.version_id),
        state: state as ProcessingStatus["state"],
        attempts,
        error_code: value.error_code === null ? null : text(value.error_code),
        ...(value.can_resume === undefined
          ? {}
          : { can_resume: value.can_resume as boolean }),
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
        ...(value.can_resume === undefined
          ? {}
          : { can_resume: value.can_resume as boolean }),
      };
      if (value.preview !== undefined) {
        const preview = value.preview === null ? null : text(value.preview);
        if (
          preview !== null &&
          (!source.published_version_id || Array.from(preview).length > 240)
        )
          throw new LibraryClientError("invalid_response");
        source.preview = preview?.trim() ? preview : null;
      }
      if (
        (value.can_resume !== undefined &&
          typeof value.can_resume !== "boolean") ||
        (value.can_resume === true &&
          (source.job_id === null ||
            source.attempts === null ||
            source.attempts >= 3 ||
            !["queued", "processing"].includes(state ?? ""))) ||
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
    if (
      (result.pdf_enabled !== undefined &&
        typeof result.pdf_enabled !== "boolean") ||
      (result.docx_enabled !== undefined &&
        typeof result.docx_enabled !== "boolean") ||
      (result.image_enabled !== undefined &&
        typeof result.image_enabled !== "boolean") ||
      (result.search_previews_enabled !== undefined &&
        typeof result.search_previews_enabled !== "boolean") ||
      (result.original_open_enabled !== undefined &&
        typeof result.original_open_enabled !== "boolean")
    )
      throw new LibraryClientError("invalid_response");
    return {
      items,
      next_cursor: next,
      ...(cleanup === undefined ? {} : { cleanup_source_ids: cleanup }),
      ...(result.docx_enabled === undefined
        ? {}
        : { docx_enabled: result.docx_enabled as boolean }),
      ...(result.image_enabled === undefined
        ? {}
        : { image_enabled: result.image_enabled as boolean }),
      ...(result.pdf_enabled === undefined
        ? {}
        : { pdf_enabled: result.pdf_enabled }),
      ...(result.search_previews_enabled === undefined
        ? {}
        : { search_previews_enabled: result.search_previews_enabled }),
      ...(result.original_open_enabled === undefined
        ? {}
        : { original_open_enabled: result.original_open_enabled }),
    };
  }

  async search(
    query: string,
    signal?: AbortSignal,
    compact = false,
  ): Promise<SearchResult> {
    if (!query.trim() || encoder.encode(query).length > 8192)
      throw new LibraryClientError("invalid_query");
    const result = record(
      await this.request(
        compact ? "search-previews" : "search",
        { query, limit: 20 },
        signal,
      ),
    );
    const version = compact ? "search-previews-v1" : "source-neighbors-v1";
    if (result.version !== version)
      throw new LibraryClientError("invalid_response");
    const windows = array(result.windows, 5).map((row) => {
      const value = record(row),
        body = text(value.text);
      if (
        value.offset_unit !== "unicode_code_point" ||
        encoder.encode(body).length > 8192 ||
        (compact && (!body.trim() || Array.from(body).length > 240))
      )
        throw new LibraryClientError("invalid_response");
      let locations: Pick<
        SearchWindow,
        "media_type" | "pages" | "paragraphs" | "ocr_regions"
      > = {};
      if (isImageMedia(value.media_type)) {
        const numbers = array(value.ocr_regions, 128).map(integer);
        if (
          value.pages !== undefined ||
          value.paragraphs !== undefined ||
          !numbers.length ||
          numbers.some(
            (n, i) => n < 1 || n > 128 || (i > 0 && n <= numbers[i - 1]),
          )
        )
          throw new LibraryClientError("invalid_response");
        locations = { media_type: value.media_type, ocr_regions: numbers };
      } else if (
        value.media_type !== undefined ||
        value.pages !== undefined ||
        value.paragraphs !== undefined ||
        value.ocr_regions !== undefined
      ) {
        const docx = value.media_type === DOCX_MEDIA;
        const key = docx ? "paragraphs" : "pages";
        const maximum = docx ? 128 : 20;
        const numbers = array(value[key], maximum).map(integer);
        if (
          (!docx && value.media_type !== "application/pdf") ||
          value[docx ? "pages" : "paragraphs"] !== undefined ||
          !numbers.length ||
          numbers.some(
            (n, i) => n < 1 || n > maximum || (i > 0 && n <= numbers[i - 1]),
          )
        )
          throw new LibraryClientError("invalid_response");
        locations = docx
          ? { media_type: DOCX_MEDIA, paragraphs: numbers }
          : { media_type: "application/pdf", pages: numbers };
      }
      const passageIds = array(value.passage_ids, compact ? 1 : 256).map(text);
      if (compact && passageIds.length !== 1)
        throw new LibraryClientError("invalid_response");
      return {
        ...identity(value),
        ...offsets(value, body),
        text: body,
        offset_unit: "unicode_code_point" as const,
        passage_ids: passageIds,
        seed_rank: integer(value.seed_rank),
        similarity: number(value.similarity),
        ...locations,
      };
    });
    const size = integer(result.utf8_bytes);
    if (
      size > 32768 ||
      size !== windows.reduce((n, w) => n + encoder.encode(w.text).length, 0)
    )
      throw new LibraryClientError("invalid_response");
    return {
      version,
      windows,
      utf8_bytes: size,
      omitted_sources: array(result.omitted_sources, 100).map((row) => {
        const value = record(row);
        return { source_id: id(value.source_id), reason: text(value.reason) };
      }),
    };
  }

  async original(
    sourceId: string,
    versionId: string,
    signal?: AbortSignal,
  ): Promise<SavedOriginal | null> {
    const generation = this.generation;
    const reply = await this.request(
      "open-original",
      { source_id: id(sourceId), version_id: id(versionId) },
      signal,
    );
    if (reply === null) return null;
    const value = record(reply);
    const title = text(value.title);
    const media = text(value.media_type) as DocumentMedia;
    const encoded = text(value.content_base64);
    if (
      value.source_id !== sourceId ||
      value.version_id !== versionId ||
      !title.trim() ||
      Array.from(title).length > 500 ||
      ![
        "text/plain",
        "text/markdown",
        "application/pdf",
        DOCX_MEDIA,
        "image/png",
        "image/jpeg",
      ].includes(media) ||
      encoded.length < 4 ||
      encoded.length > 87384 ||
      encoded.length % 4 !== 0 ||
      !/^[A-Za-z0-9+/]+={0,2}$/.test(encoded)
    )
      throw new LibraryClientError("invalid_response");
    const bytes = Uint8Array.from(atob(encoded), (char) => char.charCodeAt(0));
    if (bytes.length < 1 || bytes.length > 65536)
      throw new LibraryClientError("invalid_response");
    const digest = new Uint8Array(await crypto.subtle.digest("SHA-256", bytes));
    if (generation !== this.generation || signal?.aborted)
      throw new LibraryClientError("cancelled");
    if (
      Array.from(digest, (byte) => byte.toString(16).padStart(2, "0")).join(
        "",
      ) !== value.source_sha256
    )
      throw new LibraryClientError("invalid_response");
    return { title, media, bytes };
  }

  async open(
    sourceId: string,
    versionId: string,
    signal?: AbortSignal,
  ): Promise<SourceText | null> {
    const generation = this.generation;
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
    let locations: Partial<SourceText> = {};
    if (isImageMedia(value.media_type)) {
      locations = imageMetadata(value, body);
      const raw = Uint8Array.from(atob(locations.image_base64!), (c) =>
        c.charCodeAt(0),
      );
      if (!validImageBytes(raw, value.media_type))
        throw new LibraryClientError("invalid_response");
      const hashes = await Promise.all([
        crypto.subtle.digest("SHA-256", raw),
        crypto.subtle.digest("SHA-256", encoder.encode(body)),
      ]);
      if (generation !== this.generation || signal?.aborted)
        throw new LibraryClientError("cancelled");
      const hex = hashes.map((buffer) =>
        Array.from(new Uint8Array(buffer), (byte) =>
          byte.toString(16).padStart(2, "0"),
        ).join(""),
      );
      if (hex[0] !== value.source_sha256 || hex[1] !== value.text_sha256)
        throw new LibraryClientError("invalid_response");
    } else if (
      value.media_type !== undefined ||
      value.pages !== undefined ||
      value.paragraphs !== undefined ||
      value.text_sha256 !== undefined ||
      value.regions !== undefined ||
      value.image_base64 !== undefined
    ) {
      if (
        value.regions !== undefined ||
        value.image_base64 !== undefined ||
        value.ocr_regions !== undefined
      )
        throw new LibraryClientError("invalid_response");
      let documentLocations: Pick<
        SourceText,
        "media_type" | "text_sha256" | "pages" | "paragraphs"
      > = {};
      if (
        value.media_type !== undefined ||
        value.pages !== undefined ||
        value.paragraphs !== undefined ||
        value.text_sha256 !== undefined
      ) {
        const docx = value.media_type === DOCX_MEDIA;
        const key = docx ? "paragraphs" : "pages";
        let previous = 0;
        const spans = array(value[key], docx ? 128 : 20).map((row, index) => {
          const span = record(row),
            number = integer(span.number),
            start = integer(span.start),
            end = integer(span.end);
          if (
            number !== index + 1 ||
            start !== previous ||
            end <= start ||
            end > length
          )
            throw new LibraryClientError("invalid_response");
          previous = end;
          return { number, start, end };
        });
        if (
          (!docx && value.media_type !== "application/pdf") ||
          value[docx ? "pages" : "paragraphs"] !== undefined ||
          !spans.length ||
          previous !== length ||
          !hashPattern.test(text(value.text_sha256))
        )
          throw new LibraryClientError("invalid_response");
        documentLocations = docx
          ? {
              media_type: DOCX_MEDIA,
              paragraphs: spans,
              text_sha256: text(value.text_sha256),
            }
          : {
              media_type: "application/pdf",
              pages: spans,
              text_sha256: text(value.text_sha256),
            };
      }
      locations = documentLocations;
    }
    return {
      ...identity(value),
      body,
      passages,
      ...locations,
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
      state !== "ready" &&
      !Object.prototype.hasOwnProperty.call(MODEL_HTTP, state)
    )
      throw new LibraryClientError("invalid_response");
    if (value.period === "utc_day" && Object.keys(value).length === 4) {
      const limit = integer(value.limit);
      if (
        limit < 1 ||
        limit > 10000 ||
        used > limit ||
        state === "model_budget_exhausted" ||
        (state === "trial_quota_exhausted") !== (used === limit)
      )
        throw new LibraryClientError("invalid_response");
      return { state, used, limit, period: "utc_day" };
    }
    if (
      Object.keys(value).length !== 3 ||
      value.limit !== 3 ||
      used > 3 ||
      state === "trial_quota_exhausted" ||
      state === "trial_capacity_exhausted" ||
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
    const timeout = setTimeout(
      () => {
        timedOut = true;
        controller.abort();
      },
      route === "search" || route === "search-previews" ? 95000 : 30000,
    );
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
              Object.prototype.hasOwnProperty.call(ERROR_HTTP, value.error) &&
              ERROR_HTTP[value.error] === response.status
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
