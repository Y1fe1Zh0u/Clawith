import assert from "node:assert/strict";
import test from "node:test";

import {
  parseStoredChannelConfig,
  parseWebhookConfig,
  readOptionalChannelResource,
} from "../src/services/channelConfigResponse.ts";

test("only an explicit 404 is treated as an unconfigured channel", async () => {
  assert.equal(
    await readOptionalChannelResource(
      async () => Promise.reject({ status: 404 }),
      parseStoredChannelConfig,
    ),
    null,
  );
  for (const status of [401, 403, 500]) {
    await assert.rejects(() =>
      readOptionalChannelResource(
        async () => Promise.reject({ status }),
        parseStoredChannelConfig,
      ),
    );
  }
});

test("malformed successful channel responses remain errors", async () => {
  await assert.rejects(
    () =>
      readOptionalChannelResource(
        async () => ({ is_configured: "yes" }),
        parseStoredChannelConfig,
      ),
    /channel configuration/i,
  );
  assert.throws(() => parseWebhookConfig({ webhook_url: 42 }), /webhook/i);
});

test("valid channel and webhook responses are parsed", () => {
  assert.deepEqual(
    parseStoredChannelConfig({
      is_configured: true,
      is_connected: false,
      app_id: "app",
      extra_config: { connection_mode: "websocket" },
    }),
    {
      is_configured: true,
      is_connected: false,
      app_id: "app",
      extra_config: { connection_mode: "websocket" },
    },
  );
  assert.deepEqual(
    parseWebhookConfig({ webhook_url: "https://example.test" }),
    {
      webhook_url: "https://example.test",
    },
  );
});
