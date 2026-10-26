import { afterEach, describe, expect, it, vi } from "vitest";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import OperatorPilot from "./OperatorPilot";
import { signInPilot } from "../services/pilotAuth";
vi.mock("../services/pilotAuth", async (original) => ({
  ...(await original<object>()),
  signInPilot: vi.fn(),
}));
const ID = "00000000-0000-0000-0000-000000000001";
afterEach(() => {
  cleanup();
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
  vi.clearAllMocks();
});
describe("restricted operator screen", () => {
  it("has labeled controls and makes no request without operator configuration", () => {
    vi.stubEnv("VITE_GATHER_PILOT_PUBLIC_KEY", "");
    const send = vi.fn();
    vi.stubGlobal("fetch", send);
    render(<OperatorPilot />);
    expect(
      (
        screen.getByRole("button", {
          name: "Sign in to pilot",
        }) as HTMLButtonElement
      ).disabled,
    ).toBe(true);
    expect(screen.getByLabelText("Test account password")).toBeTruthy();
    expect(screen.getByText(/configuration is missing/)).toBeTruthy();
    expect(send).not.toHaveBeenCalled();
  });
  it("signs in, imports only fixed content, exposes status, and clears on disconnect", async () => {
    vi.stubEnv("VITE_GATHER_PILOT_PUBLIC_KEY", "sb_publishable_test");
    vi.mocked(signInPilot).mockResolvedValue("test-token");
    const send = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ items: [], next_cursor: null }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      )
      .mockResolvedValue(
        new Response(
          JSON.stringify({ source_id: ID, version_id: ID, job_id: ID }),
          { status: 202, headers: { "Content-Type": "application/json" } },
        ),
      );
    vi.stubGlobal("fetch", send);
    render(<OperatorPilot />);
    const input = screen.getByLabelText(
      "Test account password",
    ) as HTMLInputElement;
    fireEvent.change(input, { target: { value: "synthetic-password" } });
    fireEvent.click(screen.getByRole("button", { name: "Sign in to pilot" }));
    await screen.findByRole("button", { name: "Import synthetic note" });
    await screen.findByText(/No saved sources are visible/);
    expect(input.value).toBe("");
    fireEvent.click(
      screen.getByRole("button", { name: "Import synthetic note" }),
    );
    await screen.findByRole("button", { name: "Refresh status" });
    expect(screen.getByText("not checked")).toBeTruthy();
    expect(send).toHaveBeenCalledTimes(2);
    expect(JSON.parse(send.mock.calls[1][1]?.body as string).media).toBe(
      "text/plain",
    );
    fireEvent.click(screen.getByRole("button", { name: "Disconnect" }));
    await waitFor(() =>
      expect(
        screen.queryByRole("button", { name: "Refresh status" }),
      ).toBeNull(),
    );
  });
});

it("completes status, search, exact source opening and deletion with cleanup notice", async () => {
  vi.stubEnv("VITE_GATHER_PILOT_PUBLIC_KEY", "sb_publishable_test");
  vi.mocked(signInPilot).mockResolvedValue("test-token");
  const common = {
    source_id: ID,
    version_id: ID,
    source_sha256: "0".repeat(64),
    title: "Saved synthetic note",
  };
  const body = "Synthetic test note";
  const response = (value: unknown, status = 200) =>
    new Response(JSON.stringify(value), {
      status,
      headers: { "Content-Type": "application/json" },
    });
  const send = vi
    .fn<typeof fetch>()
    .mockResolvedValueOnce(response({ items: [], next_cursor: null }))
    .mockResolvedValueOnce(
      response({ source_id: ID, version_id: ID, job_id: ID }, 202),
    )
    .mockResolvedValueOnce(
      response([
        {
          job_id: ID,
          version_id: ID,
          state: "ready",
          attempts: 1,
          error_code: null,
        },
      ]),
    )
    .mockResolvedValueOnce(
      response({
        version: "source-neighbors-v1",
        windows: [
          {
            ...common,
            text: body,
            start: 0,
            end: body.length,
            offset_unit: "unicode_code_point",
            passage_ids: ["p1"],
            seed_rank: 1,
            similarity: 1,
          },
        ],
        utf8_bytes: body.length,
        omitted_sources: [],
      }),
    )
    .mockResolvedValueOnce(
      response([
        {
          ...common,
          body,
          passages: [{ id: "p1", start: 0, end: body.length }],
          model_id: "synthetic",
          model_revision: "fixture",
          dimensions: 512,
        },
      ]),
    )
    .mockResolvedValueOnce(response(true));
  vi.stubGlobal("fetch", send);
  render(<OperatorPilot />);
  fireEvent.change(screen.getByLabelText("Test account password"), {
    target: { value: "synthetic" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Sign in to pilot" }));
  await screen.findByText(/No saved sources are visible/);
  fireEvent.click(
    await screen.findByRole("button", { name: "Import synthetic note" }),
  );
  fireEvent.click(
    await screen.findByRole("button", { name: "Refresh status" }),
  );
  await screen.findByText("ready");
  fireEvent.click(screen.getByRole("button", { name: "Search saved notes" }));
  fireEvent.click(
    await screen.findByRole("button", { name: "Open saved text" }),
  );
  await waitFor(() =>
    expect(
      screen.getAllByRole("heading", { name: "Saved synthetic note" }),
    ).toHaveLength(2),
  );
  fireEvent.click(
    screen.getByRole("button", { name: "Delete synthetic note" }),
  );
  await screen.findByText(/Removed from search/);
  expect(screen.queryByRole("button", { name: "Open saved text" })).toBeNull();
  expect(
    (
      screen.getByRole("button", {
        name: "Import synthetic note",
      }) as HTMLButtonElement
    ).disabled,
  ).toBe(true);
  expect(send).toHaveBeenCalledTimes(6);
});

it("deletes a found note when the import receipt was lost on page refresh", async () => {
  vi.stubEnv("VITE_GATHER_PILOT_PUBLIC_KEY", "sb_publishable_test");
  vi.mocked(signInPilot).mockResolvedValue("test-token");
  const title = "Saved synthetic note";
  const body = "The saved database note";
  const common = {
    source_id: ID,
    version_id: ID,
    source_sha256: "0".repeat(64),
    title,
  };
  const response = (value: unknown, status = 200) =>
    new Response(JSON.stringify(value), {
      status,
      headers: { "Content-Type": "application/json" },
    });
  const send = vi
    .fn<typeof fetch>()
    .mockResolvedValueOnce(response({ items: [], next_cursor: null }))
    .mockResolvedValueOnce(
      response({
        version: "source-neighbors-v1",
        windows: [
          {
            ...common,
            text: body,
            start: 0,
            end: body.length,
            offset_unit: "unicode_code_point",
            passage_ids: ["p1"],
            seed_rank: 1,
            similarity: 1,
          },
        ],
        utf8_bytes: body.length,
        omitted_sources: [],
      }),
    )
    .mockResolvedValueOnce(response(true));
  vi.stubGlobal("fetch", send);
  render(<OperatorPilot />);
  fireEvent.change(screen.getByLabelText("Test account password"), {
    target: { value: "synthetic" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Sign in to pilot" }));
  await screen.findByText(/No saved sources are visible/);
  fireEvent.click(
    await screen.findByRole("button", { name: "Search saved notes" }),
  );
  fireEvent.click(
    await screen.findByRole("button", { name: "Delete Saved synthetic note" }),
  );
  await screen.findByText(/Removed from search/);
  expect(screen.getByText(ID)).toBeTruthy();
  expect(screen.queryByText(body)).toBeNull();
  expect(send).toHaveBeenCalledTimes(3);
});

it("restores published and failed-replacement metadata after remount, with explicit list retry", async () => {
  vi.stubEnv("VITE_GATHER_PILOT_PUBLIC_KEY", "sb_publishable_test");
  vi.mocked(signInPilot).mockResolvedValue("test-token");
  const entry = {
    source_id: ID,
    title: "Restored note",
    kind: "file",
    created_at: "2026-10-26T01:00:00.000001Z",
    published_version_id: ID,
    processing_version_id: "00000000-0000-0000-0000-000000000002",
    job_id: ID,
    state: "failed",
    attempts: 3,
    error_code: "invalid_input",
  };
  const page = () =>
    new Response(JSON.stringify({ items: [entry], next_cursor: null }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  const send = vi
    .fn<typeof fetch>()
    .mockResolvedValueOnce(page())
    .mockRejectedValueOnce(new Error("offline"))
    .mockResolvedValueOnce(page());
  vi.stubGlobal("fetch", send);
  const login = () => {
    fireEvent.change(screen.getByLabelText("Test account password"), {
      target: { value: "synthetic" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Sign in to pilot" }));
  };
  const view = render(<OperatorPilot />);
  login();
  await screen.findByRole("heading", { name: "Restored note" });
  expect(screen.getByText(/Replacement processing: failed/)).toBeTruthy();
  expect(
    screen.getByRole("button", { name: "Open saved Restored note" }),
  ).toBeTruthy();
  view.unmount();
  render(<OperatorPilot />);
  expect(screen.queryByText("Restored note")).toBeNull();
  login();
  await screen.findByText(/The library could not load/);
  expect(send).toHaveBeenCalledTimes(2);
  fireEvent.click(
    screen.getByRole("button", { name: "Refresh saved library" }),
  );
  await screen.findByRole("heading", { name: "Restored note" });
  expect(
    send.mock.calls.every(([url]) => String(url).endsWith("/v1/list")),
  ).toBe(true);
  const response = (value: unknown) =>
    new Response(JSON.stringify(value), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  send.mockResolvedValueOnce(
    response([
      {
        source_id: ID,
        version_id: ID,
        title: "Restored note",
        source_sha256: "0".repeat(64),
        body: "Published text",
        model_id: "synthetic",
        model_revision: "fixture",
        dimensions: 512,
        passages: [{ id: "fixture", start: 0, end: 14 }],
      },
    ]),
  );
  fireEvent.click(
    screen.getByRole("button", { name: "Open saved Restored note" }),
  );
  await screen.findByText("Published text");
  expect(JSON.parse(send.mock.calls[3][1]?.body as string).version_id).toBe(ID);
  send.mockResolvedValueOnce(response(true));
  fireEvent.click(
    screen.getByRole("button", { name: "Delete saved Restored note" }),
  );
  await screen.findByText(/Removed from search/);
  expect(screen.queryByText("Published text")).toBeNull();
  expect(screen.queryByRole("heading", { name: "Restored note" })).toBeNull();
  send.mockResolvedValueOnce(response({ items: [], next_cursor: null }));
  fireEvent.click(
    screen.getByRole("button", { name: "Refresh saved library" }),
  );
  await screen.findByText(/No saved sources are visible/);
  fireEvent.click(screen.getByRole("button", { name: "Disconnect" }));
  expect(screen.queryByText("Restored note")).toBeNull();
});
