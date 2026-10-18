import { useState, type CSSProperties } from 'react';
import { alternativeLabels, allDemoIssues, type DemoStudyIssue } from '@arteria/shared/fixtures';
import type { AlternativeLevel } from '@arteria/shared/contracts';
import { colors, radius, spacing } from '@arteria/shared/tokens';
import { Check, ShieldAlert, ArrowRight, Layers, Sparkles, SlidersHorizontal, Bus, Clock } from 'lucide-react';
import editorStyles from './ConnectedInterventionEditor.module.css';

export interface ScenarioTuningParams {
  greenPhaseSec: number;
  ctpPriority: boolean;
  laneWidthM: number;
}

interface ScenarioPanelProps {
  selectedIssue: DemoStudyIssue | null;
  activeAlternativeLevel: AlternativeLevel;
  onSelectAlternative: (level: AlternativeLevel) => void;
  onApplyScenario: (params?: ScenarioTuningParams) => void;
  hasAppliedScenario: boolean;
  onSelectIssue?: (issue: DemoStudyIssue) => void;
  tuningParams?: ScenarioTuningParams;
  onUpdateTuningParams?: (params: ScenarioTuningParams) => void;
}

const styles = {
  view: { display: 'flex', flexDirection: 'column', gap: spacing.md } as CSSProperties,
  selectorHeader: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
    background: colors.surface,
    padding: '12px 14px',
    borderRadius: radius.control,
    border: `1px solid ${colors.border}`,
  } as CSSProperties,
  selectInput: {
    background: colors.background,
    color: colors.text,
    border: `1px solid ${colors.border}`,
    borderRadius: '6px',
    padding: '8px 10px',
    fontSize: '13px',
    width: '100%',
    cursor: 'pointer',
    fontFamily: 'inherit',
  } as CSSProperties,
  targetIssue: {
    background: colors.background,
    borderLeft: `3px solid ${colors.accent}`,
    padding: '12px 14px',
    borderRadius: `0 ${radius.control}px ${radius.control}px 0`,
    borderTop: `1px solid ${colors.border}`,
    borderRight: `1px solid ${colors.border}`,
    borderBottom: `1px solid ${colors.border}`,
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
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: '6px',
    background: colors.background,
    padding: '4px',
    borderRadius: radius.control,
    border: `1px solid ${colors.border}`,
  } as CSSProperties,
  levelTab: (isActive: boolean): CSSProperties => ({
    border: 0,
    background: isActive ? colors.raised : 'transparent',
    color: isActive ? colors.accent : colors.muted,
    padding: '8px 4px',
    borderRadius: '6px',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '2px',
    cursor: 'pointer',
    fontWeight: isActive ? 600 : 400,
    transition: 'background 0.15s ease, color 0.15s ease',
  }),
  proposalCard: {
    background: colors.background,
    border: `1px solid ${colors.border}`,
    borderRadius: radius.control,
    padding: '16px',
  } as CSSProperties,
  badgeRow: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '11px', marginBottom: '10px' } as CSSProperties,
  modelBadge: { display: 'flex', alignItems: 'center', gap: '6px', color: colors.accent, fontWeight: 600 } as CSSProperties,
  proposalSummary: { fontSize: '15px', fontWeight: 600, lineHeight: 1.4, marginBottom: '8px', color: colors.text } as CSSProperties,
  proposalRationale: { fontSize: '12px', color: colors.muted, lineHeight: 1.5, marginBottom: '14px' } as CSSProperties,
  blockHeader: { fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.5px', color: colors.muted, marginBottom: '6px', fontWeight: 700 } as CSSProperties,
  interventionsList: { listStyle: 'none', padding: 0, margin: '0 0 14px', display: 'flex', flexDirection: 'column', gap: '6px' } as CSSProperties,
  interventionItem: { fontSize: '12px', display: 'flex', alignItems: 'center', gap: '8px', color: colors.text } as CSSProperties,
  impactTags: { display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '14px' } as CSSProperties,
  impactPill: (positive: boolean): CSSProperties => ({
    fontSize: '11px',
    padding: '3px 8px',
    borderRadius: '4px',
    background: positive ? 'rgba(164, 216, 188, 0.15)' : 'rgba(239, 196, 124, 0.15)',
    color: positive ? colors.observed : colors.warning,
    border: `1px solid ${positive ? 'rgba(164, 216, 188, 0.3)' : 'rgba(239, 196, 124, 0.3)'}`,
  }),
  tuningSection: {
    background: colors.surface,
    border: `1px solid ${colors.border}`,
    borderRadius: radius.control,
    padding: '14px',
    marginTop: '14px',
    marginBottom: '14px',
  } as CSSProperties,
  tuningRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '10px',
  } as CSSProperties,
  tuningLabel: {
    fontSize: '12px',
    color: colors.text,
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
  } as CSSProperties,
  tuningValue: {
    fontSize: '12px',
    fontWeight: 700,
    color: colors.accent,
    fontVariantNumeric: 'tabular-nums',
  } as CSSProperties,
  sliderInput: {
    width: '100%',
    cursor: 'pointer',
    accentColor: colors.accent,
  } as CSSProperties,
  liveFeedbackBox: {
    background: 'rgba(139, 201, 237, 0.08)',
    border: `1px solid rgba(139, 201, 237, 0.3)`,
    borderRadius: '6px',
    padding: '10px 12px',
    fontSize: '11px',
    color: colors.text,
    lineHeight: 1.45,
    marginTop: '10px',
  } as CSSProperties,
  validationNote: {
    display: 'flex',
    gap: '8px',
    alignItems: 'flex-start',
    fontSize: '11px',
    color: colors.muted,
    background: colors.surface,
    padding: '8px 10px',
    borderRadius: '6px',
    border: `1px solid ${colors.border}`,
  } as CSSProperties,
};

export function ScenarioPanel({
  selectedIssue,
  activeAlternativeLevel,
  onSelectAlternative,
  onApplyScenario,
  hasAppliedScenario,
  onSelectIssue,
  tuningParams,
  onUpdateTuningParams,
}: ScenarioPanelProps) {
  const [internalParams, setInternalParams] = useState<ScenarioTuningParams>({
    greenPhaseSec: 75,
    ctpPriority: true,
    laneWidthM: 2.5,
  });

  const currentParams = tuningParams ?? internalParams;
  const greenPhaseSec = currentParams.greenPhaseSec;
  const ctpPriority = currentParams.ctpPriority;
  const laneWidthM = currentParams.laneWidthM;

  const updateParam = <K extends keyof ScenarioTuningParams>(key: K, value: ScenarioTuningParams[K]) => {
    const next = { ...currentParams, [key]: value };
    if (onUpdateTuningParams) {
      onUpdateTuningParams(next);
    } else {
      setInternalParams(next);
    }
  };

  const handleReset = () => {
    const defaultParams: ScenarioTuningParams = { greenPhaseSec: 75, ctpPriority: true, laneWidthM: 2.5 };
    if (onUpdateTuningParams) onUpdateTuningParams(defaultParams);
    else setInternalParams(defaultParams);
  };

  if (!selectedIssue) {
    return (
      <div className="empty-state">
        <h3>O schimbare, trei perspective.</h3>
        <p>Demo sintetic: selectează o problemă ilustrativă pentru a explora editorul și alternativele predefinite.</p>
        <ol className="alternatives">
          {Object.entries(alternativeLabels).map(([key, label]) => (
            <li key={key}>
              <strong>{label}</strong>
              <span>Disponibilă după selectarea unei probleme din analiză</span>
            </li>
          ))}
        </ol>
        <p>Valorile de exemplu și formulele locale nu reprezintă măsurători sau evaluări OSM, AI ori SUMO.</p>

        {/* Interactive Direct Corridor Selector */}
        <div style={{ marginTop: '24px', borderTop: `1px solid ${colors.border}`, paddingTop: '16px', textAlign: 'left' }}>
          <h4 style={{ fontSize: '13px', textTransform: 'uppercase', letterSpacing: '0.8px', color: colors.muted, marginBottom: '10px', fontWeight: 700 }}>
            Alege un coridor demonstrativ:
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {allDemoIssues.map((issue) => (
              <button
                key={issue.id}
                onClick={() => onSelectIssue?.(issue)}
                style={{
                  background: colors.surface,
                  border: `1px solid ${colors.border}`,
                  borderRadius: '6px',
                  padding: '10px 12px',
                  textAlign: 'left',
                  cursor: 'pointer',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  color: colors.text,
                  transition: 'border-color 0.15s ease',
                }}
              >
                <div>
                  <div style={{ fontSize: '13px', fontWeight: 600 }}>{issue.title}</div>
                  <div style={{ fontSize: '11px', color: colors.accent }}>{issue.locationName}</div>
                </div>
                <ArrowRight size={16} style={{ color: colors.accent, flexShrink: 0 }} />
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  }

  const activeProp = selectedIssue.proposals[activeAlternativeLevel];

  // Dynamic calculations based on slider parameters
  const calculatedDelayChange = Math.round(
    (greenPhaseSec - 60) * 0.4 + (ctpPriority ? 8 : 0) + (activeAlternativeLevel === 'transformative' ? 45 : activeAlternativeLevel === 'moderate' ? 24 : 12)
  );
  const calculatedFlowCapacity = Math.round(
    2180 + (greenPhaseSec - 60) * 12 + (ctpPriority ? 180 : 0) + (activeAlternativeLevel === 'transformative' ? 900 : activeAlternativeLevel === 'moderate' ? 450 : 150)
  );

  return (
    <div style={styles.view}>
      <p className="notice" role="status" style={{ margin: 0 }}>Demo sintetic: propuneri predefinite și formule ilustrative. AI cloud indisponibil; nicio rulare SUMO.</p>
      {/* Switcher dropdown */}
      <div style={styles.selectorHeader}>
        <label htmlFor="corridor-select" style={{ fontSize: '11px', color: colors.muted, textTransform: 'uppercase', letterSpacing: '0.6px', fontWeight: 600 }}>
          Coridor / Problemă activă
        </label>
        <select
          id="corridor-select"
          style={styles.selectInput}
          value={selectedIssue.id}
          onChange={(e) => {
            const found = allDemoIssues.find((i) => i.id === e.target.value);
            if (found && onSelectIssue) onSelectIssue(found);
          }}
        >
          {allDemoIssues.map((i) => (
            <option key={i.id} value={i.id}>
              {i.title}
            </option>
          ))}
        </select>
      </div>

      <div style={styles.targetIssue}>
        <span style={styles.badgePill}>Problemă de referință</span>
        <h4 style={{ margin: '6px 0 0', fontSize: '14px', fontWeight: 600 }}>{selectedIssue.title}</h4>
        <p className="supporting" style={{ marginTop: '4px' }}>{selectedIssue.locationName}</p>
      </div>

      <div style={styles.levelTabs} role="tablist" aria-label="Nivel de intervenție">
        {(['minimal', 'moderate', 'transformative'] as AlternativeLevel[]).map((level) => {
          const isCurrent = activeAlternativeLevel === level;
          return (
            <button
              key={level}
              role="tab"
              aria-selected={isCurrent}
              style={styles.levelTab(isCurrent)}
              onClick={() => onSelectAlternative(level)}
            >
              <span style={{ fontSize: '12px' }}>{alternativeLabels[level]}</span>
              <span style={{ fontSize: '10px' }}>Cost {selectedIssue.proposals[level].costEstimateCategory}</span>
            </button>
          );
        })}
      </div>

      <div style={styles.proposalCard}>
        <div style={styles.badgeRow}>
          <span style={styles.modelBadge}><Sparkles size={14} /> Catalog demonstrativ · sintetic</span>
          <span style={{ color: colors.muted, fontSize: '11px' }}>Orizont: {activeProp.timeframe}</span>
        </div>

        <h3 style={styles.proposalSummary}>{activeProp.summary}</h3>
        <p style={styles.proposalRationale}><strong>Raționament:</strong> {activeProp.rationale}</p>

        <div>
          <h5 style={styles.blockHeader}>Intervenții propuse în catalog</h5>
          <ul style={styles.interventionsList}>
            {activeProp.interventions.map((item, idx) => (
              <li key={idx} style={styles.interventionItem}><Layers size={13} /> {item}</li>
            ))}
          </ul>
        </div>

        <div>
          <h5 style={styles.blockHeader}>Direcție estimată de impact (Ipoteză calitativă)</h5>
          <div style={styles.impactTags}>
            {activeProp.impacts.map((imp, idx) => (
              <span key={idx} style={styles.impactPill(imp.positive)}>
                {imp.label}: <strong>{imp.change}</strong>
              </span>
            ))}
          </div>
        </div>

        {/* INTERACTIVE SIMULATION & TUNING PARAMETERS */}
        <div style={styles.tuningSection}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px', borderBottom: `1px solid ${colors.border}`, paddingBottom: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <SlidersHorizontal size={16} style={{ color: colors.accent }} aria-hidden="true" />
              <span style={{ fontSize: '12px', fontWeight: 700, color: colors.text }}>Parametri demonstrativi · formule locale</span>
            </div>
            <button
              type="button"
              onClick={handleReset}
              style={{
                background: 'transparent',
                border: 'none',
                color: colors.muted,
                fontSize: '11px',
                cursor: 'pointer',
                textDecoration: 'underline',
                padding: '2px 4px',
              }}
              title="Resetează la valorile implicite (75s, prioritate CTP, 2.5m)"
            >
              Resetează
            </button>
          </div>

          <div style={{ marginBottom: '12px' }}>
            <div style={styles.tuningRow}>
              <label id="green-phase-lbl" htmlFor="green-phase-range" style={styles.tuningLabel}>
                <Clock size={13} aria-hidden="true" /> Durată ciclu verde semaforic:
              </label>
              <span style={styles.tuningValue} aria-hidden="true">{greenPhaseSec} secunde</span>
            </div>
            <input
              id="green-phase-range"
              type="range"
              min={45}
              max={120}
              step={5}
              value={greenPhaseSec}
              aria-labelledby="green-phase-lbl"
              aria-valuemin={45}
              aria-valuemax={120}
              aria-valuenow={greenPhaseSec}
              aria-valuetext={`${greenPhaseSec} secunde de verde semaforic`}
              onChange={(e) => updateParam('greenPhaseSec', Number(e.target.value))}
              style={styles.sliderInput}
            />
          </div>

          <div style={{ marginBottom: '12px' }}>
            <div style={styles.tuningRow}>
              <label id="lane-width-lbl" htmlFor="lane-width-range" style={styles.tuningLabel}>
                <Layers size={13} aria-hidden="true" /> Lățime bandă velo / pietonală:
              </label>
              <span style={styles.tuningValue} aria-hidden="true">{laneWidthM} metri</span>
            </div>
            <input
              id="lane-width-range"
              type="range"
              min={1.5}
              max={3.5}
              step={0.1}
              value={laneWidthM}
              aria-labelledby="lane-width-lbl"
              aria-valuemin={1.5}
              aria-valuemax={3.5}
              aria-valuenow={laneWidthM}
              aria-valuetext={`${laneWidthM} metri lățime utilă`}
              onChange={(e) => updateParam('laneWidthM', Number(e.target.value))}
              style={styles.sliderInput}
            />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <label htmlFor="ctp-prio" style={styles.tuningLabel}>
              <Bus size={13} aria-hidden="true" /> Prioritizare CTP tramvaie / autobuze la semafor:
            </label>
            <input
              id="ctp-prio"
              type="checkbox"
              checked={ctpPriority}
              onChange={(e) => updateParam('ctpPriority', e.target.checked)}
              style={{ cursor: 'pointer', accentColor: colors.accent }}
            />
          </div>

          <div style={styles.liveFeedbackBox}>
            <strong>Exemplu sintetic la reglaj:</strong>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '4px' }}>
              <span>Reducere timp de așteptare:</span>
              <strong style={{ color: colors.observed }}>-{calculatedDelayChange}%</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '2px' }}>
              <span>Debit maxim estimat:</span>
              <strong style={{ color: colors.accent }}>{calculatedFlowCapacity} veh/h</strong>
            </div>
          </div>
        </div>

        <div style={styles.validationNote}>
          <ShieldAlert size={15} />
          <span>Geometria, fezabilitatea și impactul real nu sunt validate în acest demo sintetic.</span>
        </div>

        <button
          className="primary-button"
          onClick={() => onApplyScenario({ greenPhaseSec, ctpPriority, laneWidthM })}
          style={{
            width: '100%',
            marginTop: '16px',
            background: hasAppliedScenario ? colors.observed : colors.accent,
            color: colors.background,
          }}
        >
          {hasAppliedScenario ? (
            <>
              <Check size={18} /> Scenariu activat · Mergi la Compară
            </>
          ) : (
            <>
              Aplică în scenariu și evaluează <ArrowRight size={18} />
            </>
          )}
        </button>
      </div>
    </div>
  );
}

export type ConnectedInterventionType =
  | 'add_pedestrian_connection'
  | 'set_connection_enabled'
  | 'traffic_signal_retiming'
  | 'new_lane'
  | 'public_transport_priority'
  | 'major_road_reconstruction'
  | 'roundabout'
  | 'underpass';

export interface ConnectedProblemOption {
  id: string;
  title: string;
  description: string;
  severity: string;
}

export interface ConnectedSolutionOption {
  id: string;
  candidateId: string | null;
  typeId: string;
  title: string;
  description: string;
  geometry: unknown;
  relatedProblemIds: string[];
  hasExplicitProblemRelation: boolean;
  canEvaluate: boolean;
  hasGeometry: boolean;
}

interface ConnectedInterventionEditorProps {
  problems: ConnectedProblemOption[];
  solutions: ConnectedSolutionOption[];
  selectedProblemId: string | null;
  onSelectProblem: (problemId: string) => void;
  selectedType: ConnectedInterventionType;
  onSelectType: (type: ConnectedInterventionType) => void;
  intensity: AlternativeLevel;
  onSelectIntensity: (intensity: AlternativeLevel) => void;
  selectedSolutionId: string | null;
  onSelectSolution: (solution: ConnectedSolutionOption) => void;
  onEvaluate: (candidateId: string) => void;
  busy: boolean;
}

const connectedInterventionTypes: {
  id: ConnectedInterventionType;
  label: string;
  capability: 'graph' | 'conceptual' | 'unavailable';
  note: string;
}[] = [
  {
    id: 'add_pedestrian_connection',
    label: 'Legături pietonale și accesibilitate',
    capability: 'graph',
    note: 'SIM poate evalua candidați validați ca editări ipotetice ale grafului pietonal.',
  },
  {
    id: 'set_connection_enabled',
    label: 'Activarea unei conexiuni modelate',
    capability: 'graph',
    note: 'Necesită un ID ARTERIA al unei conexiuni din graful baseline.',
  },
  {
    id: 'traffic_signal_retiming',
    label: 'Reglarea timpilor la semafor',
    capability: 'conceptual',
    note: 'Disponibilă numai în demonstrația separată; nu se evaluează în studiul pietonal OSM.',
  },
  {
    id: 'new_lane',
    label: 'Benzi pietonale sau piste pentru biciclete',
    capability: 'conceptual',
    note: 'Concept de planificare; SIM nu modelează lățimea benzilor sau circulația velo.',
  },
  {
    id: 'public_transport_priority',
    label: 'Prioritate pentru transportul public',
    capability: 'unavailable',
    note: 'Indisponibilă pentru simulare reală: studiul curent nu modelează vehicule sau timpi de transport.',
  },
  {
    id: 'major_road_reconstruction',
    label: 'Reconstrucție majoră de drum',
    capability: 'unavailable',
    note: 'Indisponibilă: geometria rutieră, fezabilitatea și simularea traficului nu sunt evaluate de acest motor.',
  },
  {
    id: 'roundabout',
    label: 'Sens giratoriu',
    capability: 'unavailable',
    note: 'Indisponibil pentru simulare; nu există evaluare rutieră sau SUMO pentru această zonă.',
  },
  {
    id: 'underpass',
    label: 'Pasaj subteran',
    capability: 'unavailable',
    note: 'Indisponibil pentru simulare; SIM nu verifică proiecte de infrastructură sau condiții de teren.',
  },
];

const intensityOptions: { id: AlternativeLevel; label: string }[] = [
  { id: 'minimal', label: 'Minimală' },
  { id: 'moderate', label: 'Moderată' },
  { id: 'transformative', label: 'Transformatoare' },
];

function capabilityLabel(capability: 'graph' | 'conceptual' | 'unavailable', hasCandidate: boolean): string {
  if (capability === 'unavailable') return 'Indisponibilă';
  if (capability === 'conceptual') return 'Conceptuală';
  return hasCandidate ? 'Candidat SIM' : 'Motor suportă · fără candidat validat';
}

export function ConnectedInterventionEditor({
  problems,
  solutions,
  selectedProblemId,
  onSelectProblem,
  selectedType,
  onSelectType,
  intensity,
  onSelectIntensity,
  selectedSolutionId,
  onSelectSolution,
  onEvaluate,
  busy,
}: ConnectedInterventionEditorProps) {
  const selectedTypeInfo = connectedInterventionTypes.find((type) => type.id === selectedType) ?? connectedInterventionTypes[0]!;
  const matchingSolutions = solutions.filter((solution) => solution.typeId === selectedType);
  const relatedSolutions = selectedProblemId
    ? matchingSolutions.filter((solution) => !solution.hasExplicitProblemRelation || solution.relatedProblemIds.includes(selectedProblemId))
    : matchingSolutions;
  const selectedSolution = relatedSolutions.find((solution) => solution.id === selectedSolutionId) ?? null;
  const selectedProblem = problems.find((problem) => problem.id === selectedProblemId) ?? null;

  return (
    <section className={editorStyles.editor} aria-label="Editor de intervenții">
      <div className={editorStyles.heading}>
        <div><p className={editorStyles.eyebrow}>Studiu SIM conectat</p><h2>Editor de intervenții</h2></div>
        <span className={editorStyles.step}>Problemă → intervenție → evaluare</span>
      </div>

      <label className={editorStyles.label} htmlFor="connected-problem">1. Problemă detectată</label>
      {problems.length ? (
        <select id="connected-problem" className={editorStyles.select} value={selectedProblemId ?? ''} onChange={(event) => onSelectProblem(event.target.value)}>
          <option value="" disabled>Alege o problemă din studiul SIM</option>
          {problems.map((problem) => <option key={problem.id} value={problem.id}>{problem.title} · {problem.severity} · {problem.id}</option>)}
        </select>
      ) : <p className={editorStyles.empty}>Studiul nu a returnat probleme selectabile.</p>}
      {problems.length > 0 && !selectedProblemId && <p className={editorStyles.note}>Selectează o problemă pentru a vedea soluțiile pe care SIM le-a legat explicit de ea.</p>}

      {selectedProblem && (
        <div className={editorStyles.problemSummary}>
          <strong>{selectedProblem.title}</strong>
          <small className={editorStyles.problemId}>{selectedProblem.id}</small>
          <p>{selectedProblem.description}</p>
        </div>
      )}

      <fieldset className={editorStyles.fieldset}>
        <legend>2. Tipul intervenției</legend>
        <div className={editorStyles.typeGrid}>
          {connectedInterventionTypes.map((type) => {
            const typeHasCandidate = solutions.some((solution) => solution.typeId === type.id && solution.candidateId !== null && solution.canEvaluate);
            return (
              <button key={type.id} type="button" className={type.id === selectedType ? editorStyles.typeSelected : editorStyles.typeButton} aria-pressed={type.id === selectedType} onClick={() => onSelectType(type.id)}>
                <span>{type.label}</span>
                <small>{capabilityLabel(type.capability, typeHasCandidate)}</small>
              </button>
            );
          })}
        </div>
        <p className={editorStyles.note}>{selectedTypeInfo.note}</p>
      </fieldset>

      <fieldset className={editorStyles.fieldset}>
        <legend>3. Preferința de intervenție</legend>
        <div className={editorStyles.intensity} role="group" aria-label="Preferința de intensitate">
          {intensityOptions.map((option) => (
            <button key={option.id} type="button" aria-pressed={intensity === option.id} className={intensity === option.id ? editorStyles.intensitySelected : editorStyles.intensityButton} onClick={() => onSelectIntensity(option.id)}>
              {option.label}
            </button>
          ))}
        </div>
        <p className={editorStyles.note}>Preferința se păstrează local între pagini. SIM nu o transformă în cost, amploare fizică sau impact numeric.</p>
      </fieldset>

      <div className={editorStyles.candidateSection}>
        <h3>4. Soluție disponibilă în SIM</h3>
        {relatedSolutions.length ? (
          <div className={editorStyles.candidateList} role="radiogroup" aria-label="Candidați și concepte pentru intervenția selectată">
            {relatedSolutions.map((solution) => (
              <label key={solution.id} className={selectedSolutionId === solution.id ? editorStyles.solutionSelected : editorStyles.solution}>
                <input type="radio" name="connected-sim-solution" checked={selectedSolutionId === solution.id} onChange={() => onSelectSolution(solution)} />
                <span className={editorStyles.solutionBody}>
                  <strong>{solution.title}</strong>
                  <small>{solution.candidateId ? `Candidat ${solution.candidateId}` : 'Concept SIM fără candidat evaluabil'} · {solution.canEvaluate ? 'evaluare de graf disponibilă' : 'fără evaluare'}</small>
                  <span>{solution.description}</span>
                  {!solution.hasGeometry && <small>Geometria nu a fost returnată; harta nu va afișa o formă inventată.</small>}
                </span>
              </label>
            ))}
          </div>
        ) : (
          <p className={editorStyles.empty}>
            {selectedProblemId && matchingSolutions.length > 0
              ? 'SIM nu a legat explicit candidații acestui tip de problema selectată; nu presupunem că sunt înrudite.'
              : selectedTypeInfo.capability === 'graph'
              ? 'Nu există candidat SIM pentru acest tip în studiul curent. SIM nu va crea automat o propunere.'
              : 'Poți inspecta această idee conceptual, dar motorul curent nu o poate simula sau evalua.'}
          </p>
        )}
        {selectedProblemId && relatedSolutions.some((solution) => !solution.hasExplicitProblemRelation) && (
          <p className={editorStyles.note}>SIM nu a returnat o legătură directă pentru toți candidații cu problema selectată; relația nu este presupusă.</p>
        )}
        {selectedSolution && (
          <div className={editorStyles.actions}>
            <button type="button" className={editorStyles.secondary} onClick={() => onSelectSolution(selectedSolution)}>
              {selectedSolution.hasGeometry ? 'Arată geometria pe hartă' : 'Inspectează soluția'}
            </button>
            {selectedSolution.candidateId && selectedSolution.canEvaluate && (
              <button type="button" className={editorStyles.primary} disabled={busy} onClick={() => onEvaluate(selectedSolution.candidateId!)}>
                {busy ? 'Se evaluează…' : 'Evaluează Înainte / După'}
              </button>
            )}
          </div>
        )}
      </div>
    </section>
  );
}
