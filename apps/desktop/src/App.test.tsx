import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import App from "./App";

// jsdom has no canvas renderer; interaction tests do not assert orb rendering.
vi.mock("thinking-orbs", () => ({
  ThinkingOrb: () => <span>Processing illustration</span>,
}));

beforeAll(() => {
  Object.defineProperty(window, "matchMedia", {
    value: vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });
});
afterEach(cleanup);
describe("preview workspace", () => {
  it("provides truthful privacy and copyright information without a fake report form", async () => {
    const user = userEvent.setup();
    render(<App />);
    await user.click(screen.getByRole("button", { name: "Privacy" }));
    expect(
      screen.getByRole("heading", { name: "Privacy in this preview" }),
    ).toBeTruthy();
    expect(
      screen.getByText(/Supabase is planned, not currently connected/),
    ).toBeTruthy();
    await user.click(screen.getByRole("button", { name: "Copyright" }));
    expect(screen.getByText("Reporting is not configured")).toBeTruthy();
    expect(screen.queryByRole("textbox")).toBeNull();
  });
  it("combines file type and text filtering and recovers from empty results", async () => {
    const user = userEvent.setup();
    render(<App />);
    await user.click(screen.getByRole("button", { name: "Photos" }));
    expect(
      screen
        .getAllByRole("button")
        .filter((el) => el.classList.contains("file-card")),
    ).toHaveLength(1);
    await user.type(
      screen.getByRole("textbox", { name: "Filter sample files" }),
      "nonexistent",
    );
    expect(screen.getByText("No sample files match.")).toBeTruthy();
    await user.click(screen.getByRole("button", { name: "Reset filters" }));
    expect(
      screen
        .getAllByRole("button")
        .filter((el) => el.classList.contains("file-card")),
    ).toHaveLength(4);
  });
  it("opens the selected source and makes disconnected chat explicit", async () => {
    const user = userEvent.setup();
    render(<App />);
    await user.click(
      screen.getByRole("button", { name: /The art of remembering/ }),
    );
    expect(screen.getByText("Source: The art of remembering")).toBeTruthy();
    expect(screen.getByText("Chat is not connected yet")).toBeTruthy();
    await user.click(screen.getByRole("button", { name: "Back to library" }));
    expect(
      screen.getByRole("textbox", { name: "Filter sample files" }),
    ).toBeTruthy();
  });
  it("does not pretend to upload files or install models", async () => {
    const user = userEvent.setup();
    render(<App />);
    await user.click(screen.getByRole("button", { name: "Import files" }));
    expect(screen.getByRole("status").textContent).toContain(
      "does not read, upload or index",
    );
    await user.click(screen.getByRole("button", { name: "Models & setup" }));
    expect(screen.getAllByText("Not connected")).toHaveLength(4);
  });
});
