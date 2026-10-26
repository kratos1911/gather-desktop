import { describe, expect, it, vi } from "vitest";
import { readTextFile } from "./textFile";

describe("local text-file preparation", () => {
  it("preserves actual bytes, BOM and CRLF, ignoring advisory MIME", async () => {
    const raw = new TextEncoder().encode("\uFEFF# Note\r\nStars 🌟");
    const send = vi.spyOn(globalThis, "fetch");
    const value = await readTextFile(
      new File([raw], "note.MD", { type: "application/octet-stream" }),
      new AbortController().signal,
    );
    expect(value.media).toBe("text/markdown");
    expect(Array.from(value.bytes)).toEqual(Array.from(raw));
    expect(value.preview).toBe("\uFEFF# Note\r\nStars 🌟");
    expect(send).not.toHaveBeenCalled();
    send.mockRestore();
  });
  it.each([
    ["note.exe", new Uint8Array([65]), "file_type"],
    ["note.txt", new Uint8Array(), "file_size"],
    ["note.txt", new Uint8Array(65537), "file_size"],
    ["note.txt", new Uint8Array([255]), "file_encoding"],
    ["note.txt", new Uint8Array([65, 0]), "file_controls"],
    ["note.md", new TextEncoder().encode("\uFEFF \r\n"), "file_empty"],
  ])("rejects %s with %s", async (name, bytes, code) => {
    await expect(
      readTextFile(new File([bytes], name), new AbortController().signal),
    ).rejects.toMatchObject({ code });
  });
  it("bounds the preview without truncating saved bytes and supports cancellation", async () => {
    const bytes = new Uint8Array(65536).fill(65);
    const value = await readTextFile(
      new File([bytes], "limit.txt"),
      new AbortController().signal,
    );
    expect(value.bytes.byteLength).toBe(65536);
    expect(value.preview).toHaveLength(2400);
    expect(value.previewTruncated).toBe(true);
    const cancel = new AbortController();
    const pending = readTextFile(
      new File([bytes], "cancel.txt"),
      cancel.signal,
    );
    cancel.abort();
    await expect(pending).rejects.toMatchObject({ code: "cancelled" });
  });
});
