import { readdir, readFile } from "node:fs/promises";
import { extname, relative, resolve } from "node:path";

const sourceRoot = resolve("src");
const approvedSessionStorageFile = "src/lib/registration-draft-storage.ts";
const sourceExtensions = new Set([".ts", ".tsx", ".js", ".jsx"]);
const violations = [];

async function sourceFiles(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const nested = await Promise.all(entries.map(async (entry) => {
    const path = resolve(directory, entry.name);
    if (entry.isDirectory()) return sourceFiles(path);
    return sourceExtensions.has(extname(entry.name)) ? [path] : [];
  }));
  return nested.flat();
}

for (const file of await sourceFiles(sourceRoot)) {
  const projectPath = relative(resolve("."), file).replaceAll("\\", "/");
  const source = await readFile(file, "utf8");
  if (/\blocalStorage\b/.test(source)) {
    violations.push(`${projectPath}: localStorage is prohibited for application authentication safety.`);
  }
  if (/\bsessionStorage\b/.test(source) && projectPath !== approvedSessionStorageFile) {
    violations.push(`${projectPath}: sessionStorage is permitted only in the reviewed registration-draft module.`);
  }
}

const approvedSource = await readFile(resolve(approvedSessionStorageFile), "utf8");
for (const forbidden of ["password", "token", "sessionid", "csrf", "secret"]) {
  if (approvedSource.toLowerCase().includes(forbidden)) {
    violations.push(`${approvedSessionStorageFile}: forbidden sensitive term '${forbidden}' found.`);
  }
}

if (violations.length) {
  console.error(["Client storage security check failed:", ...violations.map((item) => `- ${item}`)].join("\n"));
  process.exit(1);
}

console.log("Client storage security check passed: authentication tokens are not stored in browser storage.");
