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
