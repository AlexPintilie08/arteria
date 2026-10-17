import type { Area, Indicator, LayerId, AnalyzeResponse } from './contracts.ts';

/** Viewport bookmarks, NOT verified administrative boundaries or backend area IDs. */
export const neighborhoods = [
  { id: 'copou', name: 'Copou', center: [27.568, 47.184] as [number, number] },
  { id: 'centru', name: 'Centru', center: [27.586, 47.162] as [number, number] },
  { id: 'podu-ros', name: 'Podu Roș (Coridor Bahlui)', center: [27.584, 47.153] as [number, number] },
  { id: 'tatarasi', name: 'Tătărași', center: [27.613, 47.169] as [number, number] },
  { id: 'alexandru', name: 'Alexandru cel Bun', center: [27.548, 47.169] as [number, number] },
];
export const layers: { id: LayerId; label: string }[] = [
  { id: 'roads', label: 'Străzi' }, { id: 'walking', label: 'Mers pe jos' },
  { id: 'cycling', label: 'Biciclete' }, { id: 'public_transport', label: 'Transport public' },
  { id: 'green_space', label: 'Spații verzi' }, { id: 'buildings', label: 'Clădiri' },
  { id: 'parking', label: 'Parcări' }, { id: 'points_of_interest', label: 'Puncte de interes' },
];
export const evidenceLabels = { observed: 'Observat', calculated: 'Calculat', estimated: 'Estimat', unknown: 'Necunoscut' } as const;
export const alternativeLabels = { minimal: 'Minimală', moderate: 'Moderată', transformative: 'Transformatoare' } as const;
export function emptyIndicators(): Indicator[] {
  return [
    { id: 'walk_access', label: 'Acces pietonal la servicii', unit: '%' },
    { id: 'cycle_connectivity', label: 'Conectivitate velo', unit: 'ratio' },
    { id: 'green_access', label: 'Acces la spații verzi', unit: 'minute' },
  ].map((item) => ({ ...item, value: null, status: 'unknown', provenance: [], uncertainty: {
    kind: 'missing_data', description: 'Backendul și sursele de date nu sunt conectate.', interval: null, confidence: null,
  } }));
}
export function createDemoAnalysis(area: Area): AnalyzeResponse {
  return { analysis_id: 'fixture-no-analysis', area, created_at: new Date().toISOString(),
    indicators: emptyIndicators(), issues: [],
    layer_availability: layers.map(({ id }) => ({ layer: id, status: 'unknown', reason: 'Strat analitic neconectat.' })),
    warnings: ['Previzualizare de interfață. Nu s-a executat nicio analiză sau simulare.'],
  };
}

export interface NeighborhoodGeometry {
  id: string;
  name: string;
  center: [number, number];
  bounds: [[number, number], [number, number]];
  polygon: [number, number][];
  corridors: { id: string; name: string; coordinates: [number, number][] }[];
}

export const neighborhoodGeometries: Record<string, NeighborhoodGeometry> = {
  copou: {
    id: 'copou',
    name: 'Copou',
    center: [27.568, 47.184],
    bounds: [[27.550, 47.170], [27.585, 47.198]],
    polygon: [
      [27.555, 47.174], [27.575, 47.172], [27.584, 47.188],
      [27.578, 47.196], [27.560, 47.195], [27.552, 47.182], [27.555, 47.174]
    ],
    corridors: [
      { id: 'bvd-carol', name: 'Bulevardul Carol I', coordinates: [[27.572, 47.173], [27.569, 47.181], [27.565, 47.190], [27.561, 47.197]] },
      { id: 'str-sararie', name: 'Strada Sărărie', coordinates: [[27.579, 47.173], [27.578, 47.183], [27.574, 47.193]] }
    ]
  },
  centru: {
    id: 'centru',
    name: 'Centru',
    center: [27.586, 47.162],
    bounds: [[27.570, 47.150], [27.602, 47.172]],
    polygon: [
      [27.574, 47.156], [27.593, 47.154], [27.599, 47.168],
      [27.588, 47.171], [27.575, 47.167], [27.574, 47.156]
    ],
    corridors: [
      { id: 'bvd-stefan', name: 'Bulevardul Ștefan cel Mare', coordinates: [[27.578, 47.160], [27.585, 47.161], [27.592, 47.163]] },
      { id: 'str-anastasie-panu', name: 'Strada Anastasie Panu', coordinates: [[27.584, 47.158], [27.589, 47.160], [27.594, 47.164]] }
    ]
  },
  tatarasi: {
    id: 'tatarasi',
    name: 'Tătărași',
    center: [27.613, 47.169],
    bounds: [[27.598, 47.158], [27.630, 47.182]],
    polygon: [
      [27.601, 47.161], [27.625, 47.160], [27.628, 47.178],
      [27.615, 47.181], [27.604, 47.173], [27.601, 47.161]
    ],
    corridors: [
      { id: 'str-vasile-lupu', name: 'Strada Vasile Lupu', coordinates: [[27.604, 47.163], [27.614, 47.169], [27.623, 47.177]] },
      { id: 'str-han-tatar', name: 'Strada Han Tătar', coordinates: [[27.606, 47.167], [27.617, 47.171], [27.625, 47.174]] }
    ]
  },
  alexandru: {
    id: 'alexandru',
    name: 'Alexandru cel Bun',
    center: [27.548, 47.169],
    bounds: [[27.530, 47.156], [27.565, 47.178]],
    polygon: [
      [27.535, 47.162], [27.560, 47.160], [27.562, 47.175],
      [27.545, 47.177], [27.533, 47.170], [27.535, 47.162]
    ],
    corridors: [
      { id: 'bvd-alexandru', name: 'Bulevardul Alexandru cel Bun', coordinates: [[27.536, 47.165], [27.548, 47.168], [27.559, 47.171]] },
      { id: 'str-mircea-cel-batran', name: 'Strada Mircea cel Bătrân', coordinates: [[27.541, 47.163], [27.550, 47.167], [27.558, 47.173]] }
    ]
  },
  'podu-ros': {
    id: 'podu-ros',
    name: 'Podu Roș (Coridor Bahlui)',
    center: [27.584, 47.153],
    bounds: [[27.570, 47.140], [27.605, 47.165]],
    polygon: [
      [27.572, 47.146], [27.598, 47.145], [27.602, 47.160],
      [27.586, 47.162], [27.573, 47.156], [27.572, 47.146]
    ],
    corridors: [
      { id: 'bvd-socola', name: 'Bulevardul Socola', coordinates: [[27.584, 47.153], [27.592, 47.144], [27.601, 47.135]] },
      { id: 'str-palat', name: 'Strada Palat', coordinates: [[27.584, 47.153], [27.584, 47.159], [27.585, 47.164]] },
      { id: 'splai-bahlui', name: 'Splai Bahlui Drept', coordinates: [[27.568, 47.155], [27.584, 47.153], [27.605, 47.151]] },
      { id: 'str-nicolina', name: 'Strada Nicolina', coordinates: [[27.584, 47.153], [27.574, 47.148], [27.565, 47.142]] }
    ]
  }
};

export interface DemoStudyIssue {
  id: string;
  title: string;
  category: 'velo' | 'pietonal' | 'nod_rutier';
  locationName: string;
  coordinates: [number, number];
  description: string;
  supportingIndicatorId: string;
  proposals: {
    minimal: {
      summary: string;
      interventions: string[];
      rationale: string;
      timeframe: string;
      costEstimateCategory: 'redus' | 'mediu' | 'ridicat';
      impacts: { label: string; change: string; positive: boolean }[];
    };
    moderate: {
      summary: string;
      interventions: string[];
      rationale: string;
      timeframe: string;
      costEstimateCategory: 'redus' | 'mediu' | 'ridicat';
      impacts: { label: string; change: string; positive: boolean }[];
    };
    transformative: {
      summary: string;
      interventions: string[];
      rationale: string;
      timeframe: string;
      costEstimateCategory: 'redus' | 'mediu' | 'ridicat';
      impacts: { label: string; change: string; positive: boolean }[];
    };
  };
  comparisonData: {
    indicator: string;
    unit: string;
    baseline: number;
    scenarioMinimal: number;
    scenarioModerate: number;
    scenarioTransformative: number;
    method: string;
  }[];
}

export const demoIssuesByNeighborhood: Record<string, DemoStudyIssue[]> = {
  copou: [
    {
      id: 'issue-copou-1',
      title: 'Discontinuitate axă velo Carol I — Parcul Copou',
      category: 'velo',
      locationName: 'Bulevardul Carol I (segment Universitate — Parcul Copou)',
      coordinates: [27.570, 47.180],
      description: 'Pista de biciclete se întrerupe brusc înainte de intersecția cu Str. Oastei, forțând bicicliștii să circule pe trotuarul pietonal îngust sau pe carosabilul cu trafic intens de transport public.',
      supportingIndicatorId: 'cycle_connectivity',
      proposals: {
        minimal: {
          summary: 'Marcaj tactil și coborâri de bordură cu semnalizare prioritară velo.',
          interventions: ['Marcare trecere mixtă biciclete/pietoni', 'Semnalizare verticală C17', 'Montare stâlpișori flexibili delimitatori'],
          rationale: 'Rezolvă problema punctuală de ghidaj și avertizare fără modificarea gabaritului trotuarelor.',
          timeframe: '1-2 luni',
          costEstimateCategory: 'redus',
          impacts: [
            { label: 'Siguranță la traversare', change: '+18%', positive: true },
            { label: 'Continuitate velo', change: '+12%', positive: true },
            { label: 'Capacitate rutieră carosabil', change: '0%', positive: true }
          ]
        },
        moderate: {
          summary: 'Bandă velo dedicată bidirecțională segregată fizic prin bordură teșită.',
          interventions: ['Reconfigurare profil stradal (lățime 2.0m pistă)', 'Bordură de protecție din granit teșit', 'Reamplasare stâlpi de iluminat'],
          rationale: 'Separă complet fluxul de biciclete de fluxul pietonal universitar intens de pe B-dul Carol I.',
          timeframe: '4-6 luni',
          costEstimateCategory: 'mediu',
          impacts: [
            { label: 'Conectivitate velo continuă', change: '+45%', positive: true },
            { label: 'Reducere conflicte pieton/bicicletă', change: '-60%', positive: true },
            { label: 'Locuri de parcare adiacente', change: '-8 locuri', positive: false }
          ]
        },
        transformative: {
          summary: 'Coridor verde multimodal cu lărgire trotuar, pistă continuă și zonă shared 30 km/h.',
          interventions: ['Reducere secțiune carosabil la o bandă/sens', 'Traseu velo integrat în rețeaua metropolitană', 'Plantare aliniament 40 arbori'],
          rationale: 'Transformă axul Copou într-un bulevard ecologic universitar cu prioritate absolută mobilității active.',
          timeframe: '12-18 luni',
          costEstimateCategory: 'ridicat',
          impacts: [
            { label: 'Conectivitate velo rețea', change: '+85%', positive: true },
            { label: 'Zgomot urban la fațade', change: '-4.2 dB', positive: true },
            { label: 'Timp mediu tranzit auto vârf', change: '+4 min', positive: false }
          ]
        }
      },
      comparisonData: [
        { indicator: 'Indice continuitate velo', unit: 'ratio', baseline: 0.38, scenarioMinimal: 0.44, scenarioModerate: 0.72, scenarioTransformative: 0.94, method: 'OSM topological routing graph' },
        { indicator: 'Viteză medie biciclete', unit: 'km/h', baseline: 11.2, scenarioMinimal: 12.5, scenarioModerate: 16.8, scenarioTransformative: 19.4, method: 'Model estimativ flux continuu' },
        { indicator: 'Puncte de conflict pieton/bicicletă', unit: 'puncte/km', baseline: 14, scenarioMinimal: 11, scenarioModerate: 3, scenarioTransformative: 0, method: 'Identificare spațială intersecții de flux' }
      ]
    },
    {
      id: 'issue-copou-2',
      title: 'Acces pietonal deficitar la Parcul Expoziției',
      category: 'pietonal',
      locationName: 'Aleea Gh. Asachi — Parcul Expoziției',
      coordinates: [27.562, 47.192],
      description: 'Lipsa unei traversări protejate la nivel între stația de tramvai și intrarea principală în Parc, trotuare îngustate de arbori seculari neprotejați.',
      supportingIndicatorId: 'walk_access',
      proposals: {
        minimal: {
          summary: 'Trecere de pietoni supraînălțată cu semnalizare cu buton și iluminat dedicat LED.',
          interventions: ['Platformă supraînălțată la nivel de trotuar', 'Iluminat direcționat 50 lux pe trecere', 'Covoare tactile pentru nevăzători'],
          rationale: 'Crește vizibilitatea pietonilor pe timp de noapte și forțează încetinirea vehiculelor.',
          timeframe: '1 lună',
          costEstimateCategory: 'redus',
          impacts: [
            { label: 'Distanță de frânare vehicule', change: '-35%', positive: true },
            { label: 'Accesibilitate persoane cu mobilitate redusă', change: '+40%', positive: true },
            { label: 'Timp tranzit tramvai', change: '0%', positive: true }
          ]
        },
        moderate: {
          summary: 'Scuar median de refugiu și reconfigurare alveolă tramvai cu peron lărgit.',
          interventions: ['Refugiu central pietonal cu lățime 2.2m', 'Peron tramvai adus la nivelul podelei joase', 'Marcaje tactile extinse'],
          rationale: 'Permite traversarea în două etape în siguranță și optimizează urcarea/coborârea din transportul public.',
          timeframe: '3-5 luni',
          costEstimateCategory: 'mediu',
          impacts: [
            { label: 'Timp de așteptare pietonal la trecere', change: '-28%', positive: true },
            { label: 'Capacitate acces peron tramvai', change: '+50%', positive: true },
            { label: 'Lățime bandă auto', change: '-0.3m', positive: false }
          ]
        },
        transformative: {
          summary: 'Esplanadă pietonală integrată și reorganizare acces parc fără mașini.',
          interventions: ['Zonă complet pietonală pavată cu piatră naturală', 'Deviere acces auto de aprovizionare pe rute secundare', 'Grădină de ploaie cu drenaj sustenabil'],
          rationale: 'Conectează direct Parcul Expoziției cu Grădina Botanică într-o axă verde continuă.',
          timeframe: '9-12 luni',
          costEstimateCategory: 'ridicat',
          impacts: [
            { label: 'Suprafață pietonală continuă', change: '+1200 m²', positive: true },
            { label: 'Accesibilitate verde în 5 minute', change: '+68%', positive: true },
            { label: 'Acces autovehicule riverani', change: 'cu permis orar', positive: false }
          ]
        }
      },
      comparisonData: [
        { indicator: 'Populație cu acces la parc în 5 min', unit: '%', baseline: 64, scenarioMinimal: 68, scenarioModerate: 82, scenarioTransformative: 96, method: 'Isochrone walking catchment 400m' },
        { indicator: 'Timp mediu traversare', unit: 'secunde', baseline: 26, scenarioMinimal: 18, scenarioModerate: 12, scenarioTransformative: 6, method: 'Măsurare timp de așteptare pietoni' },
        { indicator: 'Suprafață pietonală protejată', unit: 'm²', baseline: 340, scenarioMinimal: 410, scenarioModerate: 780, scenarioTransformative: 1540, method: 'Calcul poligoane trotuare libere' }
      ]
    }
  ],
  centru: [
    {
      id: 'issue-centru-1',
      title: 'Conflict de flux în intersecția Elena Doamna — Anastasie Panu',
      category: 'nod_rutier',
      locationName: 'Nodul Elena Doamna — Palatul de Justiție',
      coordinates: [27.588, 47.161],
      description: 'Punct critic de congestie rutieră unde fluxurile auto de tranzit intră în conflict direct cu liniile de tramvai și fluxul pietonal masiv spre Palas / Curtea de Apel.',
      supportingIndicatorId: 'walk_access',
      proposals: {
        minimal: {
          summary: 'Optimizare cicluri semaforice adaptive cu undă verde tramvai și detectoare radar.',
          interventions: ['Sincronizare buclă inductivă / senzori video', 'Prioritate dedicată 8 secunde tramvai', 'Refacere marcaje galbene antiblocare'],
          rationale: 'Deblochează intersecția în orele de vârf fără șantier structural.',
          timeframe: '1-2 luni',
          costEstimateCategory: 'redus',
          impacts: [
            { label: 'Întârzieri tramvai pe oră de vârf', change: '-22%', positive: true },
            { label: 'Viteza comercială a transportului public', change: '+14%', positive: true },
            { label: 'Timp așteptare viraj stânga auto', change: '+5%', positive: false }
          ]
        },
        moderate: {
          summary: 'Sens giratoriu compact cu bandă separată pentru tramvai și protecție pietoni.',
          interventions: ['Insulă centrală denivelată 12m', 'Traversare tramvai ghidată pe axul central', 'Treceri de pietoni retrase cu 5m pentru vizibilitate'],
          rationale: 'Fluidizează virajele secundare și reduce viteza de abordare a intersecției.',
          timeframe: '6-8 luni',
          costEstimateCategory: 'mediu',
          impacts: [
            { label: 'Capacitate nod rutier', change: '+28%', positive: true },
            { label: 'Accidente cu vătămare corporală', change: '-45%', positive: true },
            { label: 'Cost de mentenanță semafoare', change: '-30%', positive: true }
          ]
        },
        transformative: {
          summary: 'Nod denivelat compact (pasaj subteran tranzit + piațetă pietonală de suprafață).',
          interventions: ['Pasaj subteran 2 benzi pe axul principal', 'Deck superior cu esplanadă pietonală și tramvai', 'Sisteme avansate de pompe evacuare pluvială'],
          rationale: 'Elimină complet traficul auto de tranzit de la suprafața istorică a orașului.',
          timeframe: '18-24 luni',
          costEstimateCategory: 'ridicat',
          impacts: [
            { label: 'Trafic auto de suprafață eliminat', change: '-75%', positive: true },
            { label: 'Calitate aer la nivel pietonal (PM10)', change: '-32%', positive: true },
            { label: 'Amprentă de șantier pe durata execuției', change: 'devieri majore 12 luni', positive: false }
          ]
        }
      },
      comparisonData: [
        { indicator: 'Timp mediu de întârziere per vehicul', unit: 'secunde/veh', baseline: 68, scenarioMinimal: 52, scenarioModerate: 38, scenarioTransformative: 14, method: 'Model determinist de coadă nod rutier' },
        { indicator: 'Viteză comercială tramvai', unit: 'km/h', baseline: 9.8, scenarioMinimal: 11.4, scenarioModerate: 14.1, scenarioTransformative: 21.0, method: 'Urmărire timpi parcurs tronson 800m' },
        { indicator: 'Nivel estimat zgomot echivalent Leq', unit: 'dB(A)', baseline: 74, scenarioMinimal: 73, scenarioModerate: 69, scenarioTransformative: 59, method: 'Calcul propagare acustică la fațadă' }
      ]
    }
  ],
  tatarasi: [
    {
      id: 'issue-tatarasi-1',
      title: 'Barieră de mobilitate și siguranță în intersecția Han Tătar',
      category: 'nod_rutier',
      locationName: 'Sens Giratoriu Han Tătar (Str. Vasile Lupu — Str. Han Tătar)',
      coordinates: [27.614, 47.169],
      description: 'Capacitate depășită în orele de vârf pe direcția Ciurchi — Vasile Lupu; lipsă trotuare continue spre Spitalul de Copii.',
      supportingIndicatorId: 'walk_access',
      proposals: {
        minimal: {
          summary: 'Reconfigurare benzi de ghidaj și insule separatoare din beton prefabricat.',
          interventions: ['Borduri prefabricate ghidaj curbă', 'Marcaje rutiere termoplastice clasa 2', 'Reamplasare treceri pietoni'],
          rationale: 'Corectează traiectoriile vehiculelor fără modificări de utilități subterane.',
          timeframe: '1 lună',
          costEstimateCategory: 'redus',
          impacts: [
            { label: 'Capacitate intrare braț secundar', change: '+15%', positive: true },
            { label: 'Viteză abordare intersecție', change: '-8 km/h', positive: true },
            { label: 'Durată execuție', change: '5 zile lucrătoare', positive: true }
          ]
        },
        moderate: {
          summary: 'Sens giratoriu turbo cu descărcare directă pentru viraj dreapta.',
          interventions: ['Banda separată de bypass dreapta', 'Elemente de delimitare fizică între benzi', 'Platforme lărgite pentru pietoni'],
          rationale: 'Evită conflictele de schimbare a benzii în interiorul inelului giratoriu.',
          timeframe: '3-4 luni',
          costEstimateCategory: 'mediu',
          impacts: [
            { label: 'Reducere timp așteptare ore vârf', change: '-35%', positive: true },
            { label: 'Siguranță manevre circulare', change: '+50%', positive: true },
            { label: 'Suprafață carosabilă ocupată', change: '+12%', positive: false }
          ]
        },
        transformative: {
          summary: 'Sens giratoriu denivelat cu pasaj subteran pe axul Vasile Lupu.',
          interventions: ['Pasaj subteran 2 benzi ax nord-sud', 'Inel de suprafață dedicat conexiunilor de cartier', 'Trotuare perimetrice lărgite la 3 metri'],
          rationale: 'Separă traficul de tranzit al cartierului de traficul rezidențial local și transportul public.',
          timeframe: '14-18 luni',
          costEstimateCategory: 'ridicat',
          impacts: [
            { label: 'Capacitate totală nod', change: '+90%', positive: true },
            { label: 'Poluare aer la nivelul locuințelor', change: '-28%', positive: true },
            { label: 'Investiție inițială', change: 'necesită finanțare europeană', positive: false }
          ]
        }
      },
      comparisonData: [
        { indicator: 'Lungime medie coadă la vârf', unit: 'metri', baseline: 240, scenarioMinimal: 195, scenarioModerate: 110, scenarioTransformative: 25, method: 'Model flux de trafic nesaturat' },
        { indicator: 'Indice acces pietonal spital', unit: 'scor 0-100', baseline: 42, scenarioMinimal: 55, scenarioModerate: 74, scenarioTransformative: 92, method: 'Evaluare obstacole și siguranță pietonală' },
        { indicator: 'Emisii CO2 în nod la frânare/oprire', unit: 'kg/h', baseline: 185, scenarioMinimal: 160, scenarioModerate: 115, scenarioTransformative: 62, method: 'Estimare pe baza timpilor de staționare' }
      ]
    }
  ],
  alexandru: [
    {
      id: 'issue-alexandru-1',
      title: 'Izolare rețea velo și pietonală pe malul râului Bahlui',
      category: 'velo',
      locationName: 'Splai Bahlui Mal Drept — Pasarela Mircea',
      coordinates: [27.545, 47.167],
      description: 'Lipsa unei conexiuni continue pe malul drept spre Podul de Piatră și Gara Nicolina, împiedicând naveta ecologică din cartier spre polul de birouri.',
      supportingIndicatorId: 'cycle_connectivity',
      proposals: {
        minimal: {
          summary: 'Barieră de delimitare și covor antiderapant pe digul existent.',
          interventions: ['Tratament antiderapant asfalt', 'Balustradă protecție pe coronament', 'Panouri informative kilometrice'],
          rationale: 'Activează tronsonul existent pentru biciclete cu cost minim.',
          timeframe: '1 lună',
          costEstimateCategory: 'redus',
          impacts: [
            { label: 'Securitate deplasare velo', change: '+25%', positive: true },
            { label: 'Atragere utilizatori navetiști', change: '+30%', positive: true },
            { label: 'Lățime utilă', change: '1.8m (sub standard ideal)', positive: false }
          ]
        },
        moderate: {
          summary: 'Pistă velo bidirecțională dedicată 2.5m cu iluminat solar inteligent.',
          interventions: ['Lărgire rambleu dig pe console ușoare', 'Puncte de încărcare biciclete electrice', 'Iluminat cu senzori de mișcare'],
          rationale: 'Asigură o pistă de nivel european complet izolată de orice trafic auto.',
          timeframe: '4-6 luni',
          costEstimateCategory: 'mediu',
          impacts: [
            { label: 'Conectivitate directă spre Gară', change: '+70%', positive: true },
            { label: 'Capacitate orară velo', change: '800 biciclete/h', positive: true },
            { label: 'Intervenție pe zona de protecție ape', change: 'avize ABA Prut-Bârlad', positive: false }
          ]
        },
        transformative: {
          summary: 'Parc liniar fluvial cu pasarelă pietonală/velo nouă peste Bahlui.',
          interventions: ['Pasarelă hobanată velo de 45m', 'Amenajare peisagistică cu amfiteatru verde', 'Traseu de alergare și pistă velo distincte'],
          rationale: 'Transformă malul râului într-un parc recreativ major care unifică cartierele Alexandru și Galata.',
          timeframe: '14-20 luni',
          costEstimateCategory: 'ridicat',
          impacts: [
            { label: 'Suprafață spațiu verde activat', change: '+18.000 m²', positive: true },
            { label: 'Acces pietonal inter-cartiere', change: '+120%', positive: true },
            { label: 'Timp navetă velo spre centru', change: '-12 min', positive: true }
          ]
        }
      },
      comparisonData: [
        { indicator: 'Timp parcurs Alexandru — Palas pe bicicletă', unit: 'minute', baseline: 24, scenarioMinimal: 20, scenarioModerate: 15, scenarioTransformative: 11, method: 'Test traseu cronometrat pe ax dedicat' },
        { indicator: 'Utilizatori velo estimați pe zi', unit: 'călătorii/zi', baseline: 320, scenarioMinimal: 540, scenarioModerate: 1250, scenarioTransformative: 2800, method: 'Model gravitațional atracție mobilitate' },
        { indicator: 'Suprafață zonă verde perimetrală accesibilă', unit: 'hectare', baseline: 1.4, scenarioMinimal: 1.4, scenarioModerate: 2.8, scenarioTransformative: 6.2, method: 'Măsurare GIS spațiu deschis reabilitat' }
      ]
    }
  ],
  'podu-ros': [
    {
      id: 'issue-podu-ros-1',
      title: 'Podu Roș Multi-Leg Center #IS-PR-01 (Congestie Critică LOS E/F)',
      category: 'nod_rutier',
      locationName: 'Nodul Podu Roș — B-dul Socola / Str. Palat / Splai Bahlui',
      coordinates: [27.584, 47.153],
      description: 'Nod de distribuție cu 6 brațe reglementate la trecerea peste râul Bahlui. Coadă de 340m pe intrarea Socola în orele de vârf (08:15 AM), conflict sever tramvai/auto și întârziere medie de 74.2 s/vehicul.',
      supportingIndicatorId: 'walk_access',
      proposals: {
        minimal: {
          summary: 'Sincronizare dinamică semafoare și benzi de preselecție viraj dreapta liber spre Splai.',
          interventions: [
            'Prelungire fază verde B-dul Socola cu 12 secunde la orele de vârf',
            'Separare fizică bandă viraj dreapta spre Splai Bahlui Drept',
            'Senzori de coadă radar integrați în dulapul de semnalizare'
          ],
          rationale: 'Rezolvă evacuarea rapidă a fluxului spre Splai fără intervenții pe podul istoric.',
          timeframe: '1-2 luni',
          costEstimateCategory: 'redus',
          impacts: [
            { label: 'Coadă maximă Socola', change: '-22% (265m)', positive: true },
            { label: 'Timp mediu așteptare', change: '-14s', positive: true },
            { label: 'Investiție infrastructură', change: 'minimă', positive: true }
          ]
        },
        moderate: {
          summary: 'Sens giratoriu turbo cu descărcări directe și bandă prioritară CTP Tramvai.',
          interventions: [
            'Reconfigurare inel Podu Roș în turbo-giratoriu cu benzi spiralate',
            'Prioritate absolută la barieră optică pentru tramvaiele 9 și 11',
            'Refugii pietonale mediane extinse la 2.5m pe ambele capete ale podului'
          ],
          rationale: 'Reduce punctele de conflict de la 24 la 8 și asigură tranzitul nestingherit al transportului public.',
          timeframe: '6-9 luni',
          costEstimateCategory: 'mediu',
          impacts: [
            { label: 'Capacitate flux nod', change: '+35% (2.940 veh/h)', positive: true },
            { label: 'Viteză comercială tramvai', change: '+28%', positive: true },
            { label: 'Conflicte de schimbare bandă', change: '-70%', positive: true }
          ]
        },
        transformative: {
          summary: 'Nod denivelat Podu Roș: Pasaj subteran Bd. Socola — Str. Palat + Pod pietonal verde peste Bahlui.',
          interventions: [
            'Pasaj rutier subteran cu 4 benzi (2 pe sens) sub albia râului Bahlui',
            'Nivel de suprafață dedicat exclusiv tramvaiului, pietonilor și velo',
            'Pasarelă pietonală nouă integrată cu promenada Splai Bahlui'
          ],
          rationale: 'Elimină complet traficul greu de tranzit din Piața Podu Roș, creând un pol civic de calitate superioară.',
          timeframe: '24-30 luni',
          costEstimateCategory: 'ridicat',
          impacts: [
            { label: 'Reducere trafic de suprafață', change: '-82%', positive: true },
            { label: 'Nivel zgomot la fațade', change: '-8.5 dB', positive: true },
            { label: 'Accesibilitate pietonală râu', change: '+150%', positive: true }
          ]
        }
      },
      comparisonData: [
        { indicator: 'Debit maxim la vârf (Flow Rate)', unit: 'veh/h', baseline: 2180, scenarioMinimal: 2450, scenarioModerate: 2940, scenarioTransformative: 3820, method: 'Model hidraulic de capacitate nod giratoriu' },
        { indicator: 'Coadă percentilă 95 (B-dul Socola)', unit: 'metri', baseline: 340, scenarioMinimal: 265, scenarioModerate: 140, scenarioTransformative: 35, method: 'Măsurători detectoare de buclă inductive Iași' },
        { indicator: 'Timp mediu de așteptare (Delay)', unit: 'secunde/veh', baseline: 74.2, scenarioMinimal: 60.5, scenarioModerate: 38.0, scenarioTransformative: 12.4, method: 'Calcul delay Webster pe faze semaforice' },
        { indicator: 'Nivel de Serviciu (Level of Service)', unit: 'clasa (A-F)', baseline: 5, scenarioMinimal: 4, scenarioModerate: 3, scenarioTransformative: 1, method: 'Standard HCM 2020 (A=1 ... F=6)' }
      ]
    }
  ]
};

export const allDemoIssues: DemoStudyIssue[] = Object.values(demoIssuesByNeighborhood).flat();

