// @vitest-environment node
import { afterEach, describe, expect, it, vi } from "vitest";
import { LibraryClient, DOCX_MEDIA } from "./libraryClient";
const ID = "00000000-0000-0000-0000-000000000001";
const receipt = { source_id: ID, version_id: ID, job_id: ID };
const respond = (value: unknown, status = 200) =>
  new Response(JSON.stringify(value), {
    status,
    headers: { "Content-Type": "application/json" },
  });
const setup = (send = vi.fn<typeof fetch>()) => {
  const client = new LibraryClient("https://library.example.invalid", {
    fetch: send,
  });
  client.setSession("test-user-session");
  return { client, send };
};
afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe("library HTTP client (synthetic responses)", () => {
  it("rejects mixed or incomplete DOCX citation metadata without retrying", async () => {
    const { client, send } = setup();
    const doc = {
      source_id: ID,
      version_id: ID,
      source_sha256: "0".repeat(64),
      title: "guide.docx",
      body: "First\n\nSecond",
      passages: [{ id: "p", start: 0, end: 13 }],
      model_id: "model",
      model_revision: "revision",
      dimensions: 2,
      media_type: DOCX_MEDIA,
      text_sha256: "1".repeat(64),
    };
    for (const spans of [
      { paragraphs: [{ number: 2, start: 0, end: 13 }] },
      { paragraphs: [{ number: 1, start: 1, end: 13 }] },
      {
        paragraphs: [{ number: 1, start: 0, end: 13 }],
        pages: [{ number: 1, start: 0, end: 13 }],
      },
    ]) {
      send.mockResolvedValueOnce(respond([{ ...doc, ...spans }]));
      await expect(client.open(ID, ID)).rejects.toMatchObject({
        code: "invalid_response",
      });
    }
    expect(send).toHaveBeenCalledTimes(3);
  });
  it("validates DOCX capability booleans rather than trusting truthy values", async () => {
    const { client, send } = setup();
    send.mockResolvedValueOnce(
      respond({ items: [], next_cursor: null, docx_enabled: "true" }),
    );
    await expect(client.listSources()).rejects.toMatchObject({
      code: "invalid_response",
    });
    expect(send).toHaveBeenCalledTimes(1);
  });
  it("preserves only bounded known model-code/status pairs and never retries", async () => {
    const { client, send } = setup();
    for (const [status, body, expected] of [
      [429, { error: "model_budget_exhausted" }, "model_budget_exhausted"],
      [
        502,
        { error: "model_identity_unavailable" },
        "model_identity_unavailable",
      ],
      [504, { error: "model_deadline" }, "model_deadline"],
      [401, { error: "model_access_denied" }, "session_required"],
      [502, { error: "private token details" }, "model_unavailable"],
      [
        502,
        { error: "model_access_denied", secret: "private" },
        "model_unavailable",
      ],
      [502, { error: "x".repeat(5000) }, "model_unavailable"],
    ] as const) {
      const count = send.mock.calls.length;
      send.mockResolvedValueOnce(respond(body, status));
      await expect(client.search("fixture")).rejects.toMatchObject({
        code: expected,
      });
      expect(send.mock.calls.length).toBe(count + 1);
    }
  });
  it("checks readiness only on request, with strict session-scoped counters", async () => {
    const { client, send } = setup();
    send.mockResolvedValueOnce(respond({ state: "ready", used: 0, limit: 3 }));
    await expect(client.modelStatus()).resolves.toEqual({
      state: "ready",
      used: 0,
      limit: 3,
    });
    expect(String(send.mock.calls[0][0])).toMatch(/\/v1\/model-status$/);
    expect(send.mock.calls[0][1]?.body).toBe("{}");
    for (const value of [
      { state: "ready", used: 3, limit: 3 },
      { state: "ready", used: 0, limit: 4 },
      { state: "private details", used: 0, limit: 3 },
      { state: "ready", used: 0, limit: 3, token: "private" },
    ]) {
      send.mockResolvedValueOnce(respond(value));
      await expect(client.modelStatus()).rejects.toThrow("invalid_response");
    }
  });
  it("calls the native transport without using the client as its receiver", async () => {
    const transport = vi.fn(function (this: unknown) {
      // Model Chromium's receiver-sensitive native fetch, which Node mocks
      // otherwise allow to be called as a method on an arbitrary object.
      expect(this).toBeUndefined();
      return Promise.resolve(respond([]));
    });
    vi.stubGlobal("fetch", transport);
    const client = new LibraryClient("https://library.example.invalid");
    client.setSession("synthetic-session");
    await expect(client.status(ID)).resolves.toEqual([]);
    expect(transport).toHaveBeenCalledTimes(1);
  });
  it("retries an uncertain import with the same immutable ID and exact bytes", async () => {
    const { client, send } = setup();
    send.mockRejectedValueOnce(new Error("private transport detail"));
    send.mockResolvedValueOnce(respond(receipt, 202));
    const bytes = new TextEncoder().encode("\ufeffhello\r\n🌟");
    const prepared = client.prepareImport("note", bytes, "text/markdown");
    bytes.fill(0);
    await expect(client.importText(prepared)).rejects.toMatchObject({
      code: "network_unavailable",
    });
    await expect(client.importText(prepared)).resolves.toEqual(receipt);
    expect(send.mock.calls[0][1]?.body).toBe(send.mock.calls[1][1]?.body);
    const payload = JSON.parse(send.mock.calls[0][1]?.body as string);
    expect(
      new TextDecoder().decode(
        Uint8Array.from(atob(payload.content_base64), (c) => c.charCodeAt(0)),
      ),
    ).toBe("\ufeffhello\r\n🌟".slice(1));
    expect(Object.isFrozen(prepared)).toBe(true);
    expect(payload.user_id).toBeUndefined();
    expect(send.mock.calls[0][1]).toMatchObject({
      credentials: "omit",
      redirect: "error",
      cache: "no-store",
    });
  });

  it("clears pending imports on logout or account change", async () => {
    const { client, send } = setup();
    const pending = client.prepareImport(
      "x",
      new Uint8Array([65]),
      "text/plain",
    );
    client.setSession("different-session");
    await expect(client.importText(pending)).rejects.toMatchObject({
      code: "stale_import",
    });
    client.setSession(null);
    await expect(client.status(ID)).rejects.toMatchObject({
      code: "session_required",
    });
    expect(send).not.toHaveBeenCalled();
  });

  it("discards late replies after the session changes", async () => {
    const { client, send } = setup();
    let finish!: (value: Response) => void;
    send.mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          finish = resolve;
        }),
    );
    const request = client.status(ID);
    client.setSession("second-session");
    finish(respond([]));
    await expect(request).rejects.toMatchObject({ code: "session_changed" });
  });

  it("honors cancellation and forbids concurrent requests", async () => {
    const { client, send } = setup();
    send.mockImplementationOnce(
      (_url, init) =>
        new Promise((_resolve, reject) => {
          init?.signal?.addEventListener("abort", () =>
            reject(new DOMException("aborted", "AbortError")),
          );
        }),
    );
    const controller = new AbortController();
    const first = client.status(ID, controller.signal);
    await expect(client.status(ID)).rejects.toMatchObject({ code: "busy" });
    controller.abort();
    await expect(first).rejects.toMatchObject({ code: "cancelled" });
  });

  it("times out once without retrying or exposing provider errors", async () => {
    vi.useFakeTimers();
    const { client, send } = setup();
    send.mockImplementationOnce(
      (_url, init) =>
        new Promise((_resolve, reject) => {
          init?.signal?.addEventListener("abort", () =>
            reject(new Error("sensitive")),
          );
        }),
    );
    const result = expect(client.status(ID)).rejects.toMatchObject({
      code: "timeout",
    });
    await vi.advanceTimersByTimeAsync(30000);
    await result;
    expect(send).toHaveBeenCalledTimes(1);
  });

  it("bounds body reads and checks response format", async () => {
    const { client, send } = setup();
    for (const response of [
      new Response("x".repeat(524289), {
        headers: { "Content-Type": "application/json" },
      }),
      respond({ bad: true }),
      new Response("<html>secret</html>"),
    ]) {
      send.mockResolvedValueOnce(response);
      await expect(client.status(ID)).rejects.toMatchObject({
        code: "invalid_response",
      });
    }
    send.mockResolvedValueOnce(respond({ error: "private details" }, 502));
    await expect(client.status(ID)).rejects.toMatchObject({
      code: "model_unavailable",
    });
    send.mockResolvedValueOnce(respond({ error: "private details" }, 503));
    await expect(client.status(ID)).rejects.toMatchObject({
      code: "library_unavailable",
    });
  });

  it("validates import bounds, UTF-8 and configured origin before network", () => {
    const { client, send } = setup();
    for (const bytes of [
      new Uint8Array(),
      new Uint8Array(65537),
      new Uint8Array([255]),
    ]) {
      expect(() => client.prepareImport("x", bytes, "text/plain")).toThrow(
        "invalid_import",
      );
    }
    for (const url of [
      "http://example.invalid",
      "https://user:pass@example.invalid",
      "https://example.invalid/path",
    ]) {
      expect(() => new LibraryClient(url)).toThrow("invalid_configuration");
    }
    expect(
      () => new LibraryClient("http://127.0.0.1:8765", { allowLoopback: true }),
    ).not.toThrow();
    expect(send).not.toHaveBeenCalled();
  });

  it("preserves unicode code-point offsets and exact version reads", async () => {
    const { client, send } = setup();
    const shared = {
      source_id: ID,
      version_id: ID,
      source_sha256: "0".repeat(64),
      title: "Note",
    };
    const window = {
      ...shared,
      text: "🌟a",
      start: 10,
      end: 12,
      offset_unit: "unicode_code_point",
      passage_ids: ["p1"],
      seed_rank: 1,
      similarity: 0.9,
    };
    const result = {
      version: "source-neighbors-v1",
      windows: [window],
      utf8_bytes: 5,
      omitted_sources: [],
    };
    send.mockResolvedValueOnce(respond(result));
    expect((await client.search("star")).windows[0]).toEqual(window);
    send.mockResolvedValueOnce(
      respond({ ...result, windows: [{ ...window, end: 13 }] }),
    );
    await expect(client.search("star")).rejects.toMatchObject({
      code: "invalid_response",
    });
    send.mockResolvedValueOnce(
      respond([
        {
          ...shared,
          version_id: "00000000-0000-0000-0000-000000000002",
          body: "🌟a",
        },
      ]),
    );
    await expect(client.open(ID, ID)).rejects.toMatchObject({
      code: "invalid_response",
    });
    send.mockResolvedValueOnce(respond([]));
    await expect(client.open(ID, ID)).resolves.toBeNull();
  });

  it("returns truthful processing and deletion states", async () => {
    const { client, send } = setup();
    const row = {
      job_id: ID,
      version_id: ID,
      state: "failed",
      attempts: 3,
      error_code: "invalid_input",
    };
    send.mockResolvedValueOnce(respond([row]));
    await expect(client.status(ID)).resolves.toEqual([row]);
    send.mockResolvedValueOnce(respond(false));
    await expect(client.delete(ID)).resolves.toBe(false);
  });
});
