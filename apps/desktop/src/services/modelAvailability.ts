/** Fixed server diagnostics only; never display upstream response text. */
export const MODEL_HTTP: Record<string, number> = {
  model_unavailable: 502,
  model_identity_unavailable: 502,
  model_access_denied: 502,
  model_busy: 429,
  model_rate_limited: 429,
  model_deadline: 504,
  model_not_ready: 503,
  model_budget_exhausted: 429,
};
export type ModelStatus = { state: string; used: number; limit: 3 };
export const MODEL_MESSAGES: Record<string, string> = {
  ready:
    "The service reported ready at this check. A successful embedding/search still needs its own validation.",
  model_identity_unavailable:
    "The backend could not obtain its Google caller identity. The operator should check the personal Gather account sign-in/configuration before trying again. No embedding request was sent.",
  model_access_denied:
    "The model service rejected the backend caller. The operator should check the service account, audience and invocation permissions. No automatic retry was made.",
  model_busy:
    "A local connection or the model service is busy. Wait, then explicitly check the connection again. Your search was not replayed.",
  model_rate_limited:
    "The cloud platform or service rate-limited the request. Startup or capacity may be involved, but the cause is unconfirmed. Wait and explicitly check again.",
  model_deadline:
    "The request deadline expired. Remote computation may have started; no automatic retry was made. Check the connection before deciding to search again.",
  model_not_ready:
    "The service reports that the model is not ready. Wait and explicitly check again. If it persists, the operator should inspect the Gather service; this response alone does not establish the cause.",
  model_budget_exhausted:
    "This local API process has used its three model attempts. No further model request was sent. Review the pilot spend before intentionally restarting the Gather API for another test session.",
  model_unavailable:
    "Model availability could not be established. Use Check model connection for a separate diagnostic; your search will not be retried automatically.",
};
