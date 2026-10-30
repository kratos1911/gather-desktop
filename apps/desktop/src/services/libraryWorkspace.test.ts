// @vitest-environment node
import { describe, expect, it, vi } from "vitest";
import { LibraryClient } from "./libraryClient";
import { LibraryWorkspace } from "./libraryWorkspace";
const ID = "00000000-0000-0000-0000-000000000001";
const reply = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
const setup = () => {
  const send = vi.fn<typeof fetch>();
  const workspace = new LibraryWorkspace(
    new LibraryClient("https://library.example.invalid", { fetch: send }),
  );
  workspace.setSession("test-session");
  return { workspace, send };
};
describe("library workspace (synthetic transport)", () => {
  it("confirms cleanup only after server success and restores pending cleanup after reconnect", async () => {
    const { workspace, send } = setup();
    send.mockResolvedValueOnce(
      reply({ items: [], next_cursor: null, cleanup_source_ids: [ID] }),
    );
    await workspace.loadSources();
    expect(workspace.getSnapshot().cleanupSources).toEqual([ID]);
    send.mockRejectedValueOnce(new Error("uncertain cleanup"));
    await workspace.finishCleanup(ID);
    expect(workspace.getSnapshot().cleanedSourceId).toBeNull();
    expect(workspace.getSnapshot().cleanupSources).toEqual([ID]);
    send.mockResolvedValueOnce(reply(true));
    await workspace.finishCleanup(ID);
    expect(workspace.getSnapshot().cleanedSourceId).toBe(ID);
    expect(workspace.getSnapshot().cleanupSources).toEqual([]);
    workspace.setSession("other-user");
    expect(workspace.getSnapshot().cleanedSourceId).toBeNull();
    expect(workspace.getSnapshot().cleanupSources).toEqual([]);
  });
  it("deletion hides immediately, then uses the owned cleanup endpoint once", async () => {
    const { workspace, send } = setup();
    send.mockResolvedValueOnce(
      reply({ items: [], next_cursor: null, cleanup_source_ids: [] }),
    );
    await workspace.loadSources();
    send.mockResolvedValueOnce(reply(true)).mockResolvedValueOnce(reply(true));
    await workspace.delete(ID);
    expect(
      send.mock.calls.slice(1).map(([url]) => new URL(String(url)).pathname),
    ).toEqual(["/v1/delete", "/v1/cleanup"]);
    expect(workspace.getSnapshot().cleanedSourceId).toBe(ID);
  });
  it("binds explicit recovery to the observed job and attempt and never retries itself", async () => {
    const { workspace, send } = setup();
    send.mockResolvedValueOnce(reply(false));
    await workspace.process(ID, ID, 1);
    expect(JSON.parse(String(send.mock.calls[0][1]?.body))).toEqual({
      source_id: ID,
      job_id: ID,
      expected_attempts: 1,
    });
    expect(workspace.getSnapshot().error).toBe("processing_not_eligible");
    expect(send).toHaveBeenCalledTimes(1);
    workspace.dispose();
  });
  it("watches an automatic import through ready without replaying import or inference", async () => {
    vi.useFakeTimers();
    const { workspace, send } = setup();
    try {
      send.mockResolvedValueOnce(
        reply(
          {
            source_id: ID,
            version_id: ID,
            job_id: ID,
            automatic_processing: true,
          },
          202,
        ),
      );
      await workspace.importText(
        "automatic.txt",
        new Uint8Array([65]),
        "text/plain",
      );
      const row = (state: string) => [
        { job_id: ID, version_id: ID, state, attempts: 1, error_code: null },
      ];
      send
        .mockResolvedValueOnce(reply(row("processing")))
        .mockResolvedValueOnce(reply(row("ready")));
      const stop = workspace.watchImport();
      await vi.advanceTimersByTimeAsync(1000);
      expect(workspace.getSnapshot().processing?.state).toBe("processing");
      await vi.advanceTimersByTimeAsync(10000);
      expect(workspace.getSnapshot().processing?.state).toBe("ready");
      await vi.advanceTimersByTimeAsync(600000);
      expect(
        send.mock.calls.map(([url]) => new URL(String(url)).pathname),
      ).toEqual(["/v1/import", "/v1/status", "/v1/status"]);
      stop();
    } finally {
      workspace.dispose();
      vi.useRealTimers();
    }
  });
  it("stops metadata watching at failure, deletion and account switching", async () => {
    vi.useFakeTimers();
    const { workspace, send } = setup();
    try {
      send.mockResolvedValueOnce(
        reply(
          {
            source_id: ID,
            version_id: ID,
            job_id: ID,
            automatic_processing: true,
          },
          202,
        ),
      );
      await workspace.importText(
        "automatic.txt",
        new Uint8Array([65]),
        "text/plain",
      );
      send.mockResolvedValueOnce(
        reply([
          {
            job_id: ID,
            version_id: ID,
            state: "queued",
            attempts: 1,
            error_code: "timeout",
          },
        ]),
      );
      const stop = workspace.watchImport();
      await vi.advanceTimersByTimeAsync(1000);
      await vi.advanceTimersByTimeAsync(600000);
      expect(send).toHaveBeenCalledTimes(2);
      stop();
      const stale = workspace.watchImport();
      workspace.setSession("other-user");
      await vi.advanceTimersByTimeAsync(20000);
      expect(send).toHaveBeenCalledTimes(2);
      stale();
    } finally {
      workspace.dispose();
      vi.useRealTimers();
    }
  });
  it("limits metadata polling and never adopts a superseded processing version", async () => {
    vi.useFakeTimers();
    const { workspace, send } = setup();
    try {
      send.mockResolvedValueOnce(
        reply(
          {
            source_id: ID,
            version_id: ID,
            job_id: ID,
            automatic_processing: true,
          },
          202,
        ),
      );
      await workspace.importText(
        "automatic.txt",
        new Uint8Array([65]),
        "text/plain",
      );
      const queued = [
        {
          job_id: ID,
          version_id: ID,
          state: "queued",
          attempts: 0,
          error_code: null,
        },
      ];
      send.mockImplementation(async () => reply(queued));
      const stop = workspace.watchImport();
      await vi.advanceTimersByTimeAsync(600000);
      expect(send).toHaveBeenCalledTimes(31);
      stop();
      send.mockResolvedValueOnce(
        reply([
          {
            ...queued[0],
            version_id: "00000000-0000-0000-0000-000000000002",
            state: "ready",
          },
        ]),
      );
      await workspace.refreshStatus();
      expect(workspace.getSnapshot().processing).toBeNull();
    } finally {
      workspace.dispose();
      vi.useRealTimers();
    }
  });
  it("discards a late model check after account switching and never replays search", async () => {
    const { workspace, send } = setup();
    let resolve!: (value: Response) => void;
    send.mockImplementationOnce(
      () =>
        new Promise((done) => {
          resolve = done;
        }),
    );
    const pending = workspace.checkModel();
    workspace.setSession("other-session");
    resolve(reply({ state: "ready", used: 0, limit: 3 }));
    await pending;
    expect(workspace.getSnapshot().modelStatus).toBeNull();
    send.mockResolvedValueOnce(
      reply({ state: "model_budget_exhausted", used: 3, limit: 3 }),
    );
    await workspace.checkModel();
    expect(workspace.getSnapshot().modelStatus?.state).toBe(
      "model_budget_exhausted",
    );
    expect(
      send.mock.calls.every(([url]) =>
        String(url).endsWith("/v1/model-status"),
      ),
    ).toBe(true);
    workspace.setSession(null);
    expect(workspace.getSnapshot().modelStatus).toBeNull();
  });
  it("corrects a definite first refusal but preserves an earlier uncertain file submission", async () => {
    const { workspace, send } = setup();
    send.mockResolvedValueOnce(reply({}, 400));
    await workspace.importText(
      "bad.md",
      new Uint8Array([65]),
      "text/markdown",
      true,
    );
    expect(workspace.getSnapshot().pendingImport).toBeNull();
    send.mockRejectedValueOnce(new Error("connection lost"));
    await workspace.importText(
      "reviewed.md",
      new Uint8Array([66]),
      "text/markdown",
      true,
    );
    const key = workspace.getSnapshot().pendingImport?.request_id;
    send.mockResolvedValueOnce(reply({}, 403));
    await workspace.retryImport();
    expect(workspace.getSnapshot().pendingImport?.request_id).toBe(key);
    expect(workspace.getSnapshot().pendingImport?.confirm_cloud_storage).toBe(
      true,
    );
    expect(send.mock.calls[1][1]?.body).toBe(send.mock.calls[2][1]?.body);
  });
  const source = (n: number) => ({
    source_id: `00000000-0000-0000-0000-${String(n).padStart(12, "0")}`,
    title: `Saved ${n}`,
    kind: "file",
    created_at: "2026-10-26T01:00:00.000001Z",
    published_version_id: null,
    processing_version_id: null,
    job_id: null,
    state: null,
    attempts: null,
    error_code: null,
  });
  it("loads bounded pages, retries the same cursor, and removes deleted rows after refresh", async () => {
    const { workspace, send } = setup();
    const items = Array.from({ length: 20 }, (_, i) => source(30 - i));
    send.mockResolvedValueOnce(reply({ items, next_cursor: "fixture_cursor" }));
    await workspace.loadSources();
    send.mockRejectedValueOnce(new Error("offline"));
    await workspace.loadSources(true);
    expect(workspace.getSnapshot().libraryStatus).toBe("error");
    expect(workspace.getSnapshot().sources).toHaveLength(20);
    send.mockResolvedValueOnce(
      reply({ items: [source(1)], next_cursor: null }),
    );
    await workspace.loadSources(true);
    expect(send.mock.calls[1][1]?.body).toBe(send.mock.calls[2][1]?.body);
    expect(workspace.getSnapshot().sources).toHaveLength(21);
    send.mockResolvedValueOnce(reply(true));
    await workspace.delete(source(30).source_id);
    expect(
      workspace
        .getSnapshot()
        .sources.some((s) => s.source_id === source(30).source_id),
    ).toBe(false);
    send.mockResolvedValueOnce(reply({ items: [], next_cursor: null }));
    await workspace.loadSources();
    expect(workspace.getSnapshot().sources).toEqual([]);
  });
  it("ignores old-account pages and cancelled replies before a subsequent deletion", async () => {
    const { workspace, send } = setup();
    let resolve!: (value: Response) => void;
    send.mockImplementationOnce(
      () =>
        new Promise((done) => {
          resolve = done;
        }),
    );
    const pending = workspace.loadSources();
    workspace.setSession("other-user-session");
    resolve(reply({ items: [source(1)], next_cursor: null }));
    await pending;
    expect(workspace.getSnapshot().sources).toEqual([]);
    send.mockImplementationOnce(
      () =>
        new Promise((done) => {
          resolve = done;
        }),
    );
    const cancelled = workspace.loadSources();
    workspace.cancel();
    resolve(reply({ items: [source(1)], next_cursor: null }));
    await cancelled;
    send.mockResolvedValueOnce(reply(true));
    await workspace.delete(source(1).source_id);
    expect(workspace.getSnapshot().sources).toEqual([]);
    workspace.setSession(null);
    expect(workspace.getSnapshot().nextCursor).toBeNull();
  });
  it("rejects oversized or inconsistent listing responses", async () => {
    const { workspace, send } = setup();
    for (const items of [
      Array.from({ length: 21 }, (_, i) => source(i)),
      [
        {
          ...source(1),
          state: "ready",
          job_id: ID,
          processing_version_id: ID,
          attempts: 1,
        },
      ],
      [source(1), source(1)],
    ]) {
      send.mockResolvedValueOnce(reply({ items, next_cursor: null }));
      await workspace.loadSources();
      expect(workspace.getSnapshot().error).toBe("invalid_response");
      expect(workspace.getSnapshot().sources).toEqual([]);
    }
  });
  it("retains uncertain import and retries the same ID before allowing a new one", async () => {
    const { workspace, send } = setup();
    send.mockRejectedValueOnce(new Error("network"));
    await workspace.importText("note", new Uint8Array([65]), "text/plain");
    const key = workspace.getSnapshot().pendingImport?.request_id;
    expect(key).toBeTruthy();
    await expect(
      workspace.importText("other", new Uint8Array([66]), "text/plain"),
    ).rejects.toThrow("pending_import_requires_resolution");
    send.mockResolvedValueOnce(
      reply({ source_id: ID, job_id: ID, version_id: ID }, 202),
    );
    await workspace.retryImport();
    expect(JSON.parse(send.mock.calls[1][1]?.body as string).request_id).toBe(
      key,
    );
    expect(workspace.getSnapshot()).toMatchObject({
      pendingImport: null,
      imported: { source_id: ID },
      processing: null,
    });
  });
  it("does not pretend queued import is ready, and shows worker failure", async () => {
    const { workspace, send } = setup();
    send.mockResolvedValueOnce(
      reply({ source_id: ID, job_id: ID, version_id: ID }, 202),
    );
    await workspace.importText("note", new Uint8Array([65]), "text/plain");
    expect(workspace.getSnapshot().processing).toBeNull();
    send.mockResolvedValueOnce(
      reply([
        {
          job_id: ID,
          version_id: ID,
          state: "failed",
          attempts: 3,
          error_code: "invalid_input",
        },
      ]),
    );
    await workspace.refreshStatus();
    expect(workspace.getSnapshot().processing?.state).toBe("failed");
  });
  it("clears all user state on logout and ignores delayed results", async () => {
    const { workspace, send } = setup();
    let resolve!: (value: Response) => void;
    send.mockImplementationOnce(
      () =>
        new Promise((done) => {
          resolve = done;
        }),
    );
    const pending = workspace.search("query");
    workspace.setSession(null);
    resolve(
      reply({
        version: "source-neighbors-v1",
        windows: [],
        utf8_bytes: 0,
        omitted_sources: [],
      }),
    );
    await pending;
    expect(workspace.getSnapshot()).toMatchObject({
      signedIn: false,
      busy: false,
      error: null,
      results: null,
      opened: null,
      pendingImport: null,
    });
  });
  it("does not claim deletion succeeded when the server rejects it", async () => {
    const { workspace, send } = setup();
    send.mockResolvedValueOnce(
      reply({ source_id: ID, job_id: ID, version_id: ID }, 202),
    );
    await workspace.importText("note", new Uint8Array([65]), "text/plain");
    send.mockResolvedValueOnce(reply(false));
    await workspace.delete(ID);
    expect(workspace.getSnapshot().imported?.source_id).toBe(ID);
    expect(workspace.getSnapshot().error).toBe("source_unavailable");
    send.mockResolvedValueOnce(reply(true));
    await workspace.delete(ID);
    expect(workspace.getSnapshot().imported).toBeNull();
  });
});
