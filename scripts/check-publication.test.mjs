import { strict as assert } from "node:assert";
import { test } from "node:test";
import { credentialFindings, privatePath } from "./check-publication.mjs";

test("private files and generated directories are blocked", () => {
  for (const file of [".env", "backend/.env.local", "keys/server.pem", "backup.sql.gz", "frontend/node_modules/a.js", "backend/.venv/file", ".validation/run.log", "service-account-prod.json"]) {
    assert.equal(privatePath(file), true, file);
  }
});
test("templates, assets and initialization SQL are publishable", () => {
  for (const file of [".env.example", "backend/.env.example", "backend/scripts/init-extensions.sql", "frontend/public/brands/apple.svg", "docs/screenshots/map.png"]) {
    assert.equal(privatePath(file), false, file);
  }
});
test("Windows paths are normalized", () => assert.equal(privatePath("frontend\\.env.production"), true));
test("credential matches are redacted and identify the line", () => {
  const token = "ghp_" + "a".repeat(36);
  const findings = credentialFindings("first line\n" + token);
  assert.deepEqual(findings, [{line: 2, rule: "GitHub token"}]);
  assert.equal(JSON.stringify(findings).includes(token), false);
});
test("private-key header is detected", () => {
  const header = ["-----BEGIN", "OPENSSH", "PRIVATE KEY-----"].join(" ");
  assert.equal(credentialFindings(header)[0].rule, "private key");
});
test("empty configuration and documented placeholders are not credentials", () => {
  assert.deepEqual(credentialFindings("LLM_API_KEY=\nDATABASE_URL=postgresql://test:test@localhost/test\nREPLACE_WITH_A_STRONG_PASSWORD"), []);
});
