import { afterEach, describe, expect, it, vi } from "vitest";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { TextFileImport } from "./TextFileImport";

afterEach(cleanup);
describe("reviewed private file selection", () => {
  it("never saves on selection; requires confirmation and renders Markdown/HTML as plain text", async () => {
    const save = vi.fn().mockResolvedValue(true);
    const { container } = render(
      <TextFileImport disabled={false} onSave={save} />,
    );
    const body = "# File\r\n<script>untrusted</script>";
    fireEvent.change(screen.getByLabelText("Choose a TXT or Markdown file"), {
      target: { files: [new File([body], "note.md")] },
    });
    expect(
      (await screen.findByLabelText("Local plain-text preview")).textContent,
    ).toBe(body);
    expect(container.querySelector("script")).toBeNull();
    expect(save).not.toHaveBeenCalled();
    const button = screen.getByRole("button", {
      name: "Save selected file",
    }) as HTMLButtonElement;
    expect(button.disabled).toBe(true);
    fireEvent.click(screen.getByRole("checkbox"));
    fireEvent.click(button);
    await waitFor(() => expect(save).toHaveBeenCalledOnce());
    expect(save.mock.calls[0][0].media).toBe("text/markdown");
    await waitFor(() => expect(screen.queryByText("note.md")).toBeNull());
  });
  it("clears confirmation and prior content when selection changes or becomes invalid", async () => {
    const save = vi.fn();
    render(<TextFileImport disabled={false} onSave={save} />);
    const input = screen.getByLabelText("Choose a TXT or Markdown file");
    fireEvent.change(input, {
      target: { files: [new File(["First"], "first.txt")] },
    });
    await screen.findByText("first.txt");
    fireEvent.click(screen.getByRole("checkbox"));
    fireEvent.change(input, {
      target: { files: [new File(["Second"], "second.md")] },
    });
    await screen.findByText("second.md");
    expect((screen.getByRole("checkbox") as HTMLInputElement).checked).toBe(
      false,
    );
    expect(screen.queryByText("First")).toBeNull();
    fireEvent.change(input, {
      target: { files: [new File(["\u0000"], "bad.txt")] },
    });
    await screen.findByRole("alert");
    expect(
      screen.queryByRole("button", { name: "Save selected file" }),
    ).toBeNull();
    expect(save).not.toHaveBeenCalled();
  });
  it("discards a selection that finishes after unmount", async () => {
    const save = vi.fn();
    const view = render(<TextFileImport disabled={false} onSave={save} />);
    fireEvent.change(screen.getByLabelText("Choose a TXT or Markdown file"), {
      target: { files: [new File(["Delayed"], "delayed.txt")] },
    });
    view.unmount();
    await Promise.resolve();
    expect(save).not.toHaveBeenCalled();
  });
});
