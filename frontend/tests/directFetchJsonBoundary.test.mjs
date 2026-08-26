import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const files = [
  "src/pages/EnterpriseSettings.tsx",
  "src/pages/AdminCompanies.tsx",
  "src/pages/Login.tsx",
  "src/pages/UserManagement.tsx",
  "src/pages/Dashboard.tsx",
  "src/pages/SSOEntry.tsx",
  "src/pages/OAuthCallback.tsx",
  "src/pages/Layout.tsx",
  "src/services/platformMetricsApi.ts",
];

test("direct page fetchJson calls are unknown-validated or explicitly void", () => {
  for (const file of files) {
    const source = readFileSync(new URL(`../${file}`, import.meta.url), "utf8");
    assert.doesNotMatch(source, /fetchJson<(?!unknown>|void>)/, file);
    assert.doesNotMatch(source, /fetchJson\s*\(/, file);
  }
});

test("each direct response family uses strict parsers", () => {
  const source = files
    .map((file) => readFileSync(new URL(`../${file}`, import.meta.url), "utf8"))
    .join("\n");
  for (const parser of [
    "parseSsoProviders",
    "parseSsoSessionStatus",
    "parseUserManagementUsers",
    "parseDashboardOkrObjectives",
    "parseNotificationItems",
    "parseEnterpriseToolList",
    "parseMcpTestResult",
    "parseOAuthCallbackResponse",
    "parsePlatformSettings",
    "parseTimeSeries",
  ]) {
    assert.match(source, new RegExp(parser), parser);
  }
});
