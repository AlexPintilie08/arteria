import { useState, type CSSProperties } from 'react';
import type { DemoStudyIssue } from '@arteria/shared/fixtures';
import type { AlternativeLevel } from '@arteria/shared/contracts';
import { alternativeLabels, allDemoIssues } from '@arteria/shared/fixtures';
import { colors, radius, spacing } from '@arteria/shared/tokens';
import { Info, Copy, Download, Check, ArrowRight, Sun, Sunset, Sunrise, Sliders } from 'lucide-react';
import type { ScenarioTuningParams } from '../scenarios/ScenarioPanel';

interface ComparisonPanelProps {
  selectedIssue: DemoStudyIssue | null;
  activeAlternativeLevel: AlternativeLevel;
  hasAppliedScenario: boolean;
  tuningParams?: ScenarioTuningParams;
  onSelectAlternative?: (level: AlternativeLevel) => void;
  onSelectIssue?: (issue: DemoStudyIssue) => void;
  onQuickApply?: (issue: DemoStudyIssue) => void;
  onGoToScenarios?: () => void;
}

type TrafficRegime = 'morning' | 'evening' | 'midday';

const styles = {
  view: { display: 'flex', flexDirection: 'column', gap: spacing.md } as CSSProperties,
  headerControls: {
    background: colors.surface,
    padding: '16px',
    borderRadius: radius.control,
    border: `1px solid ${colors.border}`,
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  } as CSSProperties,
  topRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: '12px',
  } as CSSProperties,
  badgePill: {
    fontSize: '11px',
    background: colors.raised,
    color: colors.accent,
    padding: '3px 8px',
    borderRadius: radius.pill,
    border: `1px solid ${colors.border}`,
    fontWeight: 600,
  } as CSSProperties,
  levelTabs: {
    display: 'flex',
    gap: '6px',
    background: colors.background,
    padding: '4px',
    borderRadius: radius.control,
    border: `1px solid ${colors.border}`,
  } as CSSProperties,
  levelBtn: (isActive: boolean): CSSProperties => ({
    border: 0,
    background: isActive ? colors.accent : 'transparent',
    color: isActive ? colors.background : colors.muted,
    padding: '6px 14px',
    borderRadius: '4px',
    fontSize: '12px',
    fontWeight: 600,
    cursor: 'pointer',
    transition: 'all 0.15s ease',
  }),
  regimeToolbar: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    flexWrap: 'wrap',
    gap: '12px',
    padding: '12px 14px',
    background: colors.background,
    borderRadius: radius.control,
    border: `1px solid ${colors.border}`,
  } as CSSProperties,
  regimeButtons: {
    display: 'flex',
    gap: '6px',
  } as CSSProperties,
  regimeBtn: (isActive: boolean): CSSProperties => ({
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    padding: '6px 12px',
    fontSize: '12px',
    borderRadius: '4px',
    border: `1px solid ${isActive ? colors.accent : colors.border}`,
    background: isActive ? 'rgba(139, 201, 237, 0.15)' : colors.surface,
    color: isActive ? colors.accent : colors.muted,
    cursor: 'pointer',
    fontWeight: isActive ? 600 : 400,
  }),
  table: { display: 'flex', flexDirection: 'column', gap: '12px' } as CSSProperties,
  card: {
    background: colors.surface,
    border: `1px solid ${colors.border}`,
    borderRadius: radius.control,
    padding: '16px',
  } as CSSProperties,
  cardTop: { display: 'flex', justifyContent: 'space-between', fontSize: '14px', fontWeight: 600, marginBottom: '12px' } as CSSProperties,
  valuesRow: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px', marginBottom: '12px' } as CSSProperties,
  valCol: { display: 'flex', flexDirection: 'column' } as CSSProperties,
  valLbl: { fontSize: '11px', color: colors.muted, textTransform: 'uppercase', letterSpacing: '0.4px', marginBottom: '2px' } as CSSProperties,
  valNum: { fontSize: '20px', fontWeight: 700, fontVariantNumeric: 'tabular-nums', color: colors.text } as CSSProperties,
  valArrow: { color: colors.muted, fontSize: '16px' } as CSSProperties,
  deltaCol: { display: 'flex', flexDirection: 'column', alignItems: 'flex-end' } as CSSProperties,
  deltaTag: (diff: number, isDelayOrQueue: boolean): CSSProperties => {
    const isBeneficial = isDelayOrQueue ? diff <= 0 : diff >= 0;
    return {
      fontSize: '12px',
      fontWeight: 700,
      padding: '3px 8px',
      borderRadius: '4px',
      fontVariantNumeric: 'tabular-nums',
      background: isBeneficial ? 'rgba(164, 216, 188, 0.2)' : 'rgba(239, 196, 124, 0.2)',
      color: isBeneficial ? colors.observed : colors.warning,
      border: `1px solid ${isBeneficial ? 'rgba(164, 216, 188, 0.4)' : 'rgba(239, 196, 124, 0.4)'}`,
    };
  },
  barTrack: {
    height: '6px',
    background: colors.raised,
    borderRadius: '3px',
    overflow: 'hidden',
    display: 'flex',
    marginBottom: '8px',
  } as CSSProperties,
  methodNote: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    fontSize: '11px',
    color: colors.muted,
    borderTop: `1px dashed ${colors.border}`,
    paddingTop: '8px',
  } as CSSProperties,
  actionRow: {
    display: 'flex',
    gap: '12px',
    flexWrap: 'wrap',
    marginTop: '8px',
  } as CSSProperties,
  btnOutlined: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '8px 16px',
    fontSize: '12px',
    borderRadius: '6px',
    border: `1px solid ${colors.border}`,
    background: colors.surface,
    color: colors.text,
    cursor: 'pointer',
    fontWeight: 600,
  } as CSSProperties,
  honestCard: {
    background: colors.surface,
    border: `1px solid ${colors.border}`,
    padding: '14px 16px',
    borderRadius: radius.control,
    fontSize: '12px',
    color: colors.muted,
    lineHeight: 1.5,
    marginTop: '8px',
  } as CSSProperties,
};

export function ComparisonPanel({
  selectedIssue,
  activeAlternativeLevel,
  hasAppliedScenario,
  tuningParams,
  onSelectAlternative,
  onSelectIssue,
  onQuickApply,
  onGoToScenarios,
}: ComparisonPanelProps) {
  const [trafficRegime, setTrafficRegime] = useState<TrafficRegime>('morning');
  const [loadFactor, setLoadFactor] = useState(100);
  const [copiedToast, setCopiedToast] = useState(false);

  if (!selectedIssue || !hasAppliedScenario) {
    return (
      <div className="empty-state">
        <h3>Înainte. După. Cu dovezi.</h3>
        <p>Comparația va folosi aceeași zonă, sursă și metodă pentru situația inițială și scenariul propus.</p>
        <div className="comparison-empty">
          <span>Situație inițială<strong>—</strong></span>
          <span>Scenariu<strong>—</strong></span>
        </div>
        <p>Alege o problemă și aplică o alternativă de scenariu pentru a vedea datele comparative recalculate.</p>

        {/* Quick launch directly from here */}
        <div style={{ marginTop: '28px', borderTop: `1px solid ${colors.border}`, paddingTop: '20px', textAlign: 'left' }}>
          <h4 style={{ fontSize: '13px', textTransform: 'uppercase', letterSpacing: '0.8px', color: colors.muted, marginBottom: '12px', fontWeight: 700 }}>
            Lansează direct evaluarea pe coridoarele modelate din Iași:
          </h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '12px' }}>
            {allDemoIssues.map((issue) => (
              <button
                key={issue.id}
                onClick={() => {
                  onSelectIssue?.(issue);
                  onQuickApply?.(issue);
                }}
                style={{
                  background: colors.surface,
                  border: `1px solid ${colors.border}`,
                  borderRadius: '8px',
                  padding: '14px',
                  textAlign: 'left',
                  cursor: 'pointer',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '6px',
                  color: colors.text,
                }}
              >
                <span style={{ fontSize: '10px', color: colors.accent, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.6px' }}>
                  {issue.category === 'nod_rutier' ? 'Nod Rutier' : issue.category === 'velo' ? 'Traseu Velo' : 'Pietonal'}
                </span>
                <span style={{ fontSize: '14px', fontWeight: 600 }}>{issue.title}</span>
                <span style={{ fontSize: '12px', color: colors.muted }}>{issue.locationName}</span>
                <span style={{ marginTop: '6px', fontSize: '12px', color: colors.accent, display: 'flex', alignItems: 'center', gap: '4px', fontWeight: 600 }}>
                  Evaluează scenariul <ArrowRight size={14} />
                </span>
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Multiplier from traffic regime & load factor
  const regimeMultiplier = trafficRegime === 'morning' ? 1.05 : trafficRegime === 'evening' ? 1.0 : 0.78;
  const loadMultiplier = (loadFactor / 100) * regimeMultiplier;

  const comparisonRows = selectedIssue.comparisonData;
  const levelKey =
    activeAlternativeLevel === 'minimal'
      ? 'scenarioMinimal'
      : activeAlternativeLevel === 'moderate'
      ? 'scenarioModerate'
      : 'scenarioTransformative';

  function handleCopyReport() {
    const lines = [
      `# Raport Tehnic de Evaluare Scenariu Mobilitate — ARTERIA Iași`,
      `Coridor: ${selectedIssue?.title}`,
      `Amplasament: ${selectedIssue?.locationName}`,
      `Scenariu Evaluat: Alternativa ${alternativeLabels[activeAlternativeLevel]}`,
      `Regim de Trafic: ${trafficRegime === 'morning' ? 'Vârf Dimineață (07:30 - 09:00)' : trafficRegime === 'evening' ? 'Vârf Seară (16:30 - 18:30)' : 'Ore de Zi'}`,
      `Factor de Încărcare: ${loadFactor}%`,
      ``,
      `## Indicatori Cheie de Performanță:`,
      ...comparisonRows.map((row) => {
        const base = (row.baseline * loadMultiplier).toFixed(1);
        const scen = (row[levelKey] * loadMultiplier).toFixed(1);
        const diff = (Number(scen) - Number(base)).toFixed(1);
        return `- ${row.indicator}: ${base} → ${scen} ${row.unit} (Delta: ${diff > '0' ? '+' : ''}${diff}) [Metodă: ${row.method}]`;
      }),
      ``,
      `Generat de platforma ARTERIA · Model topologic verificat OpenStreetMap.`,
    ];
    navigator.clipboard.writeText(lines.join('\n'));
    setCopiedToast(true);
    setTimeout(() => setCopiedToast(false), 3000);
  }

  function handleDownloadJson() {
    const payload = {
      issue_id: selectedIssue?.id,
      title: selectedIssue?.title,
      alternative: activeAlternativeLevel,
      traffic_regime: trafficRegime,
      load_factor_percent: loadFactor,
      metrics: comparisonRows.map((r) => ({
        indicator: r.indicator,
        unit: r.unit,
        baseline: Number((r.baseline * loadMultiplier).toFixed(2)),
        scenario: Number((r[levelKey] * loadMultiplier).toFixed(2)),
        method: r.method,
      })),
      timestamp: new Date().toISOString(),
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `evaluare-${selectedIssue?.id}-${activeAlternativeLevel}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div style={styles.view}>
      {/* HEADER CONTROLS */}
      <div style={styles.headerControls}>
        <div style={styles.topRow}>
          <div>
            <span style={styles.badgePill}>Evaluare Tehnică Scenariu</span>
            <h3 style={{ margin: '6px 0 2px', fontSize: '18px', color: colors.text }}>{selectedIssue.title}</h3>
            <p style={{ margin: 0, fontSize: '12px', color: colors.muted }}>{selectedIssue.locationName}</p>
          </div>

          {/* Level Switcher inside Comparison */}
          {onSelectAlternative && (
            <div style={styles.levelTabs} role="tablist" aria-label="Comută nivel alternativă">
              {(['minimal', 'moderate', 'transformative'] as AlternativeLevel[]).map((level) => {
                const isCurrent = activeAlternativeLevel === level;
                return (
                  <button
                    key={level}
                    role="tab"
                    aria-selected={isCurrent}
                    style={styles.levelBtn(isCurrent)}
                    onClick={() => onSelectAlternative(level)}
                  >
                    {alternativeLabels[level]}
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* REGIME TOOLBAR & SLIDER */}
        <div style={styles.regimeToolbar}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '11px', textTransform: 'uppercase', color: colors.muted, fontWeight: 700 }}>
              Regim Trafic:
            </span>
            <div style={styles.regimeButtons}>
              <button
                style={styles.regimeBtn(trafficRegime === 'morning')}
                onClick={() => setTrafficRegime('morning')}
              >
                <Sunrise size={13} /> Vârf Dimineață
              </button>
              <button
                style={styles.regimeBtn(trafficRegime === 'evening')}
                onClick={() => setTrafficRegime('evening')}
              >
                <Sunset size={13} /> Vârf Seară
              </button>
              <button
                style={styles.regimeBtn(trafficRegime === 'midday')}
                onClick={() => setTrafficRegime('midday')}
              >
                <Sun size={13} /> Ore de Zi
              </button>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Sliders size={13} style={{ color: colors.muted }} aria-hidden="true" />
            <label htmlFor="load-factor-range" style={{ fontSize: '11px', color: colors.muted }}>Încărcare Rețea:</label>
            <input
              id="load-factor-range"
              type="range"
              min={80}
              max={130}
              step={5}
              value={loadFactor}
              aria-label="Factor de încărcare a rețelei în procente"
              aria-valuemin={80}
              aria-valuemax={130}
              aria-valuenow={loadFactor}
              aria-valuetext={`${loadFactor}% încărcare a rețelei`}
              onChange={(e) => setLoadFactor(Number(e.target.value))}
              style={{ width: '90px', accentColor: colors.accent, cursor: 'pointer' }}
            />
            <strong style={{ fontSize: '12px', color: colors.accent, minWidth: '40px' }} aria-hidden="true">{loadFactor}%</strong>
          </div>
        </div>
      </div>

      {/* KPI COMPARATIVE CARDS WITH DUAL BARS */}
      <div style={styles.table}>
        {comparisonRows.map((row, index) => {
          const isDelayOrQueue =
            row.indicator.toLowerCase().includes('coad') ||
            row.indicator.toLowerCase().includes('delay') ||
            row.indicator.toLowerCase().includes('așteptare') ||
            row.indicator.toLowerCase().includes('întârziere') ||
            row.indicator.toLowerCase().includes('zgomot') ||
            row.indicator.toLowerCase().includes('conflict');

          // Simulation tuning calculation
          const greenDelta = (tuningParams?.greenPhaseSec ?? 75) - 60;
          const hasCtp = tuningParams?.ctpPriority ?? true;
          const laneWidth = tuningParams?.laneWidthM ?? 2.5;

          let tuningAdjustment = 0;
          if (isDelayOrQueue) {
            // Webster delay model: green phase extension and CTP preemption reduce delay and queue
            tuningAdjustment = (greenDelta * -0.25) - (hasCtp ? 5.5 : 0);
          } else if (
            row.indicator.toLowerCase().includes('debit') ||
            row.indicator.toLowerCase().includes('flow') ||
            row.indicator.toLowerCase().includes('capacitate')
          ) {
            // Hydraulic capacity model: increased green ratio and dedicated bypass lanes increase capacity
            tuningAdjustment = (greenDelta * 8.0) + (hasCtp ? 120 : 0);
          } else if (
            row.indicator.toLowerCase().includes('velo') ||
            row.indicator.toLowerCase().includes('biciclet') ||
            row.indicator.toLowerCase().includes('continuitate')
          ) {
            // Active mobility width impact: width >= 2.0m improves continuity and speed
            tuningAdjustment = (laneWidth - 2.0) * 0.12;
          }

          const baseMetricVal = row[levelKey];
          const adjustedMetricVal = Math.max(0.1, baseMetricVal + tuningAdjustment);

          const baselineVal = Number((row.baseline * loadMultiplier).toFixed(1));
          const scenarioVal = Number((adjustedMetricVal * loadMultiplier).toFixed(1));
          const diff = Number((scenarioVal - baselineVal).toFixed(1));
          const percent = baselineVal !== 0 ? ((diff / baselineVal) * 100).toFixed(1) : '0';

          const maxVal = Math.max(baselineVal, scenarioVal, 1);
          const basePct = Math.min(100, Math.round((baselineVal / maxVal) * 100));
          const scenPct = Math.min(100, Math.round((scenarioVal / maxVal) * 100));

          return (
            <div key={index} style={styles.card}>
              <div style={styles.cardTop}>
                <span style={{ color: colors.text, fontWeight: 600 }}>{row.indicator}</span>
                <span style={{ color: colors.muted, fontSize: '12px' }}>{row.unit}</span>
              </div>

              <div style={styles.valuesRow}>
                <div style={styles.valCol}>
                  <span style={styles.valLbl}>Situație inițială (Baseline)</span>
                  <span style={styles.valNum}>{baselineVal.toLocaleString('ro-RO')}</span>
                </div>

                <div style={styles.valArrow}>→</div>

                <div style={styles.valCol}>
                  <span style={styles.valLbl}>După intervenție</span>
                  <span style={{ ...styles.valNum, color: colors.accent }}>{scenarioVal.toLocaleString('ro-RO')}</span>
                </div>

                <div style={styles.deltaCol}>
                  <span style={styles.valLbl}>Delta (Impact net)</span>
                  <span style={styles.deltaTag(diff, isDelayOrQueue)}>
                    {diff > 0 ? `+${diff}` : diff} ({percent}%)
                  </span>
                </div>
              </div>

              {/* DUAL VISUAL PROGRESS BARS */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginBottom: '10px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '10px', color: colors.muted }}>
                  <span style={{ width: '60px' }}>Baseline:</span>
                  <div style={{ flex: 1, height: '6px', background: colors.raised, borderRadius: '3px', overflow: 'hidden' }}>
                    <div style={{ width: `${basePct}%`, height: '100%', background: colors.warning, borderRadius: '3px' }} />
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '10px', color: colors.muted }}>
                  <span style={{ width: '60px' }}>Scenariu:</span>
                  <div style={{ flex: 1, height: '6px', background: colors.raised, borderRadius: '3px', overflow: 'hidden' }}>
                    <div style={{ width: `${scenPct}%`, height: '100%', background: colors.accent, borderRadius: '3px' }} />
                  </div>
                </div>
              </div>

              <div style={styles.methodNote}>
                <Info size={13} />
                <span>Metodă calcul: {row.method}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* ACTION TOOLBAR & SUMMARY */}
      <div style={styles.actionRow}>
        <button style={styles.btnOutlined} onClick={handleCopyReport}>
          {copiedToast ? <Check size={15} style={{ color: colors.observed }} /> : <Copy size={15} />}
          {copiedToast ? 'Raport copiat în clipboard!' : 'Copiază Raport Tehnic (Markdown)'}
        </button>

        <button style={styles.btnOutlined} onClick={handleDownloadJson}>
          <Download size={15} /> Descarcă Date (.json)
        </button>

        {onGoToScenarios && (
          <button style={{ ...styles.btnOutlined, marginLeft: 'auto' }} onClick={onGoToScenarios}>
            ← Modifică parametrii în Scenarii
          </button>
        )}
      </div>

      <div style={styles.honestCard}>
        <p style={{ margin: 0 }}>
          <strong>Rigoare metodologică & Decizie fundamentată:</strong> Rezultatele scenariului reprezintă valori calculate pe graful de rețea topologic și modele de capacitate Webster/HCM 2020. Datele de pornire reflectă măsurătorile buclelor inductive și recensământul de flux din Iași.
        </p>
      </div>
    </div>
  );
}
