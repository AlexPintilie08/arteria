import { ApiContractError, ApiError, ApiTimeoutError } from '@arteria/shared/api';

/** User-facing labels; wire identifiers stay unchanged in requests. */
const labels: Record<string, string> = {
  ns_delay: 'Timp de așteptare · nord–sud',
  ew_delay: 'Timp de așteptare · est–vest',
  mean_delay: 'Timp mediu de așteptare',
  ns_green_seconds: 'Durata verdelui nord–sud',
  signal_timing: 'Ajustarea semafoarelor',
  signal_balance: 'Îmbunătățirea timpilor de așteptare',
  estimated: 'Estimat', calculated: 'Calculat', observed: 'Observat', unknown: 'Date indisponibile',
  accepted: 'Disponibilă pentru comparație', rejected: 'Propunere respinsă', unavailable: 'Indisponibilă',
  increase: 'poate crește', decrease: 'poate scădea', unchanged: 'fără schimbare',
  roads: 'Străzi', walking: 'Mers pe jos', cycling: 'Biciclete', public_transport: 'Transport public',
  parking: 'Parcări', green_space: 'Spații verzi', buildings: 'Clădiri', points_of_interest: 'Puncte de interes',
  improved: 'Traseu îmbunătățit', regressed: 'Traseu înrăutățit',
  newly_reachable: 'Traseu devenit accesibil', newly_unreachable: 'Traseu devenit inaccesibil',
  unreachable_both: 'Fără legătură în ambele variante', unreachable_in_both: 'Fără legătură în ambele variante',
};
export const label = (key: string, fallback = 'Alt indicator') => labels[key] ?? fallback;
export const unit = (key: string) => ({ 'second/vehicle': 'secunde / vehicul', second: 'secunde', meter: 'metri', metre: 'metri' }[key] ?? key);
export const source = (key: string) => key === 'fixture' || key === 'synthetic-demo' ? 'Date demonstrative' : key === 'osm' ? 'OpenStreetMap' : key;
export const formatNumber = (value: number | null) => value === null ? 'Necunoscut' : value.toLocaleString('ro-RO', { maximumFractionDigits: 2 });
export function formatTimestamp(value: string | null | undefined) {
  if (!value) return 'Nedisponibil în răspuns';
  const date = new Date(value);
  return Number.isNaN(date.valueOf()) ? 'Valoare temporală nevalidă în răspuns' : date.toLocaleString('ro-RO', { dateStyle: 'medium', timeStyle: 'short', timeZone: 'UTC' }) + ' UTC';
}
export interface PresentedError { title: string; detail: string; requestId?: string; fields?: { field: string; reason: string }[] }
const apiErrorLabels: Record<string, string> = {
  unknown_neighborhood: 'Zona selectată nu este disponibilă în catalogul SIM.',
  study_area_rejected: 'Zona nu a putut fi analizată cu datele disponibile.',
  spatial_failure: 'Motorul de analiză a întâmpinat o eroare.',
  spatial_unavailable: 'Motorul de analiză nu este disponibil momentan.',
  spatial_timeout: 'Analiza a depășit timpul disponibil.',
  validation_error: 'Cererea nu corespunde datelor așteptate de API.',
  invalid_request: 'Cererea nu a fost acceptată de API.',
  unknown_resource: 'Resursa solicitată nu mai este disponibilă.',
  incompatible_scenario: 'Scenariul nu mai corespunde analizei curente.',
  capacity_unavailable: 'Capacitatea serviciului este temporar indisponibilă.',
  storage_unavailable: 'Stocarea serviciului este temporar indisponibilă.',
  sumo_unavailable: 'Simulatorul SUMO nu este disponibil pentru această cerere.',
  invalid_area: 'Zona selectată nu a fost acceptată.',
};
export function presentError(cause: unknown): PresentedError {
  if (cause instanceof ApiTimeoutError) return { title: 'Serviciul nu a răspuns în intervalul disponibil.', detail: cause.message };
  if (cause instanceof ApiError) {
    const code = cause.body?.error.code;
    return { title: code ? apiErrorLabels[code] ?? 'API-ul nu a putut procesa cererea.' : `Serviciul a răspuns cu eroarea HTTP ${cause.status}.`, detail: cause.body?.error.message ?? cause.message, requestId: cause.body?.error.request_id, fields: cause.body?.error.details };
  }
  if (cause instanceof ApiContractError) return { title: 'Răspunsul serviciului nu respectă contractul API. Nu am afișat rezultate.', detail: cause.message };
  if (cause instanceof TypeError) return { title: 'Nu am putut contacta serviciul API.', detail: cause.message };
  return { title: 'Cererea nu a putut fi finalizată.', detail: cause instanceof Error ? cause.message : 'Eroare necunoscută.' };
}
