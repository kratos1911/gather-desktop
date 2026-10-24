// @vitest-environment node
import { describe, expect, it, vi } from "vitest";
import { signInPilot, PILOT_EMAILS } from "./pilotAuth";
const key = "sb_publishable_synthetic";
const result = {
  access_token: "synthetic-access",
  refresh_token: "never-retained",
  user: { id: "8b8de9a3-6600-465d-9ae6-8a0f2271c1dc", email: PILOT_EMAILS[0] },
};
const response = (value: unknown) =>
  new Response(JSON.stringify(value), {
    headers: { "Content-Type": "application/json" },
  });
describe("operator auth (synthetic HTTP)", () => {
  it("uses the fixed project and returns only the in-memory access token", async () => {
    const send = vi.fn<typeof fetch>().mockResolvedValue(response(result));
    await expect(
      signInPilot(
        PILOT_EMAILS[0],
        "synthetic-password",
        key,
        new AbortController().signal,
        send,
      ),
    ).resolves.toBe("synthetic-access");
    expect(send.mock.calls[0][0]).toBe(
      "https://fatolholcjxpwocnpzws.supabase.co/auth/v1/token?grant_type=password",
    );
    expect(send.mock.calls[0][1]).toMatchObject({
      credentials: "omit",
      redirect: "error",
      cache: "no-store",
    });
  });
  it("rejects unsupported accounts before network and mismatched identity after sign-in", async () => {
    const send = vi.fn<typeof fetch>();
    await expect(
      signInPilot(
        "other@example.invalid",
        "pw",
        key,
        new AbortController().signal,
        send,
      ),
    ).rejects.toThrow("invalid_pilot_configuration");
    expect(send).not.toHaveBeenCalled();
    send.mockResolvedValue(
      response({ ...result, user: { ...result.user, id: "foreign" } }),
    );
    await expect(
      signInPilot(
        PILOT_EMAILS[0],
        "pw",
        key,
        new AbortController().signal,
        send,
      ),
    ).rejects.toThrow("pilot_signin_failed");
  });
  it("never exposes sign-in response errors or accepts oversized token replies", async () => {
    for (const reply of [
      new Response("secret backend error", { status: 401 }),
      response({ ...result, access_token: "x".repeat(65537) }),
    ]) {
      const send = vi.fn<typeof fetch>().mockResolvedValue(reply);
      await expect(
        signInPilot(
          PILOT_EMAILS[0],
          "pw",
          key,
          new AbortController().signal,
          send,
        ),
      ).rejects.toThrow("pilot_signin_failed");
    }
  });
});
