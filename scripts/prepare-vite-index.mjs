import { copyFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(scriptDir, "..");

await copyFile(
  resolve(scriptDir, "source-index.html"),
  resolve(repoRoot, "index.html")
);
