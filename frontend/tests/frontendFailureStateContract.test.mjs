import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const adminCompanies = readFileSync(
  new URL("../src/pages/AdminCompanies.tsx", import.meta.url),
  "utf8",
);
const enterpriseSettings = readFileSync(
  new URL("../src/pages/EnterpriseSettings.tsx", import.meta.url),
  "utf8",
);
const platformDashboard = readFileSync(
  new URL("../src/pages/PlatformDashboard.tsx", import.meta.url),
  "utf8",
);
const livePanelUtils = readFileSync(
  new URL("../src/components/AgentBayLivePanel.utils.ts", import.meta.url),
  "utf8",
);

test("admin configuration saves require an authoritative successful load", () => {
  assert.match(adminCompanies, /platformConfigReady/);
  assert.match(adminCompanies, /if \(!platformConfigReady\) return false/);
  assert.match(adminCompanies, /platformConfigLoadError/);
  assert.doesNotMatch(
    adminCompanies,
    /getPlatformSettings\(\)[\s\S]*?\.catch\(\(\) => \{\}\)/,
  );
});

test("quota and company introduction failures cannot look editable and blank", () => {
  assert.match(enterpriseSettings, /quotaLoadState\.status !== "ready"/);
  assert.match(enterpriseSettings, /companyIntroLoadState\.status !== "ready"/);
  assert.match(enterpriseSettings, /companyIntroLoadState\.error/);
  assert.doesNotMatch(
    enterpriseSettings,
    /tenant-quotas[\s\S]{0,240}\.catch\(\(\) => \{\}\)/,
  );
});

test("platform metric refresh failures retain data and render an error", () => {
  assert.match(platformDashboard, /platformMetricsApi/);
  assert.match(platformDashboard, /setStatsError/);
  assert.match(platformDashboard, /setLeadersError/);
  assert.match(platformDashboard, /setEnhancedError/);
  assert.doesNotMatch(platformDashboard, /if \(!response\.ok\) return \[\]/);
});

test("live code truncation limit stays private to its owner", () => {
  assert.match(livePanelUtils, /const MAX_LIVE_CODE_OUTPUT_CHARS/);
  assert.doesNotMatch(
    livePanelUtils,
    /export const MAX_LIVE_CODE_OUTPUT_CHARS/,
  );
});
