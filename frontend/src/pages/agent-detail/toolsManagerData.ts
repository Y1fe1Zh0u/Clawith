type FetchTools = (
  url: string,
  init: { headers: { Authorization: string } },
) => Promise<Response>;

interface RequestAgentToolsOptions<T> {
  agentId: string;
  token: string | null;
  parsePayload: (payload: unknown) => T;
  parseError: (response: Response) => Promise<Error>;
  fetchImpl?: FetchTools;
}

export async function requestAgentToolsWithConfig<T>({
  agentId,
  token,
  parsePayload,
  parseError,
  fetchImpl = fetch,
}: RequestAgentToolsOptions<T>): Promise<T> {
  const response = await fetchImpl(
    `/api/tools/agents/${encodeURIComponent(agentId)}/with-config`,
    { headers: { Authorization: `Bearer ${token || ""}` } },
  );
  if (!response.ok) {
    throw await parseError(response);
  }
  return parsePayload(await response.json());
}
