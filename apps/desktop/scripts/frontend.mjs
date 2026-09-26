// Run frontend tools without relying on a global npm shim inside Tauri hooks.
import { spawnSync } from "node:child_process";
const build = process.argv[2] === "build";
const commands = build
  ? [
      ["node_modules/typescript/bin/tsc"],
      ["node_modules/vite/bin/vite.js", "build"],
    ]
  : [["node_modules/vite/bin/vite.js"]];
for (const args of commands) {
  const result = spawnSync(process.execPath, args, { stdio: "inherit" });
  if (result.error) {
    console.error(result.error.message);
    process.exit(1);
  }
  if (result.status !== 0) process.exit(result.status ?? 1);
}
