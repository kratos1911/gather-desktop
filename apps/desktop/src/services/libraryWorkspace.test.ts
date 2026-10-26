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
