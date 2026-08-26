import assert from "node:assert/strict";
import test from "node:test";

import { parseHttpErrorResponse } from "../src/services/apiError.ts";
import { requestAgentToolsWithConfig } from "../src/pages/agent-detail/toolsManagerData.ts";

test("tool settings load only the canonical with-config response", async () => {
  const calls = [];
  const payload = [{ id: "tool-1" }];
  const result = await requestAgentToolsWithConfig({
    agentId: "agent / 1",
    token: "browser-token",
    parsePayload: (value) => value,
    parseError: parseHttpErrorResponse,
    fetchImpl: async (url, init) => {
      calls.push({ url, init });
      return new Response(JSON.stringify(payload), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    },
  });

  assert.deepEqual(result, payload);
  assert.deepEqual(calls, [
    {
      url: "/api/tools/agents/agent%20%2F%201/with-config",
      init: { headers: { Authorization: "Bearer browser-token" } },
    },
  ]);
});

test("a missing with-config endpoint fails instead of calling the legacy endpoint", async () => {
  const calls = [];
  const compatibilityError = new Error("with-config endpoint missing");

  await assert.rejects(
    requestAgentToolsWithConfig({
      agentId: "agent-1",
      token: null,
      parsePayload: (value) => value,
      parseError: async () => compatibilityError,
      fetchImpl: async (url) => {
        calls.push(url);
        return new Response("not found", { status: 404 });
      },
    }),
    (error) => error === compatibilityError,
  );

  assert.deepEqual(calls, ["/api/tools/agents/agent-1/with-config"]);
});

test("authorization and server failures preserve canonical HTTP errors", async () => {
  for (const status of [401, 403, 500]) {
    const calls = [];
    await assert.rejects(
      requestAgentToolsWithConfig({
        agentId: "agent-1",
        token: "browser-token",
        parsePayload: (value) => value,
        parseError: parseHttpErrorResponse,
        fetchImpl: async (url) => {
          calls.push(url);
          return new Response(
            JSON.stringify({
              error: {
                code: `tools_${status}`,
                message: `tools request failed with ${status}`,
              },
            }),
            {
              status,
              headers: { "Content-Type": "application/json" },
            },
          );
        },
      }),
      (error) =>
        error.status === status &&
        error.code === `tools_${status}` &&
        error.message === `tools request failed with ${status}`,
    );
    assert.deepEqual(calls, ["/api/tools/agents/agent-1/with-config"]);
  }
});
