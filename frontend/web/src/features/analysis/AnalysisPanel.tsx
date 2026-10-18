import type { CSSProperties } from 'react';
import { EvidenceBadge } from '../../components/EvidenceBadge';
import type { AnalyzeResponse } from '@arteria/shared/contracts';
import { demoIssuesByNeighborhood, type DemoStudyIssue } from '@arteria/shared/fixtures';
import { colors, radius, spacing } from '@arteria/shared/tokens';
import { ChevronRight, CheckCircle2 } from 'lucide-react';

interface AnalysisPanelProps {
  result: AnalyzeResponse | null;
  selectedNeighborhoodId: string;
  selectedIssueId: string | null;
  onSelectIssue: (issue: DemoStudyIssue) => void;
  onGoToScenarios: () => void;
}

const styles = {
  container: { display: 'flex', flexDirection: 'column', gap: spacing.md } as CSSProperties,
  sectionBlock: { borderBottom: `1px solid ${colors.border}`, paddingBottom: spacing.md } as CSSProperties,
  sectionTitle: {
    fontSize: '13px',
    textTransform: 'uppercase',
    letterSpacing: '0.8px',
    color: colors.muted,
    marginBottom: spacing.sm,
    fontWeight: 600,
  } as CSSProperties,
  headerRow: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: spacing.sm } as CSSProperties,
  badgePill: {
    fontSize: '11px',
    background: colors.raised,
    color: colors.accent,
    padding: '3px 8px',
    borderRadius: radius.pill,
    border: `1px solid ${colors.border}`,
    fontWeight: 600,
  } as CSSProperties,
  issuesList: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: spacing.sm } as CSSProperties,
  issueCard: (isSelected: boolean): CSSProperties => ({
    background: isSelected ? 'rgba(139, 201, 237, 0.08)' : colors.background,
    border: `1px solid ${isSelected ? colors.accent : colors.border}`,
    borderRadius: radius.control,
    padding: '12px 14px',
    cursor: 'pointer',
    boxShadow: isSelected ? `0 0 0 1px ${colors.accent}` : 'none',
    transition: 'border-color 0.15s ease, background 0.15s ease',
  }),
  issueHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: spacing.xs } as CSSProperties,
  issueTag: (category: string): CSSProperties => ({
    fontSize: '10px',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
    padding: '2px 6px',
    borderRadius: '4px',
    fontWeight: 700,
    background:
      category === 'velo'
        ? 'rgba(164, 216, 188, 0.18)'
        : category === 'pietonal'
        ? 'rgba(139, 201, 237, 0.18)'
        : 'rgba(239, 196, 124, 0.18)',
    color: category === 'velo' ? colors.observed : category === 'pietonal' ? colors.calculated : colors.warning,
  }),
  selectedIndicator: {
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
    fontSize: '11px',
    color: colors.accent,
    fontWeight: 600,
  } as CSSProperties,
  issueTitle: { fontSize: '14px', fontWeight: 600, color: colors.text, marginBottom: '2px' } as CSSProperties,
  issueLocation: { fontSize: '12px', color: colors.accent, marginBottom: spacing.xs } as CSSProperties,
  issueDesc: { fontSize: '12px', color: colors.muted, lineHeight: 1.45 } as CSSProperties,
};

export function AnalysisPanel({
  result,
  selectedNeighborhoodId,
  selectedIssueId,
  onSelectIssue,
  onGoToScenarios,
}: AnalysisPanelProps) {
  if (!result) return (
    <div className="empty-state">
      <h3>Începe cu o zonă.</h3>
      <p>Alege un cartier și solicită analiza. Indicatorii vor apărea împreună cu sursa și limitele datelor.</p>
    </div>
  );

  const localIssues = demoIssuesByNeighborhood[selectedNeighborhoodId] || [];

  return (
    <div style={styles.container}>
      {result.warnings.map((warning) => (
        <p className="notice" key={warning}>{warning}</p>
      ))}

      <div style={styles.sectionBlock}>
        <h3 style={styles.sectionTitle}>Indicatori de mobilitate</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '12px' }}>
          {result.indicators.map((indicator) => (
            <article className="indicator" key={indicator.id} style={{ border: `1px solid ${colors.border}`, borderRadius: radius.control, padding: '14px', background: colors.background }}>
              <div className="indicator-heading">
                <h3>{indicator.label}</h3>
                <EvidenceBadge status={indicator.status} />
              </div>
              <p className="indicator-value">
                {indicator.value === null ? '—' : indicator.value.toLocaleString('ro-RO')} <small>{indicator.unit}</small>
              </p>
              <details>
                <summary>Surse și limite</summary>
                <p>{indicator.uncertainty.description}</p>
                {indicator.provenance.map((source, index) => (
                  <p key={index}>
                    {source.source} · {source.source_version}<br />
                    Metodă: {source.method}<br />
                    Preluat: {source.retrieved_at} · {source.crs}
                  </p>
                ))}
              </details>
            </article>
          ))}
        </div>
      </div>

      {/* TELEMETRIE DIRECTĂ CORIDOR IAȘI */}
      <div style={{ ...styles.sectionBlock, marginTop: '8px' }}>
        <div style={styles.headerRow}>
          <h3 style={{ ...styles.sectionTitle, margin: 0 }}>Telemetrie demonstrativă sintetică</h3>
          <span style={{ ...styles.badgePill, color: colors.observed, borderColor: 'rgba(164, 216, 188, 0.4)' }}>Exemple sintetice</span>
        </div>
        <p className="supporting" style={{ marginTop: 0, marginBottom: '10px' }}>
          Valori ilustrative din fixture-uri; nu provin din senzori, recensăminte sau observații de trafic din Iași:
        </p>
        <div
          style={{
            background: colors.background,
            border: `1px solid ${colors.border}`,
            borderRadius: radius.control,
            padding: '12px 14px',
            display: 'grid',
            gridTemplateColumns: 'repeat(2, 1fr)',
            gap: '10px',
          }}
        >
          {selectedNeighborhoodId === 'podu-ros' && (
            <>
              <div>
                <span style={{ fontSize: '10px', color: colors.muted, textTransform: 'uppercase' }}>Debit vârf Socola:</span>
                <div style={{ fontSize: '16px', fontWeight: 700, color: colors.accent }}>2.180 <small style={{ fontSize: '11px', color: colors.muted }}>veh/h</small></div>
              </div>
              <div>
                <span style={{ fontSize: '10px', color: colors.muted, textTransform: 'uppercase' }}>Coadă maximă:</span>
                <div style={{ fontSize: '16px', fontWeight: 700, color: colors.warning }}>340 <small style={{ fontSize: '11px', color: colors.muted }}>metri</small></div>
              </div>
              <div>
                <span style={{ fontSize: '10px', color: colors.muted, textTransform: 'uppercase' }}>Întârziere medie:</span>
                <div style={{ fontSize: '16px', fontWeight: 700, color: colors.danger }}>74.2 <small style={{ fontSize: '11px', color: colors.muted }}>secunde</small></div>
              </div>
              <div>
                <span style={{ fontSize: '10px', color: colors.muted, textTransform: 'uppercase' }}>Nivel de Serviciu:</span>
                <div style={{ fontSize: '16px', fontWeight: 700, color: colors.danger }}>LOS E/F <small style={{ fontSize: '11px', color: colors.muted }}>critic</small></div>
              </div>
            </>
          )}
          {selectedNeighborhoodId === 'copou' && (
            <>
              <div>
                <span style={{ fontSize: '10px', color: colors.muted, textTransform: 'uppercase' }}>Debit Carol I:</span>
                <div style={{ fontSize: '16px', fontWeight: 700, color: colors.accent }}>1.420 <small style={{ fontSize: '11px', color: colors.muted }}>veh/h</small></div>
              </div>
              <div>
                <span style={{ fontSize: '10px', color: colors.muted, textTransform: 'uppercase' }}>Viteză medie velo:</span>
                <div style={{ fontSize: '16px', fontWeight: 700, color: colors.warning }}>11.2 <small style={{ fontSize: '11px', color: colors.muted }}>km/h</small></div>
              </div>
              <div>
                <span style={{ fontSize: '10px', color: colors.muted, textTransform: 'uppercase' }}>Conflicte pieton/velo:</span>
                <div style={{ fontSize: '16px', fontWeight: 700, color: colors.danger }}>14 <small style={{ fontSize: '11px', color: colors.muted }}>pct/km</small></div>
              </div>
              <div>
                <span style={{ fontSize: '10px', color: colors.muted, textTransform: 'uppercase' }}>Acces verde 5 min:</span>
                <div style={{ fontSize: '16px', fontWeight: 700, color: colors.observed }}>64% <small style={{ fontSize: '11px', color: colors.muted }}>populație</small></div>
              </div>
            </>
          )}
          {selectedNeighborhoodId === 'centru' && (
            <>
              <div>
                <span style={{ fontSize: '10px', color: colors.muted, textTransform: 'uppercase' }}>Întârziere vehicul:</span>
                <div style={{ fontSize: '16px', fontWeight: 700, color: colors.danger }}>68.0 <small style={{ fontSize: '11px', color: colors.muted }}>secunde</small></div>
              </div>
              <div>
                <span style={{ fontSize: '10px', color: colors.muted, textTransform: 'uppercase' }}>Viteză tramvai:</span>
                <div style={{ fontSize: '16px', fontWeight: 700, color: colors.warning }}>9.8 <small style={{ fontSize: '11px', color: colors.muted }}>km/h</small></div>
              </div>
              <div>
                <span style={{ fontSize: '10px', color: colors.muted, textTransform: 'uppercase' }}>Zgomot fațadă Leq:</span>
                <div style={{ fontSize: '16px', fontWeight: 700, color: colors.text }}>74.0 <small style={{ fontSize: '11px', color: colors.muted }}>dB(A)</small></div>
              </div>
              <div>
                <span style={{ fontSize: '10px', color: colors.muted, textTransform: 'uppercase' }}>Flux pietonal Palas:</span>
                <div style={{ fontSize: '16px', fontWeight: 700, color: colors.observed }}>3.200 <small style={{ fontSize: '11px', color: colors.muted }}>pietoni/h</small></div>
              </div>
            </>
          )}
          {selectedNeighborhoodId === 'tatarasi' && (
            <>
              <div>
                <span style={{ fontSize: '10px', color: colors.muted, textTransform: 'uppercase' }}>Coadă Han Tătar:</span>
                <div style={{ fontSize: '16px', fontWeight: 700, color: colors.danger }}>240 <small style={{ fontSize: '11px', color: colors.muted }}>metri</small></div>
              </div>
              <div>
                <span style={{ fontSize: '10px', color: colors.muted, textTransform: 'uppercase' }}>Emisii CO2 nod:</span>
                <div style={{ fontSize: '16px', fontWeight: 700, color: colors.warning }}>185 <small style={{ fontSize: '11px', color: colors.muted }}>kg/h</small></div>
              </div>
              <div>
                <span style={{ fontSize: '10px', color: colors.muted, textTransform: 'uppercase' }}>Acces pietonal spital:</span>
                <div style={{ fontSize: '16px', fontWeight: 700, color: colors.text }}>42/100 <small style={{ fontSize: '11px', color: colors.muted }}>scor</small></div>
              </div>
              <div>
                <span style={{ fontSize: '10px', color: colors.muted, textTransform: 'uppercase' }}>Descărcare orară:</span>
                <div style={{ fontSize: '16px', fontWeight: 700, color: colors.accent }}>1.750 <small style={{ fontSize: '11px', color: colors.muted }}>veh/h</small></div>
              </div>
            </>
          )}
          {selectedNeighborhoodId === 'alexandru' && (
            <>
              <div>
                <span style={{ fontSize: '10px', color: colors.muted, textTransform: 'uppercase' }}>Timp velo spre centru:</span>
                <div style={{ fontSize: '16px', fontWeight: 700, color: colors.warning }}>24 <small style={{ fontSize: '11px', color: colors.muted }}>minute</small></div>
              </div>
              <div>
                <span style={{ fontSize: '10px', color: colors.muted, textTransform: 'uppercase' }}>Navetiști velo zilnici:</span>
                <div style={{ fontSize: '16px', fontWeight: 700, color: colors.text }}>320 <small style={{ fontSize: '11px', color: colors.muted }}>curse/zi</small></div>
              </div>
              <div>
                <span style={{ fontSize: '10px', color: colors.muted, textTransform: 'uppercase' }}>Zonă verde râu accesibilă:</span>
                <div style={{ fontSize: '16px', fontWeight: 700, color: colors.observed }}>1.4 <small style={{ fontSize: '11px', color: colors.muted }}>hectare</small></div>
              </div>
              <div>
                <span style={{ fontSize: '10px', color: colors.muted, textTransform: 'uppercase' }}>Lățime utilă dig:</span>
                <div style={{ fontSize: '16px', fontWeight: 700, color: colors.muted }}>1.8 <small style={{ fontSize: '11px', color: colors.muted }}>metri</small></div>
              </div>
            </>
          )}
        </div>
      </div>

      <div style={{ ...styles.sectionBlock, marginTop: '8px' }}>
        <div style={styles.headerRow}>
          <h3 style={{ ...styles.sectionTitle, margin: 0 }}>Probleme identificate în teritoriu</h3>
          <span style={styles.badgePill}>{localIssues.length} detectate</span>
        </div>
        <p className="supporting" style={{ marginTop: 0, marginBottom: '12px' }}>
          Probleme ilustrative din catalogul sintetic. Selectează un exemplu pentru a explora scenarii demonstrative; nu sunt constatări OSM validate.
        </p>

        <div style={styles.issuesList} role="list">
          {localIssues.map((issue) => {
            const isSelected = selectedIssueId === issue.id;
            return (
              <div
                key={issue.id}
                role="listitem"
                tabIndex={0}
                style={styles.issueCard(isSelected)}
                onClick={() => onSelectIssue(issue)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    onSelectIssue(issue);
                  }
                }}
              >
                <div style={styles.issueHeader}>
                  <span style={styles.issueTag(issue.category)}>
                    {issue.category === 'velo' ? 'Traseu Velo' : issue.category === 'pietonal' ? 'Pietonal' : 'Nod Rutier'}
                  </span>
                  {isSelected && (
                    <span style={styles.selectedIndicator}>
                      <CheckCircle2 size={15} /> Selectat
                    </span>
                  )}
                </div>
                <h4 style={styles.issueTitle}>{issue.title}</h4>
                <p style={styles.issueLocation}>{issue.locationName}</p>
                <p style={styles.issueDesc}>{issue.description}</p>
              </div>
            );
          })}
        </div>

        {selectedIssueId && (
          <div style={{ marginTop: '16px' }}>
            <button className="primary-button" style={{ width: '100%' }} onClick={onGoToScenarios}>
              Explorează propuneri pentru problema selectată <ChevronRight size={18} />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
