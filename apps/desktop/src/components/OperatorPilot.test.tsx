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
    expect(input.value).toBe("");
    fireEvent.click(
      screen.getByRole("button", { name: "Import synthetic note" }),
    );
    await screen.findByRole("button", { name: "Refresh status" });
    expect(screen.getByText("not checked")).toBeTruthy();
    expect(send).toHaveBeenCalledTimes(1);
    expect(JSON.parse(send.mock.calls[0][1]?.body as string).media).toBe(
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
  expect(send).toHaveBeenCalledTimes(5);
});
