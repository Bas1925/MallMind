// Lightweight pre-publication guard, not a complete security audit.
// Reports only paths/rule names, never matched credential values.
import { execFileSync } from "node:child_process";
import { readFileSync, statSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const rules = [
  ["private key", /-----BEGIN (?:RSA |EC |OPENSSH |DSA |ENCRYPTED )?PRIVATE KEY-----/],
  ["GitHub token", /\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{40,})\b/],
  ["provider secret key", /\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{32,}\b/],
  ["AWS access key", /\b(?:AKIA|ASIA)[A-Z0-9]{16}\b/],
  ["Google API key", /\bAIza[A-Za-z0-9_-]{35}\b/],
  ["Slack token", /\bxox[baprs]-[A-Za-z0-9-]{20,}\b/],
];

export function privatePath(filename) {
  const normalized = filename.replaceAll("\\", "/");
  const basename = path.posix.basename(normalized);
  if (basename === ".env.example") return false;
  return /(^|\/)(node_modules|\.venv|venv|\.next|\.validation|pgdata)(\/|$)/i.test(normalized)
    || /^\.env(?:\.|$)/i.test(basename)
    || /^(id_rsa|id_ed25519|credentials\.json|service-account.*\.json)$/i.test(basename)
    || /\.(pem|key|p12|pfx|dump|sql\.gz)$/i.test(basename);
}

export function credentialFindings(text) {
  const findings = [];
  text.split(/\r?\n/).forEach((line, index) => {
    for (const [rule, pattern] of rules) {
      if (pattern.test(line)) findings.push({ line: index + 1, rule });
    }
  });
  return findings;
}

function main() {
  const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
  const git = (...args) => execFileSync("git", args, {
    cwd: root, encoding: "utf8", maxBuffer: 64 * 1024 * 1024,
  });
  const failures = [];
  const scan = (source, text) => {
    for (const finding of credentialFindings(text)) {
      failures.push(`${source}:${finding.line}: possible ${finding.rule} (redacted)`);
    }
  };
  const files = [...new Set(git("ls-files", "--cached", "--others", "--exclude-standard", "-z").split("\0").filter(Boolean))];
  for (const file of files) {
    if (privatePath(file)) failures.push(`${file}: private/generated path is publishable`);
    const absolute = path.join(root, file);
    let metadata;
    try { metadata = statSync(absolute); }
    catch (error) { if (error.code === "ENOENT") continue; throw error; }
    if (!metadata.isFile()) continue;
    if (metadata.size > 10 * 1024 * 1024) {
      failures.push(`${file}: exceeds this project's 10 MiB source-file budget`);
      continue;
    }
    const content = readFileSync(absolute);
    if (!content.includes(0)) scan(file, content.toString("utf8"));
  }
  scan("staged diff", git("diff", "--cached", "--no-ext-diff", "--no-textconv"));
  if (process.argv.includes("--history")) {
    const pastPaths = new Set(git("log", "--all", "--format=", "--name-only", "--no-renames").split(/\r?\n/).filter(Boolean));
    for (const file of pastPaths) {
      if (privatePath(file)) failures.push(`${file}: private/generated path exists in Git history`);
    }
    scan("history diff", git("log", "--all", "-p", "--format=commit %h", "--no-ext-diff", "--no-textconv"));
  }
  if (failures.length) {
    console.error(`Publication guard found ${failures.length} item(s):\n${failures.join("\n")}`);
    process.exitCode = 1;
    return;
  }
  console.log(`Publication guard passed for ${files.length} source paths${process.argv.includes("--history") ? " and reachable Git history" : ""}.`);
  console.log("No supported high-confidence credential patterns found. Review still required for personal data, generic passwords, image contents and unrecognized secret formats.");
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
