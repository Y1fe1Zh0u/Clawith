import type { Agent, TokenResponse, User } from "../types";
import { AppError } from "./apiError.ts";
import type {
  AgentCollaborator,
  AgentMetrics,
  AgentTemplate,
  CompanyCreateResponse,
  CompanyStats,
  ControlScreenshotResponse,
  ControlStatusResponse,
  ControlUnlockResponse,
  CreatedAgent,
  FileItem,
  FileLockResponse,
  FileMutationResponse,
  FilePreview,
  FileRevision,
  GroupWorkspaceUploadResponse,
  JsonValue,
  PlatformSettings,
  ResolvedTenant,
  Tenant,
  TenantChoice,
  TenantSetupResponse,
  TenantTokenUsage,
  UploadResponse,
  WorkspaceUploadResponse,
} from "./apiContracts";
import type { OAuthTenantChoice } from "./oauthCallbackResponse";

export type ResponseParser<T> = (value: unknown) => T;

function invalid(path: string, expected: string): never {
  throw new AppError({
    message: `Invalid API response at ${path}: expected ${expected}`,
    code: "invalid_api_response",
    source: "http",
    retryable: false,
    details: { path, expected },
  });
}

function assertRecord(
  value: unknown,
  path: string,
): asserts value is Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    invalid(path, "object");
  }
}

function assertString(value: unknown, path: string): asserts value is string {
  if (typeof value !== "string") invalid(path, "string");
}

function assertNumber(value: unknown, path: string): asserts value is number {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    invalid(path, "finite number");
  }
}

function assertBoolean(value: unknown, path: string): asserts value is boolean {
  if (typeof value !== "boolean") invalid(path, "boolean");
}

function assertNullableString(
  value: unknown,
  path: string,
): asserts value is string | null {
  if (value !== null) assertString(value, path);
}

function assertOptionalString(
  value: unknown,
  path: string,
): asserts value is string | undefined {
  if (value !== undefined) assertString(value, path);
}

function assertOptionalNumber(
  value: unknown,
  path: string,
): asserts value is number | undefined {
  if (value !== undefined) assertNumber(value, path);
}

function assertOptionalBoolean(
  value: unknown,
  path: string,
): asserts value is boolean | undefined {
  if (value !== undefined) assertBoolean(value, path);
}

function assertOptionalNullableString(
  value: unknown,
  path: string,
): asserts value is string | null | undefined {
  if (value !== undefined) assertNullableString(value, path);
}

function readString(
  record: Record<string, unknown>,
  key: string,
  path: string,
) {
  const value = record[key];
  assertString(value, `${path}.${key}`);
  return value;
}

function readNumber(
  record: Record<string, unknown>,
  key: string,
  path: string,
) {
  const value = record[key];
  assertNumber(value, `${path}.${key}`);
  return value;
}

function assertStringArray(
  value: unknown,
  path: string,
): asserts value is string[] {
  if (!Array.isArray(value)) invalid(path, "string array");
  value.forEach((item, index) => assertString(item, `${path}[${index}]`));
}

function assertJsonValue(
  value: unknown,
  path: string,
): asserts value is JsonValue {
  if (
    value === null ||
    typeof value === "string" ||
    typeof value === "boolean" ||
    (typeof value === "number" && Number.isFinite(value))
  ) {
    return;
  }
  if (Array.isArray(value)) {
    value.forEach((item, index) => assertJsonValue(item, `${path}[${index}]`));
    return;
  }
  assertRecord(value, path);
  Object.entries(value).forEach(([key, item]) =>
    assertJsonValue(item, `${path}.${key}`),
  );
}

function assertRole(
  value: unknown,
  path: string,
): asserts value is User["role"] {
  if (
    value !== "platform_admin" &&
    value !== "org_admin" &&
    value !== "agent_admin" &&
    value !== "member"
  ) {
    invalid(path, "user role");
  }
}

function assertUser(value: unknown, path: string): asserts value is User {
  assertRecord(value, path);
  assertString(value.id, `${path}.id`);
  assertString(value.username, `${path}.username`);
  assertString(value.email, `${path}.email`);
  assertString(value.display_name, `${path}.display_name`);
  assertRole(value.role, `${path}.role`);
  assertBoolean(value.is_active, `${path}.is_active`);
  assertString(value.created_at, `${path}.created_at`);
  assertOptionalString(value.avatar_url, `${path}.avatar_url`);
  assertOptionalBoolean(value.is_platform_admin, `${path}.is_platform_admin`);
  assertOptionalString(value.tenant_id, `${path}.tenant_id`);
  assertOptionalString(value.title, `${path}.title`);
  assertOptionalString(value.feishu_open_id, `${path}.feishu_open_id`);
  assertOptionalBoolean(value.email_verified, `${path}.email_verified`);
}

function assertAgentStatus(
  value: unknown,
  path: string,
): asserts value is Agent["status"] {
  if (
    value !== "creating" &&
    value !== "running" &&
    value !== "idle" &&
    value !== "stopped" &&
    value !== "error"
  ) {
    invalid(path, "agent status");
  }
}

function assertStringRecord(
  value: unknown,
  path: string,
): asserts value is Record<string, string> {
  assertRecord(value, path);
  Object.entries(value).forEach(([key, item]) =>
    assertString(item, `${path}.${key}`),
  );
}

function assertAgent(value: unknown, path: string): asserts value is Agent {
  assertRecord(value, path);
  assertString(value.id, `${path}.id`);
  assertString(value.name, `${path}.name`);
  assertString(value.role_description, `${path}.role_description`);
  assertAgentStatus(value.status, `${path}.status`);
  assertString(value.creator_id, `${path}.creator_id`);
  assertStringRecord(value.autonomy_policy, `${path}.autonomy_policy`);
  assertNumber(value.tokens_used_today, `${path}.tokens_used_today`);
  assertNumber(value.tokens_used_month, `${path}.tokens_used_month`);
  assertBoolean(value.heartbeat_enabled, `${path}.heartbeat_enabled`);
  assertNumber(
    value.heartbeat_interval_minutes,
    `${path}.heartbeat_interval_minutes`,
  );
  assertString(value.heartbeat_active_hours, `${path}.heartbeat_active_hours`);
  assertString(value.created_at, `${path}.created_at`);
  [
    "avatar_url",
    "bio",
    "primary_model_id",
    "fallback_model_id",
    "last_heartbeat_at",
    "timezone",
    "openclaw_last_seen",
    "last_active_at",
  ].forEach((key) => assertOptionalString(value[key], `${path}.${key}`));
  [
    "tokens_used_total",
    "cache_read_tokens_today",
    "cache_read_tokens_month",
    "cache_read_tokens_total",
    "cache_creation_tokens_today",
    "cache_creation_tokens_month",
    "cache_creation_tokens_total",
    "max_tokens_per_day",
    "max_tokens_per_month",
    "context_window_size",
    "unread_count",
  ].forEach((key) => assertOptionalNumber(value[key], `${path}.${key}`));
  assertOptionalBoolean(value.onboarded_for_me, `${path}.onboarded_for_me`);
  if (
    value.agent_type !== undefined &&
    value.agent_type !== "native" &&
    value.agent_type !== "openclaw"
  ) {
    invalid(`${path}.agent_type`, "native or openclaw");
  }
  if (
    value.access_mode !== undefined &&
    value.access_mode !== "company" &&
    value.access_mode !== "private" &&
    value.access_mode !== "custom"
  ) {
    invalid(`${path}.access_mode`, "company, private, or custom");
  }
  if (
    value.company_access_level !== undefined &&
    value.company_access_level !== "use" &&
    value.company_access_level !== "manage"
  ) {
    invalid(`${path}.company_access_level`, "use or manage");
  }
}

function assertTenant(value: unknown, path: string): asserts value is Tenant {
  assertRecord(value, path);
  assertString(value.id, `${path}.id`);
  assertString(value.name, `${path}.name`);
  assertString(value.slug, `${path}.slug`);
  assertString(value.im_provider, `${path}.im_provider`);
  assertString(value.timezone, `${path}.timezone`);
  assertString(value.country_region, `${path}.country_region`);
  assertBoolean(value.is_active, `${path}.is_active`);
  assertBoolean(value.sso_enabled, `${path}.sso_enabled`);
  assertNullableString(value.sso_domain, `${path}.sso_domain`);
  assertBoolean(value.a2a_async_enabled, `${path}.a2a_async_enabled`);
  assertNullableString(value.default_model_id, `${path}.default_model_id`);
  assertNullableString(value.logo_url, `${path}.logo_url`);
  assertNullableString(value.created_at, `${path}.created_at`);
}

function parseWithAssertion<T>(
  value: unknown,
  assertion: (input: unknown, path: string) => asserts input is T,
): T {
  assertion(value, "response");
  return value;
}

export const parseUserResponse: ResponseParser<User> = (value) =>
  parseWithAssertion(value, assertUser);

export const parseAgentResponse: ResponseParser<Agent> = (value) =>
  parseWithAssertion(value, assertAgent);

export const parseCreatedAgentResponse: ResponseParser<CreatedAgent> = (
  value,
) => {
  assertRecord(value, "response");
  assertOptionalString(value.api_key, "response.api_key");
  assertAgent(value, "response");
  return value.api_key === undefined
    ? value
    : { ...value, api_key: value.api_key };
};

export const parseAgentListResponse: ResponseParser<Agent[]> = (value) => {
  if (!Array.isArray(value)) invalid("response", "agent array");
  value.forEach((item, index) => assertAgent(item, `response[${index}]`));
  return value;
};

export const parseTenantResponse: ResponseParser<Tenant> = (value) =>
  parseWithAssertion(value, assertTenant);

export const parseTenantChoicesResponse: ResponseParser<TenantChoice[]> = (
  value,
) => {
  if (!Array.isArray(value)) invalid("response", "tenant choice array");
  value.forEach((item, index) => {
    const path = `response[${index}]`;
    assertRecord(item, path);
    assertString(item.tenant_id, `${path}.tenant_id`);
    assertString(item.tenant_name, `${path}.tenant_name`);
    assertString(item.tenant_slug, `${path}.tenant_slug`);
    assertNullableString(item.logo_url, `${path}.logo_url`);
  });
  return value;
};

export const parseTenantSetupResponse: ResponseParser<TenantSetupResponse> = (
  value,
) => {
  assertRecord(value, "response");
  assertTenant(value.tenant, "response.tenant");
  assertNullableString(value.access_token, "response.access_token");
  if (value.role !== undefined) assertRole(value.role, "response.role");
  return {
    tenant: value.tenant,
    access_token: value.access_token,
    ...(value.role === undefined ? {} : { role: value.role }),
  };
};

export const parseResolvedTenantResponse: ResponseParser<ResolvedTenant> = (
  value,
) => {
  assertRecord(value, "response");
  assertString(value.id, "response.id");
  assertString(value.name, "response.name");
  assertString(value.slug, "response.slug");
  assertBoolean(value.sso_enabled, "response.sso_enabled");
  assertNullableString(value.sso_domain, "response.sso_domain");
  assertBoolean(value.is_active, "response.is_active");
  return {
    id: value.id,
    name: value.name,
    slug: value.slug,
    sso_enabled: value.sso_enabled,
    sso_domain: value.sso_domain,
    is_active: value.is_active,
  };
};

function assertTokenUsageBucket(
  value: unknown,
  path: string,
): asserts value is TenantTokenUsage["today"] {
  assertRecord(value, path);
  assertNumber(value.total_tokens, `${path}.total_tokens`);
  assertNumber(value.cache_read_tokens, `${path}.cache_read_tokens`);
  assertNumber(value.cache_creation_tokens, `${path}.cache_creation_tokens`);
  assertNumber(value.cache_hit_rate, `${path}.cache_hit_rate`);
}

export const parseTenantTokenUsageResponse: ResponseParser<TenantTokenUsage> = (
  value,
) => {
  assertRecord(value, "response");
  assertTokenUsageBucket(value.today, "response.today");
  assertTokenUsageBucket(value.month, "response.month");
  assertTokenUsageBucket(value.total, "response.total");
  return { today: value.today, month: value.month, total: value.total };
};

function assertCompanyStats(
  value: unknown,
  path: string,
): asserts value is CompanyStats {
  assertRecord(value, path);
  ["id", "name", "slug"].forEach((key) =>
    assertString(value[key], `${path}.${key}`),
  );
  assertBoolean(value.is_active, `${path}.is_active`);
  assertBoolean(value.sso_enabled, `${path}.sso_enabled`);
  assertNullableString(value.sso_domain, `${path}.sso_domain`);
  assertNullableString(value.created_at, `${path}.created_at`);
  [
    "user_count",
    "agent_count",
    "agent_running_count",
    "total_tokens",
    "cache_read_tokens_total",
  ].forEach((key) => assertNumber(value[key], `${path}.${key}`));
  assertNullableString(value.org_admin_email, `${path}.org_admin_email`);
}

export const parseCompanyStatsListResponse: ResponseParser<CompanyStats[]> = (
  value,
) => {
  if (!Array.isArray(value)) invalid("response", "company array");
  value.forEach((item, index) =>
    assertCompanyStats(item, `response[${index}]`),
  );
  return value;
};

export const parseCompanyStatsResponse: ResponseParser<CompanyStats> = (
  value,
) => parseWithAssertion(value, assertCompanyStats);

export const parseCompanyCreateResponse: ResponseParser<
  CompanyCreateResponse
> = (value) => {
  assertRecord(value, "response");
  assertCompanyStats(value.company, "response.company");
  assertString(value.admin_invitation_code, "response.admin_invitation_code");
  return {
    company: value.company,
    admin_invitation_code: value.admin_invitation_code,
  };
};

export const parsePlatformSettingsResponse: ResponseParser<PlatformSettings> = (
  value,
) => {
  assertRecord(value, "response");
  assertBoolean(
    value.allow_self_create_company,
    "response.allow_self_create_company",
  );
  assertBoolean(
    value.invitation_code_enabled,
    "response.invitation_code_enabled",
  );
  assertBoolean(
    value.sso_custom_domain_redirect_enabled,
    "response.sso_custom_domain_redirect_enabled",
  );
  return {
    allow_self_create_company: value.allow_self_create_company,
    invitation_code_enabled: value.invitation_code_enabled,
    sso_custom_domain_redirect_enabled:
      value.sso_custom_domain_redirect_enabled,
  };
};

export const parseAgentTemplatesResponse: ResponseParser<AgentTemplate[]> = (
  value,
) => {
  if (!Array.isArray(value)) invalid("response", "agent template array");
  value.forEach((item, index) => {
    const path = `response[${index}]`;
    assertRecord(item, path);
    ["id", "name", "description", "icon", "category"].forEach((key) =>
      assertString(item[key], `${path}.${key}`),
    );
    assertBoolean(item.is_builtin, `${path}.is_builtin`);
    if (item.capability_bullets !== undefined) {
      assertStringArray(item.capability_bullets, `${path}.capability_bullets`);
    }
  });
  return value;
};

export const parseAgentCollaboratorsResponse: ResponseParser<
  AgentCollaborator[]
> = (value) => {
  if (!Array.isArray(value)) invalid("response", "collaborator array");
  value.forEach((item, index) => {
    const path = `response[${index}]`;
    assertRecord(item, path);
    ["id", "name", "role", "status"].forEach((key) =>
      assertString(item[key], `${path}.${key}`),
    );
  });
  return value;
};

export const parseAgentMetricsResponse: ResponseParser<AgentMetrics> = (
  value,
) => {
  assertRecord(value, "response");
  ["agent_id", "agent_name", "status", "container"].forEach((key) =>
    assertString(value[key], `response.${key}`),
  );
  const tokens = value.tokens;
  assertRecord(tokens, "response.tokens");
  [
    "used_today",
    "used_month",
    "used_total",
    "cache_read_today",
    "cache_read_month",
    "cache_read_total",
    "cache_creation_today",
    "cache_creation_month",
    "cache_creation_total",
  ].forEach((key) => assertNumber(tokens[key], `response.tokens.${key}`));
  const tasks = value.tasks;
  assertRecord(tasks, "response.tasks");
  ["total", "done", "pending", "completion_rate"].forEach((key) =>
    assertNumber(tasks[key], `response.tasks.${key}`),
  );
  const approvals = value.approvals;
  assertRecord(approvals, "response.approvals");
  assertNumber(approvals.total, "response.approvals.total");
  assertNumber(approvals.pending, "response.approvals.pending");
  const activity = value.activity;
  assertRecord(activity, "response.activity");
  assertNumber(activity.actions_last_24h, "response.activity.actions_last_24h");
  return {
    agent_id: readString(value, "agent_id", "response"),
    agent_name: readString(value, "agent_name", "response"),
    status: readString(value, "status", "response"),
    container: readString(value, "container", "response"),
    tokens: {
      used_today: readNumber(tokens, "used_today", "response.tokens"),
      used_month: readNumber(tokens, "used_month", "response.tokens"),
      used_total: readNumber(tokens, "used_total", "response.tokens"),
      cache_read_today: readNumber(
        tokens,
        "cache_read_today",
        "response.tokens",
      ),
      cache_read_month: readNumber(
        tokens,
        "cache_read_month",
        "response.tokens",
      ),
      cache_read_total: readNumber(
        tokens,
        "cache_read_total",
        "response.tokens",
      ),
      cache_creation_today: readNumber(
        tokens,
        "cache_creation_today",
        "response.tokens",
      ),
      cache_creation_month: readNumber(
        tokens,
        "cache_creation_month",
        "response.tokens",
      ),
      cache_creation_total: readNumber(
        tokens,
        "cache_creation_total",
        "response.tokens",
      ),
    },
    tasks: {
      total: readNumber(tasks, "total", "response.tasks"),
      done: readNumber(tasks, "done", "response.tasks"),
      pending: readNumber(tasks, "pending", "response.tasks"),
      completion_rate: readNumber(tasks, "completion_rate", "response.tasks"),
    },
    approvals: {
      total: readNumber(approvals, "total", "response.approvals"),
      pending: readNumber(approvals, "pending", "response.approvals"),
    },
    activity: {
      actions_last_24h: readNumber(
        activity,
        "actions_last_24h",
        "response.activity",
      ),
    },
  };
};

export const parseFileItemsResponse: ResponseParser<FileItem[]> = (value) => {
  if (!Array.isArray(value)) invalid("response", "file item array");
  value.forEach((item, index) => {
    const path = `response[${index}]`;
    assertRecord(item, path);
    assertString(item.name, `${path}.name`);
    assertString(item.path, `${path}.path`);
    assertBoolean(item.is_dir, `${path}.is_dir`);
    assertOptionalNumber(item.size, `${path}.size`);
  });
  return value;
};

export const parseFilePreviewResponse: ResponseParser<FilePreview> = (
  value,
) => {
  assertRecord(value, "response");
  ["path", "name", "content", "type", "kind", "content_hash"].forEach((key) =>
    assertOptionalString(value[key], `response.${key}`),
  );
  if (value.sheets !== undefined) {
    if (!Array.isArray(value.sheets)) invalid("response.sheets", "sheet array");
    value.sheets.forEach((sheet, sheetIndex) => {
      const path = `response.sheets[${sheetIndex}]`;
      assertRecord(sheet, path);
      assertOptionalString(sheet.name, `${path}.name`);
      if (!Array.isArray(sheet.rows)) invalid(`${path}.rows`, "row array");
      sheet.rows.forEach((row, rowIndex) =>
        assertStringArray(row, `${path}.rows[${rowIndex}]`),
      );
    });
  }
  return value;
};

export const parseFileLockResponse: ResponseParser<FileLockResponse> = (
  value,
) => {
  assertRecord(value, "response");
  assertString(value.status, "response.status");
  assertOptionalString(value.path, "response.path");
  assertOptionalNullableString(value.locked_by, "response.locked_by");
  return {
    status: value.status,
    ...(value.path === undefined ? {} : { path: value.path }),
    ...(value.locked_by === undefined ? {} : { locked_by: value.locked_by }),
  };
};

export const parseFileMutationResponse: ResponseParser<FileMutationResponse> = (
  value,
) => {
  assertRecord(value, "response");
  assertString(value.status, "response.status");
  assertOptionalString(value.path, "response.path");
  assertOptionalString(value.revision_id, "response.revision_id");
  return {
    status: value.status,
    ...(value.path === undefined ? {} : { path: value.path }),
    ...(value.revision_id === undefined
      ? {}
      : { revision_id: value.revision_id }),
  };
};

export const parseFileRevisionsResponse: ResponseParser<FileRevision[]> = (
  value,
) => {
  if (!Array.isArray(value)) invalid("response", "file revision array");
  value.forEach((item, index) => {
    const path = `response[${index}]`;
    assertRecord(item, path);
    assertString(item.id, `${path}.id`);
    assertString(item.path, `${path}.path`);
    assertString(item.created_at, `${path}.created_at`);
    assertOptionalNullableString(item.created_by, `${path}.created_by`);
    assertOptionalNumber(item.size, `${path}.size`);
  });
  return value;
};

export const parseUploadResponse: ResponseParser<UploadResponse> = (value) => {
  assertRecord(value, "response");
  assertString(value.filename, "response.filename");
  assertString(value.extracted_text, "response.extracted_text");
  assertString(value.workspace_path, "response.workspace_path");
  assertString(value.image_data_url, "response.image_data_url");
  assertOptionalString(value.path, "response.path");
  assertOptionalNumber(value.size, "response.size");
  assertOptionalString(value.version_token, "response.version_token");
  assertOptionalNullableString(value.modified_at, "response.modified_at");
  assertOptionalNullableString(value.revision_id, "response.revision_id");
  assertOptionalString(value.saved_filename, "response.saved_filename");
  return {
    filename: value.filename,
    extracted_text: value.extracted_text,
    workspace_path: value.workspace_path,
    image_data_url: value.image_data_url,
    ...(value.path === undefined ? {} : { path: value.path }),
    ...(value.size === undefined ? {} : { size: value.size }),
    ...(value.version_token === undefined
      ? {}
      : { version_token: value.version_token }),
    ...(value.modified_at === undefined
      ? {}
      : { modified_at: value.modified_at }),
    ...(value.revision_id === undefined
      ? {}
      : { revision_id: value.revision_id }),
    ...(value.saved_filename === undefined
      ? {}
      : { saved_filename: value.saved_filename }),
  };
};

export const parseWorkspaceUploadResponse: ResponseParser<
  WorkspaceUploadResponse
> = (value) => {
  assertRecord(value, "response");
  assertString(value.status, "response.status");
  assertString(value.path, "response.path");
  assertString(value.url, "response.url");
  assertString(value.filename, "response.filename");
  assertNumber(value.size, "response.size");
  assertNullableString(
    value.extracted_text_path,
    "response.extracted_text_path",
  );
  return {
    status: value.status,
    path: value.path,
    url: value.url,
    filename: value.filename,
    size: value.size,
    extracted_text_path: value.extracted_text_path,
  };
};

export const parseGroupWorkspaceUploadResponse: ResponseParser<
  GroupWorkspaceUploadResponse
> = (value) => {
  assertRecord(value, "response");
  assertString(value.path, "response.path");
  assertNumber(value.size, "response.size");
  assertString(value.version_token, "response.version_token");
  assertOptionalNullableString(value.modified_at, "response.modified_at");
  assertOptionalNullableString(value.revision_id, "response.revision_id");
  return {
    path: value.path,
    size: value.size,
    version_token: value.version_token,
    ...(value.modified_at === undefined
      ? {}
      : { modified_at: value.modified_at }),
    ...(value.revision_id === undefined
      ? {}
      : { revision_id: value.revision_id }),
  };
};

export const parseControlStatusResponse: ResponseParser<
  ControlStatusResponse
> = (value) => {
  assertRecord(value, "response");
  assertString(value.status, "response.status");
  assertOptionalString(value.detail, "response.detail");
  assertOptionalString(value.message, "response.message");
  assertOptionalBoolean(value.success, "response.success");
  return {
    status: value.status,
    ...(value.detail === undefined ? {} : { detail: value.detail }),
    ...(value.message === undefined ? {} : { message: value.message }),
    ...(value.success === undefined ? {} : { success: value.success }),
  };
};

export const parseControlScreenshotResponse: ResponseParser<
  ControlScreenshotResponse
> = (value) => {
  parseControlStatusResponse(value);
  assertRecord(value, "response");
  assertOptionalString(value.screenshot, "response.screenshot");
  if (value.screen_size !== undefined && value.screen_size !== null) {
    assertRecord(value.screen_size, "response.screen_size");
    assertNumber(value.screen_size.width, "response.screen_size.width");
    assertNumber(value.screen_size.height, "response.screen_size.height");
  }
  return {
    ...parseControlStatusResponse(value),
    ...(value.screenshot === undefined ? {} : { screenshot: value.screenshot }),
    ...(value.screen_size === undefined || value.screen_size === null
      ? {}
      : {
          screen_size: {
            width: readNumber(
              value.screen_size,
              "width",
              "response.screen_size",
            ),
            height: readNumber(
              value.screen_size,
              "height",
              "response.screen_size",
            ),
          },
        }),
  };
};

export const parseControlUnlockResponse: ResponseParser<
  ControlUnlockResponse
> = (value) => {
  parseControlStatusResponse(value);
  assertRecord(value, "response");
  assertOptionalBoolean(value.cookies_exported, "response.cookies_exported");
  assertOptionalNumber(value.cookie_count, "response.cookie_count");
  if (value.cookies !== undefined) {
    if (!Array.isArray(value.cookies))
      invalid("response.cookies", "JSON array");
    value.cookies.forEach((cookie, index) =>
      assertJsonValue(cookie, `response.cookies[${index}]`),
    );
  }
  return {
    ...parseControlStatusResponse(value),
    ...(value.cookies_exported === undefined
      ? {}
      : { cookies_exported: value.cookies_exported }),
    ...(value.cookie_count === undefined
      ? {}
      : { cookie_count: value.cookie_count }),
    ...(value.cookies === undefined ? {} : { cookies: value.cookies }),
  };
};

export const parseTokenResponse: ResponseParser<TokenResponse> = (value) => {
  assertRecord(value, "response");
  assertString(value.access_token, "response.access_token");
  assertString(value.token_type, "response.token_type");
  assertUser(value.user, "response.user");
  assertOptionalBoolean(
    value.needs_company_setup,
    "response.needs_company_setup",
  );
  return {
    access_token: value.access_token,
    token_type: value.token_type,
    user: value.user,
    ...(value.needs_company_setup === undefined
      ? {}
      : { needs_company_setup: value.needs_company_setup }),
  };
};

export const parseLoginResponse: ResponseParser<
  | TokenResponse
  | {
      requires_tenant_selection: boolean;
      login_identifier: string;
      tenants: OAuthTenantChoice[];
    }
> = (value) => {
  assertRecord(value, "response");
  if (value.requires_tenant_selection === true) {
    assertString(value.login_identifier, "response.login_identifier");
    if (!Array.isArray(value.tenants))
      invalid("response.tenants", "tenant array");
    value.tenants.forEach((tenant, index) => {
      const path = `response.tenants[${index}]`;
      assertRecord(tenant, path);
      assertString(tenant.tenant_id, `${path}.tenant_id`);
      assertString(tenant.tenant_name, `${path}.tenant_name`);
      assertString(tenant.tenant_slug, `${path}.tenant_slug`);
      assertNullableString(tenant.logo_url, `${path}.logo_url`);
    });
    return {
      requires_tenant_selection: true,
      login_identifier: value.login_identifier,
      tenants: value.tenants,
    };
  }
  return parseTokenResponse(value);
};
