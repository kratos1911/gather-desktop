/** Synthetic HTTP and header fixtures; not live PDF extraction or semantic proof. */
import { afterEach, beforeAll, expect, it, vi } from "vitest";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import Library from "./Library";
import { signInPilot } from "../services/pilotAuth";
vi.mock("../services/pilotAuth", async (original) => ({
  ...(await original<object>()),
  signInPilot: vi.fn(),
}));
vi.mock("../services/pilotConfiguration", () => ({
  connectedPilot: true,
  libraryEndpoint: () => ({
    url: "https://library.example.test",
    allowLoopback: false,
  }),
}));
const ID = "00000000-0000-0000-0000-000000000001";
const body = "First page.\n\nSecond page holds the retention rule.";
const pages = [
  { number: 1, start: 0, end: 13 },
  { number: 2, start: 13, end: body.length },
];
const source = {
  source_id: ID,
  title: "guide.pdf",
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
async function login(send: ReturnType<typeof vi.fn<typeof fetch>>) {
  vi.stubEnv("VITE_GATHER_PILOT_PUBLIC_KEY", "sb_publishable_test");
  vi.stubGlobal("fetch", send);
  vi.mocked(signInPilot).mockResolvedValue("test-session");
  render(<Library />);
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
it.each([false, true])(
  "uses server recovery eligibility for a processing PDF (eligible=%s)",
  async (canResume) => {
    const send = vi.fn<typeof fetch>().mockResolvedValueOnce(
      reply({
        items: [
          {
            ...source,
            published_version_id: null,
            state: "processing",
            can_resume: canResume,
          },
        ],
        next_cursor: null,
        pdf_enabled: true,
      }),
    );
    await login(send);
    const button = screen.queryByRole("button", {
      name: "Resume processing guide.pdf",
    });
    if (canResume) expect(button).not.toBeNull();
    else expect(button).toBeNull();
    expect(
      screen.getByText(
        canResume
          ? "Processing interrupted · ready to resume"
          : "Processing · no retry needed",
      ),
    ).toBeTruthy();
    expect(send).toHaveBeenCalledTimes(1);
  },
);
it("refreshes a rejected recovery once and removes the stale action", async () => {
  const pending = {
    ...source,
    published_version_id: null,
    state: "queued",
    attempts: 1,
    can_resume: true,
  };
  const active = {
    ...pending,
    state: "processing",
    attempts: 2,
    can_resume: false,
  };
  const send = vi
    .fn<typeof fetch>()
    .mockResolvedValueOnce(
      reply({ items: [pending], next_cursor: null, pdf_enabled: true }),
    )
    .mockResolvedValueOnce(reply(false))
    .mockResolvedValueOnce(
      reply({ items: [active], next_cursor: null, pdf_enabled: true }),
    );
  await login(send);
  fireEvent.click(
    screen.getByRole("button", { name: "Resume processing guide.pdf" }),
  );
  await screen.findByText("Processing · no retry needed");
  expect(
    screen.queryByRole("button", { name: "Resume processing guide.pdf" }),
  ).toBeNull();
  expect(send.mock.calls.map(([url]) => new URL(String(url)).pathname)).toEqual(
    ["/v1/list", "/v1/process", "/v1/list"],
  );
});
it("enables PDF only from server capability and renders page-aware search/opening", async () => {
  const text = body.slice(13);
  const send = vi
    .fn<typeof fetch>()
    .mockResolvedValueOnce(
      reply({ items: [source], next_cursor: null, pdf_enabled: true }),
    )
    .mockResolvedValueOnce(
      reply({
        version: "source-neighbors-v1",
        windows: [
          {
            source_id: ID,
            version_id: ID,
            source_sha256: "0".repeat(64),
            title: "guide.pdf",
            text,
            start: 13,
            end: body.length,
            offset_unit: "unicode_code_point",
            passage_ids: ["p"],
            seed_rank: 1,
            similarity: 0.9,
            media_type: "application/pdf",
            pages: [2],
          },
        ],
        utf8_bytes: new TextEncoder().encode(text).length,
        omitted_sources: [],
      }),
    )
    .mockResolvedValueOnce(
      reply([
        {
          source_id: ID,
          version_id: ID,
          source_sha256: "0".repeat(64),
          title: "guide.pdf",
          body,
          passages: [{ id: "p", start: 0, end: body.length }],
          model_id: "model",
          model_revision: "revision",
          dimensions: 2,
          media_type: "application/pdf",
          text_sha256: "1".repeat(64),
          pages,
        },
      ]),
    );
  await login(send);
  expect(screen.getByRole("button", { name: "PDFs" })).toBeTruthy();
  fireEvent.change(screen.getByLabelText("Search your library"), {
    target: { value: "retention" },
  });
  expect(send).toHaveBeenCalledTimes(1);
  fireEvent.click(screen.getByRole("button", { name: "Search saved files" }));
  await screen.findByText(/Pages 2 · extracted characters/);
  fireEvent.click(screen.getByRole("button", { name: "Open saved text" }));
  const reader = await screen.findByRole("dialog", { name: "guide.pdf" });
  expect(within(reader).getByRole("heading", { name: "Page 2" })).toBeTruthy();
  expect(
    within(reader).getByLabelText("Saved document text").textContent,
  ).toContain(text);
});
it("reviews PDF bytes locally and saves them unchanged only after confirmation", async () => {
  const send = vi
    .fn<typeof fetch>()
    .mockResolvedValueOnce(
      reply({ items: [], next_cursor: null, pdf_enabled: true }),
    )
    .mockResolvedValueOnce(
      reply({ source_id: ID, version_id: ID, job_id: ID }, 202),
    )
    .mockResolvedValueOnce(
      reply({
        items: [
          {
            ...source,
            published_version_id: null,
            state: "queued",
            attempts: 0,
          },
        ],
        next_cursor: null,
        pdf_enabled: true,
      }),
    );
  await login(send);
  fireEvent.click(screen.getByRole("button", { name: "Add file" }));
  const bytes = new Uint8Array([
    37, 80, 68, 70, 45, 49, 46, 55, 10, 255, 0, 10, 37, 37, 69, 79, 70, 10,
  ]);
  fireEvent.change(
    screen.getByLabelText("Choose a PDF, TXT or Markdown file"),
    { target: { files: [new File([bytes], "guide.pdf")] } },
  );
  await screen.findByLabelText("Local PDF review");
  expect(send).toHaveBeenCalledTimes(1);
  fireEvent.click(screen.getByRole("checkbox"));
  fireEvent.click(screen.getByRole("button", { name: "Save selected file" }));
  await screen.findByText("Queued for processing");
  const payload = JSON.parse(send.mock.calls[1][1]?.body as string);
  expect(payload.media).toBe("application/pdf");
  expect(
    Array.from(atob(payload.content_base64), (c: string) => c.charCodeAt(0)),
  ).toEqual([...bytes]);
});
it("does not offer PDF import when the hosted server has not enabled it", async () => {
  await login(
    vi
      .fn<typeof fetch>()
      .mockResolvedValue(reply({ items: [], next_cursor: null })),
  );
  expect(screen.queryByRole("button", { name: "PDFs" })).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "Add file" }));
  expect(screen.getByLabelText("Choose a TXT or Markdown file")).toBeTruthy();
});
