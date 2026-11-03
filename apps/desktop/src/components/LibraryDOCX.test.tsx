/** Synthetic HTTP/header fixtures; not actual DOCX extraction or live semantic proof. */
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
import { DOCX_MEDIA } from "../services/libraryClient";
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
const body = "First page.\n\nSecond <b>page</b> holds the retention rule.";
const pages = [
  { number: 1, start: 0, end: 13 },
  { number: 2, start: 13, end: body.length },
];
const source = {
  source_id: ID,
  title: "guide.docx",
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

it("uses paragraph citations and renders saved DOCX text literally", async () => {
  const send = vi
    .fn<typeof fetch>()
    .mockResolvedValueOnce(
      reply({ items: [source], next_cursor: null, docx_enabled: true }),
    )
    .mockResolvedValueOnce(
      reply({
        version: "source-neighbors-v1",
        windows: [
          {
            source_id: ID,
            version_id: ID,
            source_sha256: "0".repeat(64),
            title: "guide.docx",
            text: body.slice(13),
            start: 13,
            end: body.length,
            offset_unit: "unicode_code_point",
            passage_ids: ["p"],
            seed_rank: 1,
            similarity: 0.9,
            media_type: DOCX_MEDIA,
            paragraphs: [2],
          },
        ],
        utf8_bytes: new TextEncoder().encode(body.slice(13)).length,
        omitted_sources: [],
      }),
    )
    .mockResolvedValueOnce(
      reply([
        {
          source_id: ID,
          version_id: ID,
          source_sha256: "0".repeat(64),
          title: "guide.docx",
          body,
          passages: [{ id: "p", start: 0, end: body.length }],
          model_id: "model",
          model_revision: "revision",
          dimensions: 2,
          media_type: DOCX_MEDIA,
          text_sha256: "1".repeat(64),
          paragraphs: pages,
        },
      ]),
    );
  await login(send);
  expect(screen.getByRole("button", { name: "Word documents" })).toBeTruthy();
  fireEvent.change(screen.getByLabelText("Search your library"), {
    target: { value: "retention" },
  });
  expect(send).toHaveBeenCalledTimes(1);
  fireEvent.click(screen.getByRole("button", { name: "Search saved files" }));
  await screen.findByText(/Paragraphs 2 · extracted characters/);
  fireEvent.click(screen.getByRole("button", { name: "Open saved text" }));
  const reader = await screen.findByRole("dialog", { name: "guide.docx" });
  expect(
    within(reader).getByRole("heading", { name: "Paragraph 2" }),
  ).toBeTruthy();
  expect(within(reader).queryByRole("heading", { name: "Page 2" })).toBeNull();
  expect(
    within(reader).getByLabelText("Saved document text").textContent,
  ).toContain(body.slice(13));
  expect(reader.querySelector("b")).toBeNull();
  expect(send).toHaveBeenCalledTimes(3);
});
it("reviews Word archive bytes locally and preserves them after explicit confirmation", async () => {
  const send = vi
    .fn<typeof fetch>()
    .mockResolvedValueOnce(
      reply({
        items: [],
        next_cursor: null,
        pdf_enabled: true,
        docx_enabled: true,
      }),
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
        docx_enabled: true,
      }),
    );
  await login(send);
  fireEvent.click(screen.getByRole("button", { name: "Add file" }));
  const bytes = new Uint8Array([80, 75, 3, 4, 255, 0, 1]); // Header fixture only; backend validates OOXML.
  fireEvent.change(
    screen.getByLabelText("Choose a DOCX, PDF, TXT or Markdown file"),
    { target: { files: [new File([bytes], "guide.docx")] } },
  );
  await screen.findByLabelText("Local Word document review");
  expect(send).toHaveBeenCalledTimes(1);
  expect(
    (
      screen.getByRole("button", {
        name: "Save selected file",
      }) as HTMLButtonElement
    ).disabled,
  ).toBe(true);
  fireEvent.click(screen.getByRole("checkbox"));
  fireEvent.click(screen.getByRole("button", { name: "Save selected file" }));
  await screen.findByText("Queued for processing");
  const payload = JSON.parse(send.mock.calls[1][1]?.body as string);
  expect(payload.media).toBe(DOCX_MEDIA);
  expect(
    Array.from(atob(payload.content_base64), (c: string) => c.charCodeAt(0)),
  ).toEqual([...bytes]);
});
it("keeps DOCX import disabled when the server has not advertised support", async () => {
  const send = vi
    .fn<typeof fetch>()
    .mockResolvedValue(reply({ items: [], next_cursor: null }));
  await login(send);
  expect(screen.queryByRole("button", { name: "Word documents" })).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "Add file" }));
  const input = screen.getByLabelText(
    "Choose a TXT or Markdown file",
  ) as HTMLInputElement;
  expect(input.accept).not.toContain(".docx");
  expect(send).toHaveBeenCalledTimes(1);
});
