import { cp, mkdir, rm, stat } from "node:fs/promises";
import { dirname, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(scriptDir, "..");
const distDir = resolve(repoRoot, "dist");

function assertInsideRepo(target) {
  const normalizedRoot = repoRoot.endsWith(sep) ? repoRoot : `${repoRoot}${sep}`;
  if (target !== repoRoot && !target.startsWith(normalizedRoot)) {
    throw new Error(`Refusing to write outside repo: ${target}`);
  }
}

async function exists(path) {
  try {
    await stat(path);
    return true;
  } catch {
    return false;
  }
}

const generatedDirs = ["assets", "blog", "projects", "stocks"];
const generatedFiles = ["index.html", "Divyam_Matia_Resume.pdf", "profile-placeholder.jpg", ".nojekyll"];

await mkdir(distDir, { recursive: true });

const stocksIndex = resolve(distDir, "stocks", "index.html");
const watchlistIndex = resolve(distDir, "stocks", "watchlist", "index.html");
if (await exists(stocksIndex)) {
  await mkdir(dirname(watchlistIndex), { recursive: true });
  await cp(stocksIndex, watchlistIndex, { force: true });
}

for (const dir of generatedDirs) {
  const from = resolve(distDir, dir);
  const to = resolve(repoRoot, dir);
  assertInsideRepo(to);
  await rm(to, { recursive: true, force: true });
  if (await exists(from)) {
    await cp(from, to, { recursive: true });
  }
}

for (const file of generatedFiles) {
  const from = resolve(distDir, file);
  const to = resolve(repoRoot, file);
  assertInsideRepo(to);
  if (await exists(from)) {
    await cp(from, to, { force: true });
  }
}
