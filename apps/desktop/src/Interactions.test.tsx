import { afterEach, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { OrbPreview, ReadingPane } from "./components/Interactions";

vi.mock("motion/react", async (original) => ({
  ...(await original<typeof import("motion/react")>()),
  useReducedMotion: () => true,
}));
vi.mock("thinking-orbs", () => ({
  ThinkingOrb: ({ paused }: { paused: boolean }) => (
    <span>{paused ? "Indicator paused" : "Indicator playing"}</span>
  ),
}));
afterEach(cleanup);
it("keeps optional animation and smooth scrolling off under reduced motion", () => {
  render(
    <>
      <OrbPreview />
      <ReadingPane>Sample source</ReadingPane>
    </>,
  );
  expect(screen.getByText("Indicator paused")).toBeTruthy();
  expect(
    (
      screen.getByRole("button", {
        name: "Reduced motion enabled",
      }) as HTMLButtonElement
    ).disabled,
  ).toBe(true);
  const checkbox = screen.getByRole("checkbox") as HTMLInputElement;
  expect(checkbox.disabled).toBe(true);
  expect(checkbox.checked).toBe(false);
});
