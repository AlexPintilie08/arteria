/** Draft wire contract: docs/API_CONTRACT.md. Coordinates are [longitude, latitude]. */
export type Position = [number, number];
export type Geometry =
  | { type: 'Point'; coordinates: Position }
  | { type: 'LineString'; coordinates: Position[] }
  | { type: 'Polygon'; coordinates: Position[][] };
export type EvidenceStatus = 'observed' | 'calculated' | 'estimated' | 'unknown';
export interface Provenance {
  source: string;
  source_version: string;
  retrieved_at: string;
  method: string;
  crs: string;
}
export interface Uncertainty {
  kind: string;
  description: string;
  interval: [number, number] | null;
  confidence: number | null;
}
export interface Evidence {
  status: EvidenceStatus;
  provenance: Provenance[];
  uncertainty: Uncertainty;
}
export type Measurement = Evidence & { value: number | null; unit: string };
export type Indicator = Measurement & { id: string; label: string };
export interface AreaRef { city_id: string; area_id: string }
export interface Area extends AreaRef {
  boundary: Extract<Geometry, { type: 'Polygon' }> | null;
  boundary_source: 'known_area' | 'user_selected';
  crs: string;
}
export type LayerId = 'roads' | 'walking' | 'cycling' | 'public_transport' | 'parking' | 'green_space' | 'buildings' | 'points_of_interest';
export type AlternativeLevel = 'minimal' | 'moderate' | 'transformative';
export interface AnalyzeRequest {
  area: Area;
  layers: LayerId[];
  analysis: {
    network_modes: ('walk' | 'bike' | 'drive')[];
    accessibility_thresholds: { value: number; unit: 'minute'; mode: 'walk' | 'bike' | 'drive' }[];
  };
  data_as_of: string | null;
}
/** Issue shape is provisional: the backend has not finalized its schema yet. */
export interface Issue extends Evidence {
  id: string; label: string; indicator_ids: string[]; geometry: Geometry | null;
}
export interface AnalyzeResponse {
  analysis_id: string;
  baseline_id: string;
  inputs?: { cycle_seconds: number; lost_seconds: number; ns_green_seconds: number };
  area: AreaRef & { crs: string };
  created_at: string;
  indicators: Indicator[];
  issues: Issue[];
  layer_availability: { layer: LayerId; status: EvidenceStatus; reason: string }[];
  warnings: string[];
}
export interface Intervention {
  type: string; geometry: Geometry; parameters: Record<string, unknown>;
  parameter_units?: Record<string, string>; affected_feature_ids?: string[];
}
export interface ProposeRequest {
  analysis_id: string; area: AreaRef; issue_id: string;
  intervention_catalog_version: string;
  constraints: { max_affected_area: { value: number; unit: 'hectare' } };
  requested_alternatives: AlternativeLevel[];
  parameters?: { ns_green_seconds: number };
}
export interface Alternative {
  level: AlternativeLevel; summary: string; interventions: Intervention[]; rationale: string;
  expected_impacts: (Evidence & { indicator_id: string; direction: 'increase' | 'decrease' | 'unchanged'; value: number | null; unit: string | null })[];
  assumptions: string[];
  validation: { status: 'accepted' | 'rejected' | 'unavailable'; checks: string[] };
}
export interface ProposeResponse {
  proposal_set_id: string; analysis_id: string;
  model: { provider: string; model_id: string; generated_at: string };
  alternatives: Alternative[];
  rejected_alternatives: unknown[];
  warnings: string[];
}
export type SimulationRequest =
  | { requested: false; mode: 'none'; replay_id: null }
  | { requested: true; mode: 'live' | 'offline'; replay_id: null }
  | { requested: true; mode: 'replay'; replay_id: string };
export interface EvaluateRequest {
  analysis_id: string; area: AreaRef; baseline_id: string;
  proposal_set_id: string; alternative_level: AlternativeLevel;
  interventions: Intervention[];
  evaluation: { indicators: string[]; traffic_simulation: SimulationRequest };
}
export interface EvaluateResponse {
  evaluation_id: string; scenario_id: string; created_at: string;
  baseline: { id: string; source_snapshot: string };
  scenario: { id: string; intervention_catalog_version: string };
  comparisons: { indicator_id: string; baseline: Measurement; scenario: Measurement; delta: Measurement }[];
  simulation: {
    status: string; mode: 'none' | 'live' | 'offline' | 'replay'; run_id: string | null;
    started_at: string | null; completed_at: string | null;
    simulator: { name: string; version: string } | null;
    configuration: Record<string, unknown> | null; measurements: Indicator[];
  };
  warnings: string[];
}
export interface ApiErrorBody {
  error: { code: string; message: string; details: { field: string; reason: string }[]; request_id: string };
}

/** Native graph API kept separate from traffic-signal measurements. */
export interface SpatialCandidate {
  candidate_id: string;
  intervention: Record<string, unknown>;
  rank?: number;
  evaluation_rationale: string[];
  ranking_explanation?: string;
}
export interface SpatialStudy {
  study_id: string; baseline_id: string; source: 'fixture' | 'osm'; engine_revision: string;
  analysis: Record<string, unknown>;
  alternatives: { ranked_candidates: SpatialCandidate[]; warnings: string[] };
  proposal_options: SpatialProposalOption[];
  proposal_validation: SpatialProposalValidation;
  evidence_packet: Record<string, unknown>;
  warnings: string[];
}
export interface SpatialProposalOption {
  candidate_id: string;
  rank: number;
  summary: string;
  intervention: Record<string, unknown>;
  evaluation_status: string;
  planning_category_status: string;
  modeled_impact: { aggregate: Record<string, number | null>; observed: false };
  screening: { status?: string; physical_feasibility: 'unknown'; missing_evidence: string[]; warnings: string[] };
}
export interface SpatialProposalValidation {
  status: string;
  summary: { submitted_count: number; accepted_count: number; rejected_count: number; duplicate_count: number };
  results: { candidate_id: string | null; status: string; physical_feasibility: 'unknown'; findings: { code: string; message: string }[] }[];
}
export interface SpatialSelection {
  baseline_id: string; candidate_id: string; intervention: Record<string, unknown>;
}
export interface SpatialEvaluation {
  source: 'fixture' | 'osm'; execution: 'stored_graph_comparison'; sumo_executed: false;
  evaluated_at: string;
  impact: {
    aggregate: Record<string, number | null>;
    routes: { origin_node_id: string; destination_node_id: string; outcome: string; distance_delta_m: number | null }[];
  };
  proposal_validation: { status: string; candidate_id: string | null; physical_feasibility: 'unknown'; findings: { code: string; message: string }[] };
  warnings: string[];
}
