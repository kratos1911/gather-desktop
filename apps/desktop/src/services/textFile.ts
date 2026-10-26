/** Local, bounded file preparation only. No network or persistence. */
import { LibraryClientError } from "./libraryClient";

export const MAX_TEXT_FILE_BYTES = 65536;
export type SelectedTextFile = Readonly<{
  title: string;
  media: "text/plain" | "text/markdown";
  bytes: Uint8Array;
  preview: string;
  previewTruncated: boolean;
}>;

function hasControls(value: string, allowLayout = false): boolean {
  for (const character of value) {
    const code = character.charCodeAt(0);
    if (
      (code < 32 && !(allowLayout && [9, 10, 13].includes(code))) ||
      (code >= 127 && code <= 159)
    )
      return true;
  }
  return false;
}

export async function readTextFile(
  file: File,
  signal: AbortSignal,
): Promise<SelectedTextFile> {
  if (signal.aborted) throw new LibraryClientError("cancelled");
  if (
    !file.name ||
    Array.from(file.name).length > 500 ||
    hasControls(file.name) ||
    file.name.includes("/") ||
    file.name.includes("\\") ||
    !/\.(txt|md|markdown)$/i.test(file.name)
  )
    throw new LibraryClientError("file_type");
  if (
    !Number.isSafeInteger(file.size) ||
    file.size < 1 ||
    file.size > MAX_TEXT_FILE_BYTES
  )
    throw new LibraryClientError("file_size");
  const bytes = await new Promise<Uint8Array>((resolve, reject) => {
    const reader = new FileReader();
    const cleanup = () => {
      signal.removeEventListener("abort", abort);
    };
    const abort = () => reader.abort();
    reader.onload = () => {
      cleanup();
      if (signal.aborted) return reject(new LibraryClientError("cancelled"));
      if (
        !(reader.result instanceof ArrayBuffer) ||
        reader.result.byteLength !== file.size ||
        reader.result.byteLength > MAX_TEXT_FILE_BYTES
      )
        return reject(new LibraryClientError("file_size"));
      resolve(new Uint8Array(reader.result));
    };
    reader.onerror = () => {
      cleanup();
      reject(new LibraryClientError("file_read_failed"));
    };
    reader.onabort = () => {
      cleanup();
      reject(new LibraryClientError("cancelled"));
    };
    signal.addEventListener("abort", abort, { once: true });
    // Bound the actual read as well as the metadata check.
    reader.readAsArrayBuffer(file.slice(0, MAX_TEXT_FILE_BYTES + 1));
  });
  if (signal.aborted) throw new LibraryClientError("cancelled");
  let body: string;
  try {
    body = new TextDecoder("utf-8", { fatal: true, ignoreBOM: true }).decode(
      bytes,
    );
  } catch {
    throw new LibraryClientError("file_encoding");
  }
  if (hasControls(body, true)) throw new LibraryClientError("file_controls");
  // Match the backend whitespace policy after removing only leading BOMs.
  if (
    /^[\t\n\r \u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]*$/u.test(
      body.replace(/^\uFEFF+/u, ""),
    )
  )
    throw new LibraryClientError("file_empty");
  const points = Array.from(body);
  return Object.freeze({
    title: file.name,
    media: /\.txt$/i.test(file.name) ? "text/plain" : "text/markdown",
    bytes,
    preview: points.slice(0, 2400).join(""),
    previewTruncated: points.length > 2400,
  });
}
