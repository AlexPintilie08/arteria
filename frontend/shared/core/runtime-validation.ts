import type {
  AnalyzeResponse, ApiErrorBody, EvaluateResponse, ProposeResponse, SpatialEvaluation, SpatialStudy,
} from './contracts.ts';

export class ApiContractError extends Error {
  readonly endpoint: string;
  constructor(endpoint: string, detail: string) {
    super(`Răspuns API invalid pentru ${endpoint}: ${detail}`);
    this.name = 'ApiContractError';
    this.endpoint = endpoint;
  }
}

type Check = (value: unknown, path: string) => void;
const record: Check = (v, p) => { if (!v || typeof v !== 'object' || Array.isArray(v)) throw new Error(`${p} trebuie să fie un obiect`); };
const string: Check = (v, p) => { if (typeof v !== 'string' || !v) throw new Error(`${p} trebuie să fie text nevid`); };
const nullableString: Check = (v, p) => { if (v !== null) string(v, p); };
const numberOrNull: Check = (v, p) => { if (v !== null && (typeof v !== 'number' || !Number.isFinite(v))) throw new Error(`${p} trebuie să fie număr finit sau null`); };
function array(v: unknown, p: string, item: Check = () => {}) { if (!Array.isArray(v)) throw new Error(`${p} trebuie să fie o listă`); v.forEach((x, i) => item(x, `${p}[${i}]`)); }
const strings: Check = (v, p) => array(v, p, string);
function field(o: Record<string, unknown>, key: string, check: Check, path = '') { check(o[key], path ? `${path}.${key}` : key); }
function objectAt(v: unknown, p: string): Record<string, unknown> { record(v, p); return v as Record<string, unknown>; }
function checkProvenance(v: unknown, p: string) {
  const o = objectAt(v, p);
  for (const k of ['source', 'source_version', 'method', 'crs']) field(o, k, string, p);
  field(o, 'retrieved_at', string, p);
}
function checkUncertainty(v: unknown, p: string) {
  const o = objectAt(v, p); field(o, 'kind', string, p); field(o, 'description', string, p);
  if (!Array.isArray(o.interval) && o.interval !== null) throw new Error(`${p}.interval trebuie să fie listă sau null`);
  if (o.confidence !== null && (typeof o.confidence !== 'number' || !Number.isFinite(o.confidence))) throw new Error(`${p}.confidence invalid`);
}
function checkMeasurement(v: unknown, p: string) {
  const o = objectAt(v, p); field(o, 'value', numberOrNull, p); field(o, 'unit', string, p);
  if (!['observed', 'calculated', 'estimated', 'unknown'].includes(String(o.status))) throw new Error(`${p}.status invalid`);
  field(o, 'provenance', (x, q) => array(x, q, checkProvenance), p); field(o, 'uncertainty', checkUncertainty, p);
}
function checkIndicator(v: unknown, p: string) { const o = objectAt(v, p); field(o, 'id', string, p); field(o, 'label', string, p); checkMeasurement(o, p); }
function checkGeometry(v: unknown, p: string) {
  if (v === null) return;
  const o = objectAt(v, p);
  if (!['Point', 'LineString', 'Polygon'].includes(String(o.type)) || !Array.isArray(o.coordinates)) throw new Error(`${p} nu este o geometrie suportată`);
}
function checkAnalyze(v: unknown) {
  const o = objectAt(v, 'response');
  for (const k of ['analysis_id', 'baseline_id', 'created_at']) field(o, k, string);
  const area = objectAt(o.area, 'area'); field(area, 'city_id', string, 'area'); field(area, 'area_id', string, 'area'); field(area, 'crs', string, 'area');
  if (area.boundary !== null) checkGeometry(area.boundary, 'area.boundary');
  if (!['known_area', 'user_selected'].includes(String(area.boundary_source))) throw new Error('area.boundary_source invalid');
  field(o, 'inputs', (x, p) => { const i = objectAt(x, p); for (const k of ['cycle_seconds', 'lost_seconds', 'ns_green_seconds']) if (typeof i[k] !== 'number' || !Number.isFinite(i[k])) throw new Error(`${p}.${k} invalid`); }, 'response');
  field(o, 'provenance', (x, p) => array(x, p, checkProvenance));
  field(o, 'indicators', (x, p) => array(x, p, checkIndicator));
  field(o, 'issues', (x, p) => array(x, p, (item, q) => { const i = objectAt(item, q); field(i, 'id', string, q); field(i, 'label', string, q); field(i, 'geometry', checkGeometry, q); field(i, 'provenance', (z, r) => array(z, r, checkProvenance), q); field(i, 'uncertainty', checkUncertainty, q); field(i, 'indicator_ids', strings, q); }));
  field(o, 'layer_availability', (x, p) => array(x, p, (item, q) => { const i = objectAt(item, q); field(i, 'layer', string, q); field(i, 'status', string, q); field(i, 'reason', string, q); }));
  field(o, 'warnings', strings);
  if (o.mode !== 'demo') throw new Error('mode trebuie să fie demo');
}
function checkPropose(v: unknown) {
  const o = objectAt(v, 'response'); for (const k of ['proposal_set_id', 'analysis_id', 'baseline_id']) field(o, k, string);
  const m = objectAt(o.model, 'model'); for (const k of ['provider', 'model_id', 'generated_at']) field(m, k, string, 'model');
  field(o, 'alternatives', (x, p) => array(x, p, (item, q) => { const a = objectAt(item, q); for (const k of ['level', 'summary', 'rationale']) field(a, k, string, q); field(a, 'interventions', (z, r) => array(z, r, (iv, s) => { const obj = objectAt(iv, s); field(obj, 'type', string, s); field(obj, 'parameters', record, s); field(obj, 'geometry', checkGeometry, s); } ), q); field(a, 'expected_impacts', (z, r) => array(z, r, (im, s) => { const e = objectAt(im, s); field(e, 'indicator_id', string, s); checkMeasurement(e, s); field(e, 'direction', string, s); } ), q); const val = objectAt(a.validation, `${q}.validation`); field(val, 'status', string, `${q}.validation`); field(val, 'checks', strings, `${q}.validation`); field(a, 'assumptions', strings, q); }));
  field(o, 'rejected_alternatives', array); field(o, 'warnings', strings);
}
function checkEvaluate(v: unknown) {
  const o = objectAt(v, 'response'); for (const k of ['evaluation_id', 'scenario_id', 'created_at']) field(o, k, string);
  for (const key of ['baseline', 'scenario']) { const r = objectAt(o[key], key); field(r, 'id', string, key); field(r, 'source_snapshot', string, key); field(r, 'intervention_catalog_version', string, key); }
  field(o, 'comparisons', (x, p) => array(x, p, (item, q) => { const c = objectAt(item, q); field(c, 'indicator_id', string, q); for (const k of ['baseline', 'scenario', 'delta']) checkMeasurement(c[k], `${q}.${k}`); field(c, 'percent_change', numberOrNull, q); if (!['improved', 'worsened', 'unchanged', 'unknown'].includes(String(c.impact))) throw new Error(`${q}.impact invalid`); }));
  const sim = objectAt(o.simulation, 'simulation'); for (const k of ['status', 'mode']) field(sim, k, string, 'simulation'); field(sim, 'measurements', (x, p) => array(x, p, checkIndicator), 'simulation'); field(o, 'warnings', strings);
}
function checkSpatialStudy(v: unknown) {
  const o = objectAt(v, 'response'); for (const k of ['study_id', 'baseline_id', 'created_at', 'engine_revision']) field(o, k, string);
  if (!['fixture', 'osm'].includes(String(o.source))) throw new Error('source trebuie să fie fixture sau osm');
  if (o.calculation !== 'pedestrian_graph') throw new Error('calculation invalid');
  const a = objectAt(o.analysis, 'analysis');
  if (a.provenance !== undefined) { const p = objectAt(a.provenance, 'analysis.provenance'); field(p, 'source', string, 'analysis.provenance'); if (p.source_version !== undefined && p.source_version !== null) field(p, 'source_version', string, 'analysis.provenance'); if (p.retrieved_at !== undefined && p.retrieved_at !== null) field(p, 'retrieved_at', string, 'analysis.provenance'); }
  const alt = objectAt(o.alternatives, 'alternatives'); field(alt, 'ranked_candidates', (x, p) => array(x, p, (item, q) => { const c = objectAt(item, q); field(c, 'candidate_id', string, q); field(c, 'intervention', record, q); field(c, 'evaluation_rationale', strings, q); }), 'alternatives'); field(alt, 'warnings', strings, 'alternatives');
  field(o, 'proposal_options', (x, p) => array(x, p, (item, q) => {
    const option = objectAt(item, q);
    for (const k of ['candidate_id', 'summary', 'evaluation_status', 'planning_category_status']) field(option, k, string, q);
    if (typeof option.rank !== 'number' || !Number.isFinite(option.rank)) throw new Error(`${q}.rank invalid`);
    field(option, 'intervention', record, q);
    const impact = objectAt(option.modeled_impact, `${q}.modeled_impact`);
    if (impact.observed !== false) throw new Error(`${q}.modeled_impact.observed trebuie să fie false`);
    const aggregate = objectAt(impact.aggregate, `${q}.modeled_impact.aggregate`);
    for (const [k, n] of Object.entries(aggregate)) numberOrNull(n, `${q}.modeled_impact.aggregate.${k}`);
    const screening = objectAt(option.screening, `${q}.screening`);
    if (screening.physical_feasibility !== 'unknown') throw new Error(`${q}.screening.physical_feasibility invalid`);
    field(screening, 'missing_evidence', strings, `${q}.screening`); field(screening, 'warnings', strings, `${q}.screening`);
  }));
  checkProposalValidation(o.proposal_validation, 'proposal_validation');
  const evidence = objectAt(o.evidence_packet, 'evidence_packet');
  if (evidence.schema_version !== undefined) string(evidence.schema_version, 'evidence_packet.schema_version');
  if (evidence.truncation !== undefined) { const truncation = objectAt(evidence.truncation, 'evidence_packet.truncation'); if (truncation.serialized_bytes !== undefined && (typeof truncation.serialized_bytes !== 'number' || !Number.isFinite(truncation.serialized_bytes))) throw new Error('evidence_packet.truncation.serialized_bytes invalid'); }
  field(o, 'warnings', strings);
}
function checkProposalValidation(v: unknown, p: string) {
  const o = objectAt(v, p); field(o, 'status', string, p);
  const summary = objectAt(o.summary, `${p}.summary`);
  for (const key of ['submitted_count', 'accepted_count', 'rejected_count', 'duplicate_count']) if (typeof summary[key] !== 'number' || !Number.isFinite(summary[key])) throw new Error(`${p}.summary.${key} invalid`);
  field(o, 'results', (x, q) => array(x, q, (item, r) => { const result = objectAt(item, r); nullableString(result.candidate_id, `${r}.candidate_id`); field(result, 'status', string, r); if (result.physical_feasibility !== 'unknown') throw new Error(`${r}.physical_feasibility invalid`); field(result, 'findings', (z, s) => array(z, s, (finding, t) => { const f = objectAt(finding, t); field(f, 'code', string, t); field(f, 'message', string, t); }), r); }), p);
}
function checkCandidateValidation(v: unknown, p: string) {
  const o = objectAt(v, p);
  field(o, 'status', string, p);
  nullableString(o.candidate_id, `${p}.candidate_id`);
  if (o.physical_feasibility !== 'unknown') throw new Error(`${p}.physical_feasibility invalid`);
  field(o, 'findings', (x, q) => array(x, q, (item, r) => { const finding = objectAt(item, r); field(finding, 'code', string, r); field(finding, 'message', string, r); }), p);
}
function checkSpatialEvaluation(v: unknown) {
  const o = objectAt(v, 'response'); for (const k of ['study_id', 'baseline_id', 'candidate_id', 'evaluated_at']) field(o, k, string);
  if (!['fixture', 'osm'].includes(String(o.source)) || o.execution !== 'stored_graph_comparison' || o.sumo_executed !== false) throw new Error('proveniența sau tipul comparației invalide');
  const impact = objectAt(o.impact, 'impact'); const aggregate = objectAt(impact.aggregate, 'impact.aggregate'); for (const [k, value] of Object.entries(aggregate)) numberOrNull(value, `impact.aggregate.${k}`);
  field(impact, 'routes', (x, p) => array(x, p, (item, q) => { const r = objectAt(item, q); field(r, 'origin_node_id', string, q); field(r, 'destination_node_id', string, q); field(r, 'outcome', string, q); field(r, 'distance_delta_m', numberOrNull, q); }), 'impact');
  checkCandidateValidation(o.proposal_validation, 'proposal_validation'); field(o, 'warnings', strings);
}
function checkSpatialPlanning(v: unknown) {
  const o = objectAt(v, 'response');
  for (const k of ['planning_id', 'study_id', 'baseline_id', 'area_id', 'engine_revision', 'evidence_packet_sha256', 'created_at']) field(o, k, string);
  if (!/^[a-f0-9]{64}$/.test(String(o.evidence_packet_sha256))) throw new Error('evidence_packet_sha256 invalid');
  if (!['fixture', 'osm'].includes(String(o.source)) || o.calculation !== 'pedestrian_graph') throw new Error('source sau calculation invalid');
  if (!['provider_unavailable', 'timeout', 'provider_error', 'invalid_response', 'completed_with_rejections', 'completed'].includes(String(o.provider_status))) throw new Error('provider_status invalid');
  if (typeof o.ai_generated !== 'boolean') throw new Error('ai_generated trebuie să fie boolean');
  nullableString(o.provider, 'provider'); nullableString(o.model_id, 'model_id'); nullableString(o.summary, 'summary'); nullableString(o.error_code, 'error_code');
  field(o, 'identified_problems', (x, p) => array(x, p, (item, q) => objectAt(item, q)));
  const recommendations = o.recommended_solutions;
  field(o, 'recommended_solutions', (x, p) => array(x, p, (item, q) => {
    const recommendation = objectAt(item, q);
    field(recommendation, 'solution_id', string, q); field(recommendation, 'candidate_id', string, q);
    if (recommendation.authoritative_sim_solution !== undefined) {
      const authoritative = objectAt(recommendation.authoritative_sim_solution, `${q}.authoritative_sim_solution`);
      field(authoritative, 'solution_id', string, `${q}.authoritative_sim_solution`);
      field(authoritative, 'candidate_id', string, `${q}.authoritative_sim_solution`);
      if (authoritative.candidate_id !== recommendation.candidate_id) throw new Error(`${q}.authoritative_sim_solution.candidate_id mismatch`);
    }
  }));
  if (o.validation !== null) objectAt(o.validation, 'validation');
  field(o, 'warnings', strings);
  if (!o.ai_generated && Array.isArray(recommendations) && recommendations.length !== 0) throw new Error('recomandările nevalidate nu pot fi afișate ca AI');
}
const validators: Record<string, Check> = {
  analyze: checkAnalyze, propose: checkPropose, evaluate: checkEvaluate,
  spatialStudy: checkSpatialStudy, spatialNeighborhoodStudy: checkSpatialStudy, spatialEvaluate: checkSpatialEvaluation,
  spatialPlanning: checkSpatialPlanning,
};
export function parseApiResponse<T>(value: unknown, endpoint: string): T {
  try { validators[endpoint]?.(value, 'response'); }
  catch (cause) { throw new ApiContractError(endpoint, cause instanceof Error ? cause.message : 'schema incompatibil'); }
  return value as T;
}
export function isApiErrorBody(value: unknown): value is ApiErrorBody {
  try {
    const root = objectAt(value, 'body'); const err = objectAt(root.error, 'error');
    for (const k of ['code', 'message', 'request_id']) field(err, k, string, 'error');
    field(err, 'details', (x, p) => array(x, p, (item, q) => { const d = objectAt(item, q); field(d, 'field', string, q); field(d, 'reason', string, q); }), 'error');
    return true;
  } catch { return false; }
}
