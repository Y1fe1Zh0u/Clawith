import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import { parseHttpErrorResponse } from "../src/services/apiError.ts";
import {
  parseCompleteList,
  requestAgentToolsWithConfig,
  requestToolsMutation,
  updateToolEnabled,
} from "../src/pages/agent-detail/toolsManagerData.ts";

const toolsManagerSource = readFileSync(
  new URL(
    "../src/pages/agent-detail/components/ToolsManager.tsx",
    import.meta.url,
  ),
  "utf8",
);

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

test("a malformed successful tools response fails explicitly", async () => {
  assert.match(toolsManagerSource, /typeof value\.enabled !== "boolean"/);
  assert.match(toolsManagerSource, /!isRecord\(value\.config_schema\)/);
  await assert.rejects(
    requestAgentToolsWithConfig({
      agentId: "agent-1",
      token: "browser-token",
      parsePayload: (payload) =>
        parseCompleteList({
          payload,
          contractName: "agent tools",
          parseItem: (item) =>
            typeof item === "object" && item !== null && "id" in item
              ? item
              : null,
        }),
      parseError: parseHttpErrorResponse,
      fetchImpl: async () =>
        new Response(JSON.stringify([{ missing_id: true }]), { status: 200 }),
    }),
    /invalid agent tools response/i,
  );
});

test("tool mutation failures preserve HTTP errors and the reducer can roll back", async () => {
  const initial = [
    { id: "tool-1", enabled: false },
    { id: "tool-2", enabled: true },
  ];
  const toolIds = new Set(["tool-1"]);
  const optimistic = updateToolEnabled(initial, toolIds, true);
  assert.deepEqual(optimistic, [
    { id: "tool-1", enabled: true },
    { id: "tool-2", enabled: true },
  ]);
  assert.deepEqual(updateToolEnabled(optimistic, toolIds, false), initial);

  await assert.rejects(
    requestToolsMutation({
      url: "/api/tools/agents/agent-1",
      token: "browser-token",
      method: "PUT",
      body: [{ tool_id: "tool-1", enabled: true }],
      parseError: parseHttpErrorResponse,
      fetchImpl: async () =>
        new Response(
          JSON.stringify({
            error: { code: "tools_403", message: "mutation denied" },
          }),
          { status: 403 },
        ),
    }),
    (error) =>
      error.status === 403 &&
      error.code === "tools_403" &&
      error.message === "mutation denied",
  );
});

test("ToolsManager exposes load retry and closes config modals only after successful writes", () => {
  assert.match(toolsManagerSource, /const \[loadError, setLoadError\]/);
  assert.match(toolsManagerSource, /role="alert"[\s\S]*?void loadTools\(\)/);
  assert.match(
    toolsManagerSource,
    /if \(loadError && tools\.length === 0\) return loadErrorNotice/,
  );
  assert.match(
    toolsManagerSource,
    /await requestToolsMutation\(\{[\s\S]*?category-config[\s\S]*?\}\);\s*setConfigCategory\(null\)/,
  );
  assert.match(
    toolsManagerSource,
    /await requestToolsMutation\(\{[\s\S]*?tool-config[\s\S]*?\}\);\s*setConfigTool\(null\)/,
  );
  assert.match(
    toolsManagerSource,
    /catch \(error\) \{\s*setTools\([\s\S]*?!enabled[\s\S]*?toast\.error/,
  );
});
