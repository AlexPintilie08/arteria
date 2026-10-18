import type { AnalyzeRequest, AnalyzeResponse, ProposeRequest, ProposeResponse, EvaluateRequest, EvaluateResponse, ApiErrorBody, SpatialStudy, SpatialSelection, SpatialEvaluation, SpatialPlanningResult } from './contracts.ts';
import { ApiContractError, isApiErrorBody, parseApiResponse } from './runtime-validation.ts';
export { ApiContractError } from './runtime-validation.ts';

export class ApiError extends Error {
  readonly status: number;
  readonly body?: ApiErrorBody;
  constructor(message: string, status: number, body?: ApiErrorBody) {
    super(message); this.name = 'ApiError'; this.status = status; this.body = body;
  }
}
export class ApiTimeoutError extends Error {
  constructor() { super('Cererea a expirat înainte ca API-ul să răspundă.'); this.name = 'ApiTimeoutError'; }
}
export function createApiClient(baseUrl: string, options: { fetch?: typeof fetch; timeoutMs?: number } = {}) {
  const transport = options.fetch ?? globalThis.fetch;
  async function request<T>(path: string, init: RequestInit, signal?: AbortSignal): Promise<T> {
    const controller = new AbortController();
    const abort = () => controller.abort(signal?.reason);
    if (signal?.aborted) abort();
    else signal?.addEventListener('abort', abort, { once: true });
    let timedOut = false;
    const timeout = setTimeout(() => { timedOut = true; controller.abort(); }, options.timeoutMs ?? 30_000);
    try {
      let response: Response;
      try {
        response = await transport(`${baseUrl.replace(/\/$/, '')}${path}`, { ...init, signal: controller.signal });
      } catch (cause) { if (timedOut) throw new ApiTimeoutError(); throw cause; }
      if (!response.ok) {
        let body: ApiErrorBody | undefined;
        try {
          const candidate: unknown = await response.json();
          if (isApiErrorBody(candidate)) body = candidate;
        } catch { if (timedOut) throw new ApiTimeoutError(); /* A proxy may return HTML. Keep the public error readable. */ }
        throw new ApiError(body?.error.message ?? `Serviciul a răspuns cu HTTP ${response.status}.`, response.status, body);
      }
      let candidate: unknown;
      try { candidate = await response.json(); }
      catch { if (timedOut) throw new ApiTimeoutError(); throw new ApiContractError(endpointName(path), `JSON-ul nu poate fi decodat (HTTP ${response.status})`); }
      return parseApiResponse<T>(candidate, endpointName(path));
    } finally {
      clearTimeout(timeout); signal?.removeEventListener('abort', abort);
    }
  }
  async function post<T>(path: string, payload: unknown, signal?: AbortSignal, headers: Record<string, string> = {}): Promise<T> {
    return request<T>(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...headers },
      body: JSON.stringify(payload),
    }, signal);
  }
  async function get<T>(path: string, signal?: AbortSignal): Promise<T> {
    return request<T>(path, { method: 'GET' }, signal);
  }
  return {
    spatialStudy: (signal?: AbortSignal) => post<SpatialStudy>('/api/v1/spatial/studies', { source: 'fixture' }, signal),
    getSpatialStudy: (studyId: string, signal?: AbortSignal) => get<SpatialStudy>(
      `/api/v1/spatial/studies/${encodeURIComponent(studyId)}`, signal,
    ),
    spatialNeighborhoodStudy: (neighborhoodId: string, signal?: AbortSignal) => post<SpatialStudy>(
      '/api/v1/spatial/studies', { source: 'osm', neighborhood_id: neighborhoodId }, signal,
    ),
    spatialPlanning: (studyId: string, idempotencyKey: string, signal?: AbortSignal) => post<SpatialPlanningResult>(
      `/api/v1/spatial/studies/${encodeURIComponent(studyId)}/planning`, {}, signal, { 'Idempotency-Key': idempotencyKey },
    ),
    getSpatialPlanning: (studyId: string, planningId: string, signal?: AbortSignal) => get<SpatialPlanningResult>(
      `/api/v1/spatial/studies/${encodeURIComponent(studyId)}/planning/${encodeURIComponent(planningId)}`, signal,
    ),
    spatialEvaluate: (studyId: string, body: SpatialSelection, signal?: AbortSignal) => post<SpatialEvaluation>(`/api/v1/spatial/studies/${encodeURIComponent(studyId)}/evaluate`, body, signal),
    analyze: (body: AnalyzeRequest, signal?: AbortSignal) => post<AnalyzeResponse>('/analyze', body, signal),
    propose: (body: ProposeRequest, signal?: AbortSignal) => post<ProposeResponse>('/propose', body, signal),
    evaluate: (body: EvaluateRequest, signal?: AbortSignal) => post<EvaluateResponse>('/evaluate', body, signal),
  };
}

function endpointName(path: string) {
  if (path.includes('/planning')) return 'spatialPlanning';
  if (path === '/analyze') return 'analyze';
  if (path === '/propose') return 'propose';
  if (path === '/evaluate') return 'evaluate';
  if (path.endsWith('/evaluate')) return 'spatialEvaluate';
  return 'spatialStudy';
}
