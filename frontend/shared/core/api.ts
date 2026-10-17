import type { AnalyzeRequest, AnalyzeResponse, ProposeRequest, ProposeResponse, EvaluateRequest, EvaluateResponse, ApiErrorBody, SpatialStudy, SpatialSelection, SpatialEvaluation } from './contracts.ts';

export class ApiError extends Error {
  readonly status: number;
  readonly body?: ApiErrorBody;
  constructor(message: string, status: number, body?: ApiErrorBody) {
    super(message); this.name = 'ApiError'; this.status = status; this.body = body;
  }
}
export function createApiClient(baseUrl: string, options: { fetch?: typeof fetch; timeoutMs?: number } = {}) {
  const transport = options.fetch ?? globalThis.fetch;
  async function post<T>(path: string, payload: unknown, signal?: AbortSignal): Promise<T> {
    const controller = new AbortController();
    const abort = () => controller.abort(signal?.reason);
    if (signal?.aborted) abort();
    else signal?.addEventListener('abort', abort, { once: true });
    const timeout = setTimeout(() => controller.abort(), options.timeoutMs ?? 30_000);
    try {
      const response = await transport(`${baseUrl.replace(/\/$/, '')}${path}`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload), signal: controller.signal,
      });
      if (!response.ok) {
        let body: ApiErrorBody | undefined;
        try {
          const candidate = await response.json() as Partial<ApiErrorBody>;
          if (candidate.error && typeof candidate.error.message === 'string') body = candidate as ApiErrorBody;
        } catch { /* A proxy may return HTML. Keep the public error readable. */ }
        throw new ApiError(body?.error.message ?? `Serviciul a răspuns cu HTTP ${response.status}.`, response.status, body);
      }
      // Compile-time types only. Add runtime validators once the backend schema is finalized.
      return await response.json() as T;
    } finally {
      clearTimeout(timeout); signal?.removeEventListener('abort', abort);
    }
  }
  return {
    spatialStudy: (signal?: AbortSignal) => post<SpatialStudy>('/api/v1/spatial/studies', { source: 'fixture' }, signal),
    spatialEvaluate: (studyId: string, body: SpatialSelection, signal?: AbortSignal) => post<SpatialEvaluation>(`/api/v1/spatial/studies/${encodeURIComponent(studyId)}/evaluate`, body, signal),
    analyze: (body: AnalyzeRequest, signal?: AbortSignal) => post<AnalyzeResponse>('/analyze', body, signal),
    propose: (body: ProposeRequest, signal?: AbortSignal) => post<ProposeResponse>('/propose', body, signal),
    evaluate: (body: EvaluateRequest, signal?: AbortSignal) => post<EvaluateResponse>('/evaluate', body, signal),
  };
}
