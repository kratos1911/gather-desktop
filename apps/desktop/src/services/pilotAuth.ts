/** Fixed hosted test accounts only. Tokens stay in memory; no signup/refresh storage. */
import { LibraryClientError } from "./libraryClient";
export const PILOT_NOTE =
  "Synthetic Gather pilot note. Database records are protected through ownership checks and row-level security policies.";
export const PILOT_QUERY = "How is access to database records restricted?";
export const PILOT_EMAILS = [
  "gather-pilot-a@example.invalid",
  "gather-pilot-b@example.invalid",
] as const;
const IDS = [
  "8b8de9a3-6600-465d-9ae6-8a0f2271c1dc",
  "903b7ed0-9d21-467c-907a-4032d589f4c4",
];
const BASE = "https://fatolholcjxpwocnpzws.supabase.co";
export async function signInPilot(
  email: string,
  password: string,
  key: string,
  signal: AbortSignal,
  send: typeof fetch = fetch,
): Promise<string> {
  const index = PILOT_EMAILS.findIndex((item) => item === email);
  if (
    index < 0 ||
    !password ||
    !key.startsWith("sb_publishable_") ||
    key.length > 8192 ||
    /\s/.test(key)
  )
    throw new LibraryClientError("invalid_pilot_configuration");
  const controller = new AbortController();
  const abort = () => controller.abort();
  signal.addEventListener("abort", abort, { once: true });
  if (signal.aborted) controller.abort();
  const timeout = setTimeout(abort, 5000);
  let reader: ReadableStreamDefaultReader<Uint8Array> | undefined;
  try {
    const response = await send(`${BASE}/auth/v1/token?grant_type=password`, {
      method: "POST",
      headers: { apikey: key, "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
      signal: controller.signal,
      credentials: "omit",
      redirect: "error",
      cache: "no-store",
    });
    if (
      !response.ok ||
      response.headers.get("content-type")?.split(";")[0] !==
        "application/json" ||
      !response.body
    )
      throw new Error();
    reader = response.body.getReader();
    let size = 0;
    const chunks: Uint8Array[] = [];
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      size += value.length;
      if (size > 65536) throw new Error();
      chunks.push(value);
    }
    if (controller.signal.aborted) throw new Error();
    const raw = new Uint8Array(size);
    let offset = 0;
    for (const chunk of chunks) {
      raw.set(chunk, offset);
      offset += chunk.length;
    }
    const result = JSON.parse(
      new TextDecoder("utf-8", { fatal: true }).decode(raw),
    );
    if (
      result.user?.id !== IDS[index] ||
      result.user?.email !== email ||
      typeof result.access_token !== "string" ||
      !result.access_token ||
      result.access_token.length > 8192 ||
      /[^\x21-\x7e]/.test(result.access_token)
    )
      throw new Error();
    return result.access_token;
  } catch {
    throw new LibraryClientError(
      signal.aborted ? "cancelled" : "pilot_signin_failed",
    );
  } finally {
    controller.abort();
    void reader?.cancel().catch(() => {});
    clearTimeout(timeout);
    signal.removeEventListener("abort", abort);
  }
}
