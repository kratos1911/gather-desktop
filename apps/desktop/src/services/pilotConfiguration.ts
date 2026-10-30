/** Public build configuration only. Never accepts backend credentials. */
export const CLOUD_LIBRARY_URL =
  "https://gather-library-pilot-119730530113.asia-south1.run.app";
export const connectedPilot =
  import.meta.env.VITE_GATHER_CONNECTED_PILOT === "1";
export const pilotAvailable = import.meta.env.DEV || connectedPilot;
export function libraryEndpoint() {
  if (connectedPilot) return { url: CLOUD_LIBRARY_URL, allowLoopback: false };
  if (import.meta.env.DEV)
    return { url: "http://127.0.0.1:8765", allowLoopback: true };
  throw new Error("pilot_not_enabled");
}
