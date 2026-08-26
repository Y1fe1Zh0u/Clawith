/** API service layer */

import type { Agent, TokenResponse, User, Task } from "../types";
import type { OAuthTenantChoice } from "./oauthCallbackResponse";
import type {
  ActivityItem,
  AgentCollaborator,
  AgentCreateRequest,
  AgentMetrics,
  AgentTemplate,
  ChannelConfig,
  ChannelConfigRequest,
  ClawhubSkill,
  CompanyCreateResponse,
  CompanyStats,
  ControlScreenshotResponse,
  ControlStatusResponse,
  ControlUnlockResponse,
  CreatedAgent,
  Credential,
  CredentialMutationRequest,
  FileItem,
  FileLockResponse,
  FileMutationResponse,
  FilePreview,
  FileRevision,
  GatewayMessage,
  InboxMessage,
  JsonValue,
  LlmModel,
  OnboardingStatus,
  PersonalAssistantResponse,
  PlatformSettings,
  ResolvedTenant,
  Schedule,
  ScheduleCreateRequest,
  ScheduleHistoryItem,
  ScheduleRunResponse,
  ScheduleUpdateRequest,
  Skill,
  SkillImportResult,
  SkillMutationRequest,
  SkillUrlPreview,
  TaskCreateRequest,
  TaskTriggerResponse,
  Tenant,
  TenantChoice,
  TenantSetupResponse,
  TenantTokenUsage,
  TenantUpdate,
  Trigger,
  TriggerUpdateRequest,
  UploadResponse,
  WorkspaceUploadResponse,
} from "./apiContracts";
import {
  AppError,
  parseHttpError,
  parseHttpErrorResponse,
  normalizeUnknownError,
} from "./apiError";
import {
  parseAgentCollaboratorsResponse,
  parseAgentListResponse,
  parseAgentMetricsResponse,
  parseAgentResponse,
  parseAgentTemplatesResponse,
  parseCompanyCreateResponse,
  parseCompanyStatsListResponse,
  parseCompanyStatsResponse,
  parseControlScreenshotResponse,
  parseControlStatusResponse,
  parseControlUnlockResponse,
  parseCreatedAgentResponse,
  parseFileItemsResponse,
  parseFileLockResponse,
  parseFileMutationResponse,
  parseFilePreviewResponse,
  parseFileRevisionsResponse,
  parseLoginResponse,
  parsePlatformSettingsResponse,
  parseResolvedTenantResponse,
  parseTenantChoicesResponse,
  parseTenantResponse,
  parseTenantSetupResponse,
  parseTenantTokenUsageResponse,
  parseUploadResponse,
  parseUserResponse,
  parseWorkspaceUploadResponse,
  type ResponseParser,
} from "./apiResponseParsers";

export { ApiError, AppError } from "./apiError";
export type { ApiErrorContext, AppErrorContext, ErrorSource } from "./apiError";

const API_BASE = "/api";

async function request<T>(
  url: string,
  options: RequestInit = {},
  parser?: ResponseParser<T>,
): Promise<T> {
  const token = localStorage.getItem("token");
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  let res: Response;
  try {
    res = await fetch(`${API_BASE}${url}`, { ...options, headers });
  } catch (error) {
    throw normalizeUnknownError(error, {
      code: "network_error",
      source: "http",
      retryable: true,
    });
  }

  if (!res.ok) {
    const apiError = await parseHttpErrorResponse(res);
    // Auto-logout on expired/invalid token (but not on auth endpoints — let them show errors)
    const isAuthEndpoint =
      url.startsWith("/auth/login") ||
      url.startsWith("/auth/register") ||
      url.startsWith("/auth/verify-email") ||
      url.startsWith("/auth/resend-verification") ||
      url.startsWith("/auth/forgot-password") ||
      url.startsWith("/auth/reset-password");
    if (res.status === 401 && !isAuthEndpoint) {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      window.location.href = "/login";
      throw apiError;
    }
    throw apiError;
  }

  if (res.status === 204) {
    throw new AppError({
      message: "API returned no content for a JSON response",
      code: "invalid_api_response",
      source: "http",
      retryable: false,
    });
  }
  if (parser) {
    const value: unknown = await res.json();
    return parser(value);
  }
  return res.json();
}

async function requestVoid(
  url: string,
  options: RequestInit = {},
): Promise<void> {
  await requestRaw(url, options, true);
}

async function requestRaw(
  url: string,
  options: RequestInit,
  expectNoContent: boolean,
): Promise<unknown> {
  const token = localStorage.getItem("token");
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${url}`, { ...options, headers });
  } catch (error) {
    throw normalizeUnknownError(error, {
      code: "network_error",
      source: "http",
      retryable: true,
    });
  }
  if (!res.ok) throw await parseHttpErrorResponse(res);
  if (expectNoContent) {
    if (res.status !== 204) {
      throw new AppError({
        message: "API returned content where no content was expected",
        code: "invalid_api_response",
        source: "http",
        retryable: false,
      });
    }
    return undefined;
  }
  return res.json();
}

/** Legacy/Internal generic fetcher */
export const fetchJson = request;

async function uploadFile(
  url: string,
  file: File,
  extraFields?: Record<string, string>,
): Promise<WorkspaceUploadResponse> {
  const token = localStorage.getItem("token");
  const formData = new FormData();
  formData.append("file", file);
  if (extraFields) {
    for (const [k, v] of Object.entries(extraFields)) {
      formData.append(k, v);
    }
  }
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${url}`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    });
  } catch (error) {
    throw normalizeUnknownError(error, {
      code: "network_error",
      source: "http",
      retryable: true,
    });
  }
  if (!res.ok) {
    throw await parseHttpErrorResponse(res);
  }
  const value: unknown = await res.json();
  return parseWorkspaceUploadResponse(value);
}

// Upload with progress tracking via XMLHttpRequest.
// Returns { promise, abort } — call abort() to cancel the upload.
// Progress callback: 0-100 = upload phase, 101 = processing phase (server is parsing the file).
export function uploadFileWithProgress(
  url: "/chat/upload",
  file: File,
  onProgress?: (percent: number) => void,
  extraFields?: Record<string, string>,
  timeoutMs?: number,
): { promise: Promise<UploadResponse>; abort: () => void };
export function uploadFileWithProgress(
  url: string,
  file: File,
  onProgress?: (percent: number) => void,
  extraFields?: Record<string, string>,
  timeoutMs?: number,
): { promise: Promise<WorkspaceUploadResponse>; abort: () => void };
export function uploadFileWithProgress<T>(
  url: string,
  file: File,
  onProgress: ((percent: number) => void) | undefined,
  extraFields: Record<string, string> | undefined,
  timeoutMs: number | undefined,
  parser: ResponseParser<T>,
): { promise: Promise<T>; abort: () => void };
export function uploadFileWithProgress(
  url: string,
  file: File,
  onProgress?: (percent: number) => void,
  extraFields?: Record<string, string>,
  timeoutMs?: number,
  parser?: ResponseParser<unknown>,
): { promise: Promise<unknown>; abort: () => void } {
  const xhr = new XMLHttpRequest();
  const promise = new Promise<unknown>((resolve, reject) => {
    const token = localStorage.getItem("token");
    const formData = new FormData();
    formData.append("file", file);
    if (extraFields) {
      for (const [k, v] of Object.entries(extraFields)) {
        formData.append(k, v);
      }
    }
    xhr.open("POST", `${API_BASE}${url}`);
    if (token) xhr.setRequestHeader("Authorization", `Bearer ${token}`);

    // Upload phase: 0-100%
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && onProgress) {
        onProgress(Math.round((e.loaded / e.total) * 100));
      }
    };
    // Upload bytes finished → enter processing phase
    xhr.upload.onload = () => {
      if (onProgress) onProgress(101); // 101 = "processing" sentinel
    };

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const value: unknown = JSON.parse(xhr.responseText);
          const responseParser =
            parser ??
            (url === "/chat/upload"
              ? parseUploadResponse
              : parseWorkspaceUploadResponse);
          resolve(responseParser(value));
        } catch {
          reject(
            new AppError({
              message: "Upload returned an invalid JSON response",
              code: "invalid_upload_response",
              source: "http",
              retryable: false,
            }),
          );
        }
      } else {
        reject(
          parseHttpError({
            status: xhr.status,
            statusText: xhr.statusText,
            bodyText: xhr.responseText,
            traceId: xhr.getResponseHeader("X-Trace-Id"),
          }),
        );
      }
    };
    xhr.onerror = () =>
      reject(
        new AppError({
          message: "Network error",
          code: "network_error",
          source: "http",
          retryable: true,
        }),
      );
    xhr.ontimeout = () =>
      reject(
        new AppError({
          message: "Upload timed out",
          code: "upload_timeout",
          source: "http",
          retryable: true,
        }),
      );
    xhr.onabort = () =>
      reject(
        new AppError({
          message: "Upload cancelled",
          code: "upload_cancelled",
          source: "http",
          retryable: false,
        }),
      );
    xhr.timeout = timeoutMs ?? 120_000;
    xhr.send(formData);
  });
  return { promise, abort: () => xhr.abort() };
}

// ─── Auth ─────────────────────────────────────────────
export const authApi = {
  register: (data: {
    username?: string;
    email: string;
    password: string;
    display_name: string;
    invitation_code?: string;
    provider?: string;
    provider_code?: string;
  }) =>
    request<{
      user_id: string;
      email: string;
      access_token: string;
      message: string;
      user?: User;
      needs_company_setup: boolean;
    }>("/auth/register", { method: "POST", body: JSON.stringify(data) }),

  login: (data: {
    login_identifier: string;
    password: string;
    tenant_id?: string;
  }) =>
    request<
      | TokenResponse
      | {
          requires_tenant_selection: boolean;
          login_identifier: string;
          tenants: OAuthTenantChoice[];
        }
    >(
      "/auth/login",
      { method: "POST", body: JSON.stringify(data) },
      parseLoginResponse,
    ),

  forgotPassword: (data: { email: string }) =>
    request<{ ok: boolean; message: string }>("/auth/forgot-password", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  resetPassword: (data: { token: string; new_password: string }) =>
    request<{ ok: boolean }>("/auth/reset-password", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  emailHint: (username: string) =>
    request<{ hint: string }>(
      `/auth/email-hint?username=${encodeURIComponent(username)}`,
    ),

  me: () => request<User>("/auth/me", {}, parseUserResponse),

  updateMe: (data: Partial<User>) =>
    request<User>(
      "/auth/me",
      { method: "PATCH", body: JSON.stringify(data) },
      parseUserResponse,
    ),

  verifyEmail: (token: string) =>
    request<{
      ok: boolean;
      message: string;
      access_token: string;
      user: User;
      needs_company_setup: boolean;
    }>("/auth/verify-email", {
      method: "POST",
      body: JSON.stringify({ token }),
    }),

  resendVerification: (email: string) =>
    request<{ ok: boolean; message: string }>("/auth/resend-verification", {
      method: "POST",
      body: JSON.stringify({ email }),
    }),

  getMyTenants: () =>
    request<TenantChoice[]>("/auth/my-tenants", {}, parseTenantChoicesResponse),

  switchTenant: (tenantId: string) =>
    request<{ access_token: string; redirect_url?: string; message?: string }>(
      "/auth/switch-tenant",
      { method: "POST", body: JSON.stringify({ tenant_id: tenantId }) },
    ),
};

// ─── Tenants ──────────────────────────────────────────
export const tenantApi = {
  selfCreate: (data: { name: string }) =>
    request<TenantSetupResponse>(
      "/tenants/self-create",
      { method: "POST", body: JSON.stringify(data) },
      parseTenantSetupResponse,
    ),

  join: (invitationCode: string) =>
    request<TenantSetupResponse>(
      "/tenants/join",
      {
        method: "POST",
        body: JSON.stringify({ invitation_code: invitationCode }),
      },
      parseTenantSetupResponse,
    ),

  registrationConfig: () =>
    request<{ allow_self_create_company: boolean }>(
      "/tenants/registration-config",
    ),

  resolveByDomain: (domain: string) =>
    request<ResolvedTenant>(
      `/tenants/resolve-by-domain?domain=${encodeURIComponent(domain)}`,
      {},
      parseResolvedTenantResponse,
    ),

  me: () => request<Tenant>("/tenants/me", {}, parseTenantResponse),

  tokenUsage: () =>
    request<TenantTokenUsage>(
      "/tenants/me/token-usage",
      {},
      parseTenantTokenUsageResponse,
    ),
};

export const onboardingApi = {
  status: () => request<OnboardingStatus>("/onboarding/status"),

  start: (entryMode: "create" | "join") =>
    request<OnboardingStatus>("/onboarding/start", {
      method: "POST",
      body: JSON.stringify({ entry_mode: entryMode }),
    }),

  createPersonalAssistant: (data: {
    name: string;
    personality: string;
    work_style: string;
    boundaries?: string;
  }) =>
    request<PersonalAssistantResponse>("/onboarding/personal-assistant", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  complete: () =>
    request<OnboardingStatus>("/onboarding/complete", { method: "POST" }),
};

export const adminApi = {
  listCompanies: () =>
    request<CompanyStats[]>(
      "/admin/companies",
      {},
      parseCompanyStatsListResponse,
    ),

  createCompany: (data: { name: string }) =>
    request<CompanyCreateResponse>(
      "/admin/companies",
      { method: "POST", body: JSON.stringify(data) },
      parseCompanyCreateResponse,
    ),

  updateCompany: (id: string, data: TenantUpdate) =>
    request<Tenant>(
      `/tenants/${id}`,
      { method: "PUT", body: JSON.stringify(data) },
      parseTenantResponse,
    ),

  toggleCompany: (id: string) =>
    request<CompanyStats>(
      `/admin/companies/${id}/toggle`,
      { method: "PUT" },
      parseCompanyStatsResponse,
    ),

  getPlatformSettings: () =>
    request<PlatformSettings>(
      "/admin/platform-settings",
      {},
      parsePlatformSettingsResponse,
    ),

  updatePlatformSettings: (data: Partial<PlatformSettings>) =>
    request<PlatformSettings>(
      "/admin/platform-settings",
      { method: "PUT", body: JSON.stringify(data) },
      parsePlatformSettingsResponse,
    ),
};

// ─── Agents ───────────────────────────────────────────
export const agentApi = {
  list: (tenantId?: string) =>
    request<Agent[]>(
      `/agents/${tenantId ? `?tenant_id=${tenantId}` : ""}`,
      {},
      parseAgentListResponse,
    ),

  get: (id: string) => request<Agent>(`/agents/${id}`, {}, parseAgentResponse),

  create: (data: AgentCreateRequest) =>
    request<CreatedAgent>(
      "/agents/",
      { method: "POST", body: JSON.stringify(data) },
      parseCreatedAgentResponse,
    ),

  update: (id: string, data: Partial<Agent>) =>
    request<Agent>(
      `/agents/${id}`,
      { method: "PATCH", body: JSON.stringify(data) },
      parseAgentResponse,
    ),

  delete: (id: string) => requestVoid(`/agents/${id}`, { method: "DELETE" }),

  start: (id: string) =>
    request<Agent>(
      `/agents/${id}/start`,
      { method: "POST" },
      parseAgentResponse,
    ),

  stop: (id: string) =>
    request<Agent>(
      `/agents/${id}/stop`,
      { method: "POST" },
      parseAgentResponse,
    ),

  metrics: (id: string) =>
    request<AgentMetrics>(
      `/agents/${id}/metrics`,
      {},
      parseAgentMetricsResponse,
    ),

  collaborators: (id: string) =>
    request<AgentCollaborator[]>(
      `/agents/${id}/collaborators`,
      {},
      parseAgentCollaboratorsResponse,
    ),

  templates: () =>
    request<AgentTemplate[]>(
      "/agents/templates",
      {},
      parseAgentTemplatesResponse,
    ),

  // OpenClaw gateway
  generateApiKey: (id: string) =>
    request<{ api_key: string; message: string }>(`/agents/${id}/api-key`, {
      method: "POST",
    }),

  gatewayMessages: (id: string) =>
    request<GatewayMessage[]>(`/agents/${id}/gateway-messages`),
};

// ─── Tasks ────────────────────────────────────────────
export const taskApi = {
  list: (agentId: string, status?: string, type?: string) => {
    const params = new URLSearchParams();
    if (status) params.set("status_filter", status);
    if (type) params.set("type_filter", type);
    return request<Task[]>(`/agents/${agentId}/tasks/?${params}`);
  },

  create: (agentId: string, data: TaskCreateRequest) =>
    request<Task>(`/agents/${agentId}/tasks/`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  update: (agentId: string, taskId: string, data: Partial<Task>) =>
    request<Task>(`/agents/${agentId}/tasks/${taskId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  getLogs: (agentId: string, taskId: string) =>
    request<
      { id: string; task_id: string; content: string; created_at: string }[]
    >(`/agents/${agentId}/tasks/${taskId}/logs`),

  trigger: (agentId: string, taskId: string) =>
    request<TaskTriggerResponse>(`/agents/${agentId}/tasks/${taskId}/trigger`, {
      method: "POST",
    }),
};

// ─── Files ────────────────────────────────────────────
export const fileApi = {
  list: (agentId: string, path: string = "") =>
    request<FileItem[]>(
      `/agents/${agentId}/files/?path=${encodeURIComponent(path)}`,
      {},
      parseFileItemsResponse,
    ),

  read: (agentId: string, path: string) =>
    request<{ path: string; content: string }>(
      `/agents/${agentId}/files/content?path=${encodeURIComponent(path)}`,
    ),

  write: (agentId: string, path: string, content: string) =>
    request(
      `/agents/${agentId}/files/content?path=${encodeURIComponent(path)}`,
      {
        method: "PUT",
        body: JSON.stringify({ content }),
      },
    ),

  autosave: (
    agentId: string,
    path: string,
    content: string,
    sessionId?: string | null,
  ) =>
    request<{ status: string; path: string; revision_id?: string }>(
      `/agents/${agentId}/files/content?path=${encodeURIComponent(path)}`,
      {
        method: "PUT",
        body: JSON.stringify({
          content,
          autosave: true,
          session_id: sessionId || undefined,
        }),
      },
    ),

  delete: (agentId: string, path: string) =>
    request(
      `/agents/${agentId}/files/content?path=${encodeURIComponent(path)}`,
      {
        method: "DELETE",
      },
    ),

  preview: (agentId: string, path: string) =>
    request<FilePreview>(
      `/agents/${agentId}/files/preview?path=${encodeURIComponent(path)}`,
      {},
      parseFilePreviewResponse,
    ),

  lock: (agentId: string, path: string, sessionId?: string | null) =>
    request<FileLockResponse>(
      `/agents/${agentId}/files/locks`,
      {
        method: "POST",
        body: JSON.stringify({ path, session_id: sessionId || undefined }),
      },
      parseFileLockResponse,
    ),

  unlock: (agentId: string, path: string) =>
    request<FileLockResponse>(
      `/agents/${agentId}/files/locks?path=${encodeURIComponent(path)}`,
      {
        method: "DELETE",
      },
      parseFileLockResponse,
    ),

  revisions: (agentId: string, path: string) =>
    request<FileRevision[]>(
      `/agents/${agentId}/files/revisions?path=${encodeURIComponent(path)}`,
      {},
      parseFileRevisionsResponse,
    ),

  restoreRevision: (agentId: string, revisionId: string) =>
    request<FileMutationResponse>(
      `/agents/${agentId}/files/restore`,
      { method: "POST", body: JSON.stringify({ revision_id: revisionId }) },
      parseFileMutationResponse,
    ),

  upload: (
    agentId: string,
    file: File,
    path: string = "workspace/knowledge_base",
    onProgress?: (pct: number) => void,
  ) =>
    onProgress
      ? uploadFileWithProgress(
          `/agents/${agentId}/files/upload?path=${encodeURIComponent(path)}`,
          file,
          onProgress,
        ).promise
      : uploadFile(
          `/agents/${agentId}/files/upload?path=${encodeURIComponent(path)}`,
          file,
        ),

  importSkill: (agentId: string, skillId: string) =>
    request<FileMutationResponse>(
      `/agents/${agentId}/files/import-skill`,
      { method: "POST", body: JSON.stringify({ skill_id: skillId }) },
      parseFileMutationResponse,
    ),

  downloadUrl: (
    agentId: string,
    path: string,
    options?: { inline?: boolean },
  ) => {
    const token = localStorage.getItem("token");
    const params = new URLSearchParams({ path, token: token || "" });
    if (options?.inline) params.set("inline", "1");
    return `${API_BASE}/agents/${agentId}/files/download?${params.toString()}`;
  },
};

export type FocusApiItem = {
  id: string;
  agent_id: string;
  key: string;
  title?: string | null;
  description: string;
  status: "in_progress" | "completed";
  kind: "normal" | "system";
  source: string;
  metadata?: { [key: string]: JsonValue };
  sort_order: number;
  completed_at?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};

// ─── Focus ───────────────────────────────────────────
export const focusApi = {
  list: (agentId: string, includeCompleted = true) =>
    request<FocusApiItem[]>(
      `/agents/${agentId}/focus/?include_completed=${includeCompleted ? "true" : "false"}`,
    ),

  upsert: (
    agentId: string,
    data: {
      key?: string;
      title?: string | null;
      description: string;
      status?: FocusApiItem["status"];
      kind?: FocusApiItem["kind"];
      source?: string;
      metadata?: { [key: string]: JsonValue };
    },
  ) =>
    request<FocusApiItem>(`/agents/${agentId}/focus/`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  complete: (agentId: string, key: string) =>
    request<FocusApiItem>(
      `/agents/${agentId}/focus/${encodeURIComponent(key)}/complete`,
      { method: "POST" },
    ),
};

// ─── Channel Config ───────────────────────────────────
export const channelApi = {
  get: (agentId: string) =>
    request<ChannelConfig>(`/agents/${agentId}/channel`).catch(() => null),

  create: (agentId: string, data: ChannelConfigRequest) =>
    request<ChannelConfig>(`/agents/${agentId}/channel`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  update: (agentId: string, data: ChannelConfigRequest) =>
    request<ChannelConfig>(`/agents/${agentId}/channel`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  delete: (agentId: string) =>
    requestVoid(`/agents/${agentId}/channel`, { method: "DELETE" }),

  webhookUrl: (agentId: string) =>
    request<{ webhook_url: string }>(
      `/agents/${agentId}/channel/webhook-url`,
    ).catch(() => null),
};

// ─── Enterprise ───────────────────────────────────────
export const enterpriseApi = {
  llmModels: () => {
    const tid = localStorage.getItem("current_tenant_id");
    return request<LlmModel[]>(
      `/enterprise/llm-models${tid ? `?tenant_id=${tid}` : ""}`,
    );
  },

  setDefaultModel: (modelId: string) =>
    requestVoid(`/enterprise/llm-models/${modelId}/set-default`, {
      method: "POST",
    }),
  templates: () => request<AgentTemplate[]>("/agents/templates"),

  // Enterprise Knowledge Base
  kbFiles: (path: string = "") =>
    request<FileItem[]>(
      `/enterprise/knowledge-base/files?path=${encodeURIComponent(path)}`,
    ),

  kbUpload: (file: File, subPath: string = "") =>
    uploadFile(
      `/enterprise/knowledge-base/upload?sub_path=${encodeURIComponent(subPath)}`,
      file,
    ),

  kbRead: (path: string) =>
    request<{ path: string; content: string }>(
      `/enterprise/knowledge-base/content?path=${encodeURIComponent(path)}`,
    ),

  kbWrite: (path: string, content: string) =>
    request(
      `/enterprise/knowledge-base/content?path=${encodeURIComponent(path)}`,
      {
        method: "PUT",
        body: JSON.stringify({ content }),
      },
    ),

  kbDelete: (path: string) =>
    request(
      `/enterprise/knowledge-base/content?path=${encodeURIComponent(path)}`,
      {
        method: "DELETE",
      },
    ),
};

// ─── Activity Logs ────────────────────────────────────
export const activityApi = {
  list: (agentId: string, limit = 50) =>
    request<ActivityItem[]>(`/agents/${agentId}/activity?limit=${limit}`),
};

// ─── Messages ─────────────────────────────────────────
export const messageApi = {
  inbox: (limit = 50) =>
    request<InboxMessage[]>(`/messages/inbox?limit=${limit}`),

  unreadCount: () =>
    request<{ unread_count: number }>("/messages/unread-count"),

  markRead: (messageId: string) =>
    request<void>(`/messages/${messageId}/read`, { method: "PUT" }),

  markAllRead: () => request<void>("/messages/read-all", { method: "PUT" }),
};

// ─── Schedules ────────────────────────────────────────
export const scheduleApi = {
  list: (agentId: string) =>
    request<Schedule[]>(`/agents/${agentId}/schedules/`),

  create: (agentId: string, data: ScheduleCreateRequest) =>
    request<Schedule>(`/agents/${agentId}/schedules/`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  update: (agentId: string, scheduleId: string, data: ScheduleUpdateRequest) =>
    request<Schedule>(`/agents/${agentId}/schedules/${scheduleId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  delete: (agentId: string, scheduleId: string) =>
    requestVoid(`/agents/${agentId}/schedules/${scheduleId}`, {
      method: "DELETE",
    }),

  trigger: (agentId: string, scheduleId: string) =>
    request<ScheduleRunResponse>(
      `/agents/${agentId}/schedules/${scheduleId}/run`,
      {
        method: "POST",
      },
    ),

  history: (agentId: string, scheduleId: string) =>
    request<ScheduleHistoryItem[]>(
      `/agents/${agentId}/schedules/${scheduleId}/history`,
    ),
};

// ─── Skills ───────────────────────────────────────────
export const skillApi = {
  list: () => request<Skill[]>("/skills/"),
  get: (id: string) => request<Skill>(`/skills/${id}`),
  create: (data: SkillMutationRequest) =>
    request<Skill>("/skills/", { method: "POST", body: JSON.stringify(data) }),
  update: (id: string, data: Partial<SkillMutationRequest>) =>
    request<Skill>(`/skills/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
  delete: (id: string) => requestVoid(`/skills/${id}`, { method: "DELETE" }),
  // Path-based browse for FileBrowser
  browse: {
    list: (path: string) =>
      request<FileItem[]>(
        `/skills/browse/list?path=${encodeURIComponent(path)}`,
      ),
    read: (path: string) =>
      request<{ content: string }>(
        `/skills/browse/read?path=${encodeURIComponent(path)}`,
      ),
    write: (path: string, content: string) =>
      request<FileMutationResponse>("/skills/browse/write", {
        method: "PUT",
        body: JSON.stringify({ path, content }),
      }),
    delete: (path: string) =>
      request<FileMutationResponse>(
        `/skills/browse/delete?path=${encodeURIComponent(path)}`,
        {
          method: "DELETE",
        },
      ),
  },
  // ClawHub marketplace integration
  clawhub: {
    search: (q: string) =>
      request<ClawhubSkill[]>(
        `/skills/clawhub/search?q=${encodeURIComponent(q)}`,
      ),
    detail: (slug: string) =>
      request<ClawhubSkill>(`/skills/clawhub/detail/${slug}`),
    install: (slug: string) =>
      request<SkillImportResult>("/skills/clawhub/install", {
        method: "POST",
        body: JSON.stringify({ slug }),
      }),
  },
  importFromUrl: (url: string) =>
    request<SkillImportResult>("/skills/import-from-url", {
      method: "POST",
      body: JSON.stringify({ url }),
    }),
  previewUrl: (url: string) =>
    request<SkillUrlPreview>("/skills/import-from-url/preview", {
      method: "POST",
      body: JSON.stringify({ url }),
    }),
  // Tenant-level settings
  settings: {
    getToken: () =>
      request<{
        configured: boolean;
        source: string;
        masked: string;
        clawhub_configured: boolean;
        clawhub_masked: string;
      }>("/skills/settings/token"),
    setToken: (github_token: string) =>
      request<{ configured: boolean }>("/skills/settings/token", {
        method: "PUT",
        body: JSON.stringify({ github_token }),
      }),
    setClawhubKey: (clawhub_key: string) =>
      request<{ clawhub_configured: boolean }>("/skills/settings/token", {
        method: "PUT",
        body: JSON.stringify({ clawhub_key }),
      }),
  },
  // Agent-level import (writes to agent workspace)
  agentImport: {
    fromClawhub: (agentId: string, slug: string) =>
      request<SkillImportResult>(
        `/agents/${agentId}/files/import-from-clawhub`,
        {
          method: "POST",
          body: JSON.stringify({ slug }),
        },
      ),
    fromUrl: (agentId: string, url: string) =>
      request<SkillImportResult>(`/agents/${agentId}/files/import-from-url`, {
        method: "POST",
        body: JSON.stringify({ url }),
      }),
  },
};

// ─── Triggers (Aware Engine) ──────────────────────────
export const triggerApi = {
  list: (agentId: string) => request<Trigger[]>(`/agents/${agentId}/triggers`),

  update: (agentId: string, triggerId: string, data: TriggerUpdateRequest) =>
    request<{ ok: boolean }>(`/agents/${agentId}/triggers/${triggerId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  delete: (agentId: string, triggerId: string) =>
    request<void>(`/agents/${agentId}/triggers/${triggerId}`, {
      method: "DELETE",
    }),
};

// ─── Agent Credentials ────────────────────────────────
export const credentialApi = {
  list: (agentId: string) =>
    request<Credential[]>(`/agents/${agentId}/credentials/`),

  create: (agentId: string, data: CredentialMutationRequest) =>
    request<Credential>(`/agents/${agentId}/credentials/`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  update: (
    agentId: string,
    credentialId: string,
    data: CredentialMutationRequest,
  ) =>
    request<Credential>(`/agents/${agentId}/credentials/${credentialId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  delete: (agentId: string, credentialId: string) =>
    requestVoid(`/agents/${agentId}/credentials/${credentialId}`, {
      method: "DELETE",
    }),
};

// ─── AgentBay Take Control ────────────────────────────
export const controlApi = {
  click: (
    agentId: string,
    data: { session_id: string; x: number; y: number; button?: string },
  ) =>
    request<ControlStatusResponse>(
      `/agents/${agentId}/control/click`,
      { method: "POST", body: JSON.stringify(data) },
      parseControlStatusResponse,
    ),

  type: (agentId: string, data: { session_id: string; text: string }) =>
    request<ControlStatusResponse>(
      `/agents/${agentId}/control/type`,
      { method: "POST", body: JSON.stringify(data) },
      parseControlStatusResponse,
    ),

  pressKeys: (agentId: string, data: { session_id: string; keys: string[] }) =>
    request<ControlStatusResponse>(
      `/agents/${agentId}/control/press_keys`,
      { method: "POST", body: JSON.stringify(data) },
      parseControlStatusResponse,
    ),

  /** Simulate a natural human drag (Bezier curve trajectory) for slider CAPTCHAs. */
  drag: (
    agentId: string,
    data: {
      session_id: string;
      from_x: number;
      from_y: number;
      to_x: number;
      to_y: number;
      duration_ms?: number;
    },
  ) =>
    request<ControlStatusResponse>(
      `/agents/${agentId}/control/drag`,
      { method: "POST", body: JSON.stringify(data) },
      parseControlStatusResponse,
    ),

  /** Get the current active page URL from the browser session (for auto-populating domain). */
  currentUrl: (agentId: string, data: { session_id: string }) =>
    request<{ status: string; url: string }>(
      `/agents/${agentId}/control/current-url`,
      { method: "POST", body: JSON.stringify(data) },
    ),

  screenshot: (agentId: string, data: { session_id: string }) =>
    request<ControlScreenshotResponse>(
      `/agents/${agentId}/control/screenshot`,
      {
        method: "POST",
        body: JSON.stringify(data),
      },
      parseControlScreenshotResponse,
    ),

  lock: (
    agentId: string,
    data: { session_id: string; platform_hint?: string; env_type?: string },
  ) =>
    request<ControlStatusResponse>(
      `/agents/${agentId}/control/lock`,
      { method: "POST", body: JSON.stringify(data) },
      parseControlStatusResponse,
    ),

  unlock: (
    agentId: string,
    data: {
      session_id: string;
      export_cookies?: boolean;
      platform_hint?: string;
    },
  ) =>
    request<ControlUnlockResponse>(
      `/agents/${agentId}/control/unlock`,
      { method: "POST", body: JSON.stringify(data) },
      parseControlUnlockResponse,
    ),
};

// ─── Experience Library ───────────────────────────────
export interface ExperienceEntry {
  id: string;
  // Set only for an edit draft derived from a published/retired source entry.
  draft_of_id: string | null;
  tenant_id: string | null;
  title: string;
  body: string; // 正文 — free-form markdown
  applicability: string; // 适用条件与失效信号 — the agent's read-or-skip preview; required to publish
  status: "draft" | "published" | "retired";
  tags: string[];
  // Legacy response fields; published Experience is tenant-wide.
  visibility_scope: "company" | "department" | "user";
  visibility_scope_id: string | null;
  origin: "chat" | "legacy_plaza";
  origin_session_id: string | null;
  origin_agent_id: string | null;
  created_by: string;
  reviewed_by: string | null;
  last_reviewed_at: string | null;
  retired_at: string | null;
  created_at: string;
  updated_at: string | null;
  created_by_name?: string | null;
  origin_agent_name?: string | null;
  // Whether the caller may edit/review/retire/re-publish (single-entry fetch only; null in lists).
  can_manage?: boolean | null;
}

export type ExperienceView = "team" | "mine" | "all";

export const experienceApi = {
  list: (
    params: {
      view?: ExperienceView;
      status?: string;
      tag?: string;
      q?: string;
    } = {},
  ) => {
    const qs = new URLSearchParams();
    if (params.view) qs.set("view", params.view);
    if (params.status) qs.set("status", params.status);
    if (params.tag) qs.set("tag", params.tag);
    if (params.q) qs.set("q", params.q);
    const s = qs.toString();
    return request<ExperienceEntry[]>(`/experience/entries${s ? `?${s}` : ""}`);
  },
  get: (id: string) => request<ExperienceEntry>(`/experience/entries/${id}`),
  createDraftFromContent: (data: {
    agent_id: string;
    content: string;
    session_id?: string;
  }) =>
    request<ExperienceEntry>("/experience/drafts", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  // Distill chat content into title / body / applicability WITHOUT persisting (human confirms in the editor).
  distill: (data: { agent_id: string; content: string; session_id?: string }) =>
    request<{
      title: string;
      body: string;
      applicability: string;
      tags: string[];
      extracted: boolean;
    }>("/experience/distill", { method: "POST", body: JSON.stringify(data) }),
  create: (data: Partial<ExperienceEntry>) =>
    request<ExperienceEntry>("/experience/entries", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  createRevision: (id: string, data: Partial<ExperienceEntry>) =>
    request<ExperienceEntry>(`/experience/entries/${id}/draft`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  update: (id: string, data: Partial<ExperienceEntry>) =>
    request<ExperienceEntry>(`/experience/entries/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  publish: (id: string) =>
    request<ExperienceEntry>(`/experience/entries/${id}/publish`, {
      method: "POST",
    }),
  retire: (id: string) =>
    request<ExperienceEntry>(`/experience/entries/${id}/retire`, {
      method: "POST",
    }),
  remove: (id: string) =>
    request<{ deleted: boolean }>(`/experience/entries/${id}`, {
      method: "DELETE",
    }),
  review: (id: string) =>
    request<ExperienceEntry>(`/experience/entries/${id}/review`, {
      method: "POST",
    }),
  references: (id: string) =>
    request<{ entry_id: string; read_count: number; cited_count: number }>(
      `/experience/entries/${id}/references`,
    ),
  stats: () =>
    request<{
      total: number;
      today: number;
      cited: number;
      top_contributors: { name: string; count: number }[];
    }>("/experience/stats"),
};

// ─── Org structure (synced from Feishu/DingTalk/WeCom; empty until org sync runs) ───
export interface OrgDepartmentItem {
  id: string;
  name: string;
  path?: string;
  parent_id?: string | null;
  member_count?: number;
}

export const orgApi = {
  departments: () =>
    request<{ items: OrgDepartmentItem[]; total_member: number }>(
      "/enterprise/org/departments",
    ),
};
