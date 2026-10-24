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
