import { cp, mkdir, rm, stat, writeFile } from "node:fs/promises";
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

function redirectPage({ title, description, target }) {
  return `<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="description" content="${description}" />
    <meta http-equiv="refresh" content="0; url=${target}" />
    <link rel="canonical" href="${target}" />
    <title>${title}</title>
    <script>window.location.replace("${target}");</script>
  </head>
  <body>
    <p>Opening <a href="${target}">${target}</a>...</p>
  </body>
</html>
`;
}

const generatedDirs = ["assets", "blog", "creater", "home", "india", "projects", "stocks", "watchlist", "data"];
const generatedFiles = ["index.html", "CNAME", "Divyam_Matia_Resume.pdf", "profile-placeholder.jpg", ".nojekyll"];

await mkdir(distDir, { recursive: true });

const homeIndex = resolve(distDir, "home", "index.html");
const stocksIndex = resolve(distDir, "stocks", "index.html");
const watchlistIndex = resolve(distDir, "watchlist", "index.html");
const portfolioIndex = resolve(distDir, "index.html");
const createrIndex = resolve(distDir, "creater", "index.html");

if (await exists(portfolioIndex)) {
  await mkdir(dirname(createrIndex), { recursive: true });
  await cp(portfolioIndex, createrIndex, { force: true });
}

if (await exists(stocksIndex)) {
  await mkdir(dirname(watchlistIndex), { recursive: true });
  await cp(stocksIndex, watchlistIndex, { force: true });

  const indiaIndex = resolve(distDir, "india", "index.html");
  await mkdir(dirname(indiaIndex), { recursive: true });
  await cp(stocksIndex, indiaIndex, { force: true });

  // Scan sub-routes under /india/
  for (const scanId of ["scan100-200", "scan50-100"]) {
    const scanIndex = resolve(distDir, "india", scanId, "index.html");
    await mkdir(dirname(scanIndex), { recursive: true });
    await cp(stocksIndex, scanIndex, { force: true });
  }
}

// Use the home page as the root index
if (await exists(homeIndex)) {
  await cp(homeIndex, portfolioIndex, { force: true });
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
