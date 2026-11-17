/** Synthetic HTTP/geometry fixtures; these do not demonstrate live cloud OCR. */
import pngData from "../test-fixtures/image-ocr/synthetic-note.png?inline";
import jpegData from "../test-fixtures/image-ocr/synthetic-note.jpg?inline";
import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Library from "./Library";
import { LibraryClient, validImageBytes } from "../services/libraryClient";
import { readTextFile } from "../services/textFile";

vi.mock("../services/pilotAuth", async (original) => ({
  ...(await original<object>()),
  signInPilot: vi.fn(async () => "synthetic-session"),
}));
vi.mock("../services/pilotConfiguration", () => ({
  connectedPilot: true,
  libraryEndpoint: () => ({
    url: "https://library.example.test",
    allowLoopback: false,
  }),
}));
const { webcrypto } = await vi.importActual<{ webcrypto: Crypto }>(
  "node:crypto",
);
const raw = Uint8Array.from(atob(pngData.split(",")[1]), (c) =>
  c.charCodeAt(0),
);
const jpeg = Uint8Array.from(atob(jpegData.split(",")[1]), (c) =>
  c.charCodeAt(0),
);
async function sha256(data: Uint8Array) {
  const digest = await webcrypto.subtle.digest(
    "SHA-256",
    Uint8Array.from(data),
  );
  return Array.from(new Uint8Array(digest), (byte) =>
    byte.toString(16).padStart(2, "0"),
  ).join("");
}
const lines = [
  "Gather image pilot",
  "Orchard backups last fourteen days.",
  "Archive requests belong in the Cedar queue.",
];
const body = lines.join("\n\n");
const ID = "00000000-0000-0000-0000-000000000001";
const source = {
  source_id: ID,
  title: "synthetic-note.png",
  kind: "file",
  created_at: "2026-11-04T01:00:00.000001Z",
  published_version_id: ID,
  processing_version_id: ID,
  job_id: ID,
  state: "ready",
  attempts: 1,
  error_code: null,
};
let offset = 0;
const regions = lines.map((line, index) => {
  const end = offset + line.length + (index < lines.length - 1 ? 2 : 0);
  const region = {
    number: index + 1,
    start: offset,
    end,
    x: 30,
    y: 25 + index * 55,
    width: 900,
    height: 35,
    confidence: 95,
  };
  offset = end;
  return region;
});
const document = {
  ...source,
  version_id: ID,
  body,
  source_sha256: await sha256(raw),
  text_sha256: await sha256(new TextEncoder().encode(body)),
  media_type: "image/png",
  width: 1000,
  height: 220,
  engine: "tesseract-5.5.0-lstm",
  ocr_model_sha256:
    "7d4322bd2a7749724879683fc3912cb542f19906c83bcc1a52132556427170b2",
  language: "eng",
  regions,
  image_base64: pngData.split(",")[1],
  model_id: "model",
  model_revision: "revision",
  dimensions: 2,
  passages: [{ id: "p1", start: 0, end: body.length }],
};
const reply = (value: unknown) =>
  new Response(JSON.stringify(value), {
    headers: { "Content-Type": "application/json" },
  });
const page = () =>
  reply({
    items: [source],
    next_cursor: null,
    cleanup_source_ids: [],
    image_enabled: true,
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
function setup(send: ReturnType<typeof vi.fn<typeof fetch>>) {
  vi.stubEnv("VITE_GATHER_PILOT_PUBLIC_KEY", "sb_publishable_test");
  vi.stubGlobal("fetch", send);
  vi.stubGlobal("crypto", webcrypto);
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

describe("image OCR contracts (synthetic HTTP fixtures)", () => {
  it("gates local image selection and checks PNG/JPEG dimensions before preview", async () => {
    const file = new File([raw], "synthetic-note.png", { type: "image/png" });
    await expect(
      readTextFile(file, new AbortController().signal),
    ).rejects.toMatchObject({ code: "file_type" });
    expect(validImageBytes(raw, "image/png")).toBe(true);
    expect(validImageBytes(jpeg, "image/jpeg")).toBe(true);
    const bomb = raw.slice();
    new DataView(bomb.buffer).setUint32(16, 100000);
    expect(validImageBytes(bomb, "image/png")).toBe(false);
    expect(validImageBytes(raw, "image/jpeg")).toBe(false);
  });
  it("reviews the selected image locally without uploading or pretending OCR has run", async () => {
    const send = vi.fn<typeof fetch>().mockResolvedValue(page());
    setup(send);
    render(<Library />);
    await login();
    fireEvent.click(screen.getByRole("button", { name: "Add file" }));
    await userEvent.upload(
      screen.getByLabelText("Choose an image or supported document"),
      new File([raw], "synthetic-note.png", { type: "image/png" }),
    );
    const image = await screen.findByRole("img", {
      name: "Selected image: synthetic-note.png",
    });
    expect(image.getAttribute("src")).toMatch(/^data:image\/png;base64,/);
    expect(
      (
        screen.getByRole("button", {
          name: "Save selected file",
        }) as HTMLButtonElement
      ).disabled,
    ).toBe(true);
    expect(send).toHaveBeenCalledTimes(1);
  });
  it("searches and opens the exact image with OCR-region citations and plain text", async () => {
    const send = vi.fn<typeof fetch>().mockImplementation(async (input) => {
      const path = new URL(String(input)).pathname;
      if (path === "/v1/list") return page();
      if (path === "/v1/open") return reply([document]);
      if (path === "/v1/search")
        return reply({
          version: "source-neighbors-v1",
          windows: [
            {
              source_id: ID,
              version_id: ID,
              source_sha256: document.source_sha256,
              title: source.title,
              text: body,
              start: 0,
              end: body.length,
              offset_unit: "unicode_code_point",
              passage_ids: ["p1"],
              seed_rank: 1,
              similarity: 0.9,
              media_type: "image/png",
              ocr_regions: [1, 2, 3],
            },
          ],
          utf8_bytes: new TextEncoder().encode(body).length,
          omitted_sources: [],
        });
      throw new Error("unexpected synthetic request");
    });
    setup(send);
    render(<Library />);
    await login();
    fireEvent.click(screen.getByRole("button", { name: "Images" }));
    fireEvent.change(screen.getByLabelText("Search your library"), {
      target: { value: "Where do archive requests belong?" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Search saved files" }));
    await screen.findByText(/OCR regions 1, 2, 3/);
    fireEvent.click(
      screen.getByRole("button", { name: `Preview ${source.title}` }),
    );
    fireEvent.click(screen.getByRole("button", { name: "Read saved text" }));
    const reader = await screen.findByRole("dialog", {
      name: "synthetic-note.png",
    });
    expect(
      within(reader)
        .getByRole("img", { name: "Saved original: synthetic-note.png" })
        .getAttribute("src"),
    ).toBe("data:image/png;base64," + document.image_base64);
    expect(
      within(reader).getByRole("heading", { name: "Text region 3" }),
    ).toBeTruthy();
    expect(within(reader).getByText(lines[2])).toBeTruthy();
  });
  it("rejects tampered original bytes and out-of-image OCR geometry", async () => {
    vi.stubGlobal("crypto", webcrypto);
    for (const value of [
      { ...document, source_sha256: "0".repeat(64) },
      {
        ...document,
        regions: [{ ...regions[0], width: 2000 }, ...regions.slice(1)],
      },
    ]) {
      const client = new LibraryClient("https://library.example.test", {
        fetch: vi.fn<typeof fetch>().mockResolvedValue(reply([value])),
      });
      client.setSession("synthetic");
      await expect(client.open(ID, ID)).rejects.toMatchObject({
        code: "invalid_response",
      });
    }
  });
  it("discards an image response when the account changes during integrity hashing", async () => {
    let release!: () => void;
    const gate = new Promise<void>((resolve) => {
      release = resolve;
    });
    const digest = vi.fn(
      async (algorithm: AlgorithmIdentifier, data: BufferSource) => {
        await gate;
        return webcrypto.subtle.digest(
          algorithm as string,
          data as Uint8Array<ArrayBuffer>,
        );
      },
    );
    vi.stubGlobal("crypto", { subtle: { digest } });
    const client = new LibraryClient("https://library.example.test", {
      fetch: vi.fn<typeof fetch>().mockResolvedValue(reply([document])),
    });
    client.setSession("user-a");
    const pending = client.open(ID, ID).catch((error) => error);
    await waitFor(() => expect(digest).toHaveBeenCalledTimes(2));
    client.setSession("user-b");
    release();
    expect(await pending).toMatchObject({ code: "cancelled" });
  });
});
