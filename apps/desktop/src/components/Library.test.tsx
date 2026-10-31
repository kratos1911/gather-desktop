import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import App from "../App";
import Library from "./Library";
import { signInPilot } from "../services/pilotAuth";
vi.mock("../services/pilotAuth", async (original) => ({
  ...(await original<object>()),
  signInPilot: vi.fn(),
}));
vi.mock("../services/pilotConfiguration", () => ({
  pilotAvailable: true,
  connectedPilot: true,
  libraryEndpoint: () => ({
    url: "https://library.example.test",
    allowLoopback: false,
  }),
}));
const ID = "00000000-0000-0000-0000-000000000001";
const OTHER = "00000000-0000-0000-0000-000000000002";
const body =
  "# Notes\nThe Orchard team keeps backups for fourteen days.\n<b>Plain text</b>";
const source = {
  source_id: ID,
  title: "notes.md",
  kind: "file",
  created_at: "2026-10-31T01:00:00.000001Z",
  published_version_id: ID,
  processing_version_id: ID,
  job_id: ID,
  state: "ready",
  attempts: 1,
  error_code: null,
};
const reply = (value: unknown, status = 200) =>
  new Response(JSON.stringify(value), {
    status,
    headers: { "Content-Type": "application/json" },
  });
const page = (items: unknown[] = [source]) =>
  reply({ items, next_cursor: null, cleanup_source_ids: [] });
const results = () =>
  reply({
    version: "source-neighbors-v1",
    windows: [
      {
        source_id: ID,
        version_id: ID,
        source_sha256: "0".repeat(64),
        title: source.title,
        text: body,
        start: 0,
        end: Array.from(body).length,
        offset_unit: "unicode_code_point",
        passage_ids: ["p1"],
        seed_rank: 1,
        similarity: 0.9,
      },
    ],
    utf8_bytes: new TextEncoder().encode(body).length,
    omitted_sources: [],
  });
const opened = () =>
  reply([
    {
      ...source,
      version_id: ID,
      source_sha256: "0".repeat(64),
      body,
      model_id: "model",
      model_revision: "revision",
      dimensions: 2,
      passages: [{ id: "p1", start: 0, end: Array.from(body).length }],
    },
  ]);
beforeAll(() => {
  Object.defineProperty(HTMLDialogElement.prototype, "showModal", {
    configurable: true,
    value() {
      this.open = true;
    },
  });
  Object.defineProperty(HTMLDialogElement.prototype, "close", {
    configurable: true,
    value() {
      this.open = false;
    },
  });
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
  vi.clearAllMocks();
});
function setup(send: ReturnType<typeof vi.fn<typeof fetch>>) {
  vi.stubEnv("VITE_GATHER_PILOT_PUBLIC_KEY", "sb_publishable_test");
  vi.mocked(signInPilot).mockResolvedValue("test-session");
  vi.stubGlobal("fetch", send);
}
async function login() {
  fireEvent.change(screen.getByLabelText("Password"), {
    target: { value: "synthetic" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Sign in" }));
  await screen.findByRole("list", { name: "Saved files" });
  await waitFor(() =>
    expect(
      (
        screen.getByRole("button", {
          name: "Refresh library",
        }) as HTMLButtonElement
      ).disabled,
    ).toBe(false),
  );
}

describe("unified authenticated library (synthetic HTTP fixtures)", () => {
  it("routes the app to one real library and one explicit semantic search, with exact text and confirmed deletion", async () => {
    const send = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(page())
      .mockResolvedValueOnce(results())
      .mockResolvedValueOnce(opened())
      .mockResolvedValueOnce(reply(true))
      .mockResolvedValueOnce(reply(true));
    setup(send);
    render(<App />);
    await screen.findByLabelText("Password");
    await login();
    expect(screen.getAllByRole("textbox")).toHaveLength(1);
    expect(screen.queryByText("Operator pilot")).toBeNull();
    expect(screen.queryByText("The art of remembering")).toBeNull();
    expect(screen.getByRole("button", { name: "Open notes.md" })).toBeTruthy();
    fireEvent.change(screen.getByLabelText("Search your library"), {
      target: { value: "How long are backups kept?" },
    });
    expect(send).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByRole("button", { name: "Search saved files" }));
    await screen.findByRole("list", { name: "Search results" });
    expect(JSON.parse(send.mock.calls[1][1]?.body as string).query).toBe(
      "How long are backups kept?",
    );
    expect(screen.getByText(/Characters 0–/)).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Open saved text" }));
    const reader = await screen.findByRole("dialog", { name: "notes.md" });
    expect(
      within(reader).getByLabelText("Saved document text").textContent,
    ).toBe(body);
    expect(reader.querySelector("b")).toBeNull();
    expect(JSON.parse(send.mock.calls[2][1]?.body as string)).toEqual({
      source_id: ID,
      version_id: ID,
    });
    fireEvent.click(
      within(reader).getByRole("button", { name: "Close notes.md" }),
    );
    fireEvent.click(screen.getByRole("button", { name: "Delete notes.md" }));
    expect(send).toHaveBeenCalledTimes(3);
    fireEvent.click(
      screen.getByRole("button", { name: "Delete file permanently" }),
    );
    await screen.findByText(/Deletion complete/);
    expect(
      screen.queryByRole("button", { name: "Open saved text" }),
    ).toBeNull();
    expect(
      send.mock.calls.map(([url]) => new URL(String(url)).pathname),
    ).toEqual([
      "/v1/list",
      "/v1/search",
      "/v1/open",
      "/v1/delete",
      "/v1/cleanup",
    ]);
  });
  it("adds reviewed files to the same grid and updates them after automatic processing, without inference on typing", async () => {
    const send = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(page([]))
      .mockResolvedValueOnce(
        reply(
          {
            source_id: ID,
            version_id: ID,
            job_id: ID,
            automatic_processing: true,
          },
          202,
        ),
      )
      .mockResolvedValueOnce(
        page([
          {
            ...source,
            published_version_id: null,
            state: "queued",
            attempts: 0,
          },
        ]),
      )
      .mockResolvedValueOnce(
        reply([
          {
            job_id: ID,
            version_id: ID,
            state: "ready",
            attempts: 1,
            error_code: null,
          },
        ]),
      )
      .mockResolvedValueOnce(page());
    setup(send);
    render(<Library />);
    await login();
    expect(
      (
        screen.getByRole("button", {
          name: "Search saved files",
        }) as HTMLButtonElement
      ).disabled,
    ).toBe(true);
    fireEvent.click(screen.getByRole("button", { name: "Add file" }));
    fireEvent.change(screen.getByLabelText("Choose a TXT or Markdown file"), {
      target: { files: [new File([body], "notes.md")] },
    });
    await screen.findByLabelText("Local plain-text preview");
    expect(send).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByRole("checkbox"));
    fireEvent.click(screen.getByRole("button", { name: "Save selected file" }));
    await screen.findByText("Queued for processing");
    await screen.findByText("Ready to search", {}, { timeout: 2500 });
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(
      atob(JSON.parse(send.mock.calls[1][1]?.body as string).content_base64),
    ).toBe(body);
    expect(
      send.mock.calls.map(([url]) => new URL(String(url)).pathname),
    ).toEqual(["/v1/list", "/v1/import", "/v1/list", "/v1/status", "/v1/list"]);
  });
  it("keeps unpublished files closed, shows replacement truth and restores metadata after reauthentication", async () => {
    const items = [
      {
        ...source,
        source_id: OTHER,
        published_version_id: null,
        title: "waiting.txt",
        state: "failed",
        error_code: "timeout",
        attempts: 3,
      },
      {
        ...source,
        processing_version_id: OTHER,
        state: "failed",
        error_code: "timeout",
      },
    ];
    const send = vi
      .fn<typeof fetch>()
      .mockImplementation(async () => page(items));
    setup(send);
    const view = render(<Library />);
    await login();
    expect(
      (
        screen.getByRole("button", {
          name: "Open waiting.txt",
        }) as HTMLButtonElement
      ).disabled,
    ).toBe(true);
    expect(
      screen.getByText("Saved version available · replacement failed"),
    ).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Markdown" }));
    expect(
      screen.queryByRole("button", { name: "Open waiting.txt" }),
    ).toBeNull();
    view.unmount();
    render(<Library />);
    expect(screen.queryByText("notes.md")).toBeNull();
    await login();
    expect(screen.getByRole("button", { name: "Open notes.md" })).toBeTruthy();
    expect(send).toHaveBeenCalledTimes(2);
  });
  it("discards late search data on sign-out and exposes readiness only under account settings", async () => {
    let resolve!: (response: Response) => void;
    const send = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(page())
      .mockImplementationOnce(
        () =>
          new Promise((done) => {
            resolve = done;
          }),
      );
    setup(send);
    render(<Library />);
    await login();
    expect(
      screen.queryByRole("button", { name: "Check model connection" }),
    ).toBeNull();
    fireEvent.change(screen.getByLabelText("Search your library"), {
      target: { value: "backups" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Search saved files" }));
    fireEvent.click(
      screen.getByRole("button", { name: "Connection & account" }),
    );
    fireEvent.click(screen.getByRole("button", { name: "Sign out" }));
    resolve(results());
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Sign in" })).toBeTruthy(),
    );
    expect(screen.queryByText(body)).toBeNull();
    expect(screen.queryByRole("list", { name: "Search results" })).toBeNull();
    expect(
      (screen.getByLabelText("Search your library") as HTMLInputElement).value,
    ).toBe("");
  });
  it("keeps failed listing retry explicit and does not claim readiness or issue automatic model checks", async () => {
    const send = vi
      .fn<typeof fetch>()
      .mockRejectedValueOnce(new Error("offline"))
      .mockResolvedValueOnce(page([]));
    setup(send);
    render(<Library />);
    await login();
    expect(screen.getByRole("alert")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Refresh library" }));
    await screen.findByText("Make room for your first find.");
    expect(send).toHaveBeenCalledTimes(2);
    expect(
      send.mock.calls.every(([url]) => String(url).endsWith("/v1/list")),
    ).toBe(true);
  });
});
