import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import { AppError } from "../src/services/apiError.ts";
import {
  parseControlScreenshotResponse,
  parseTenantSetupResponse,
  parseUploadResponse,
} from "../src/services/apiResponseParsers.ts";

const tenant = {
  id: "tenant-1",
  name: "Acme",
  slug: "acme",
  im_provider: "web_only",
  timezone: "Asia/Shanghai",
  country_region: "001",
  is_active: true,
  sso_enabled: false,
  sso_domain: null,
  a2a_async_enabled: true,
  default_model_id: null,
  logo_url: null,
  created_at: null,
};

test("tenant setup parser accepts the documented success contract", () => {
  assert.deepEqual(
    parseTenantSetupResponse({
      tenant,
      access_token: "token-1",
      role: "org_admin",
    }),
    { tenant, access_token: "token-1", role: "org_admin" },
  );
});

test("tenant setup parser rejects malformed successful payloads", () => {
  assert.throws(
    () => parseTenantSetupResponse({ tenant, access_token: 42 }),
    (error) =>
      error instanceof AppError && error.code === "invalid_api_response",
  );
});

test("upload and control parsers validate fields consumed by the UI", () => {
  const upload = parseUploadResponse({
    filename: "brief.pdf",
    extracted_text: "brief",
    workspace_path: "workspace/uploads/brief.pdf",
    image_data_url: "",
  });
  assert.equal(upload.filename, "brief.pdf");

  assert.deepEqual(
    parseControlScreenshotResponse({
      status: "ok",
      screenshot: "data:image/png;base64,AA==",
      screen_size: { width: 1440, height: 900 },
    }).screen_size,
    { width: 1440, height: 900 },
  );

  assert.throws(
    () =>
      parseControlScreenshotResponse({
        status: "ok",
        screenshot: "data:image/png;base64,AA==",
        screen_size: { width: "1440", height: 900 },
      }),
    (error) =>
      error instanceof AppError && error.code === "invalid_api_response",
  );
});

test("request reads a successful JSON response body only once", () => {
  const source = readFileSync(
    new URL("../src/services/api.ts", import.meta.url),
    "utf8",
  );
  assert.doesNotMatch(
    source,
    /const value: unknown = await res\.json\(\);[\s\S]{0,120}return parser \? parser\(value\) : res\.json\(\)/,
  );
});
