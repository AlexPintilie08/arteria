import { Text, View, StyleSheet } from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { neighborhoods, emptyIndicators, evidenceLabels } from '@arteria/shared/fixtures';
import { colors, spacing } from '@arteria/shared/tokens';
import { demoMode } from '../../lib/api';
import { Screen } from '../../components/Screen';
import { type } from '../../components/typography';
import type { RootStackParamList } from '../../app/navigation';
export function AnalysisScreen({ route }: NativeStackScreenProps<RootStackParamList, 'Analysis'>) {
  const name = neighborhoods.find((area) => area.id === route.params.neighborhoodId)?.name ?? 'Zonă necunoscută';
  return <Screen><Text style={type.title}>{name}</Text><Text style={type.notice}>{demoMode ? 'Previzualizare de interfață. Nu s-a executat o analiză.' : 'Integrarea analizei native este în așteptarea backendului și a zonelor validate.'}</Text>{emptyIndicators().map((indicator) => <View key={indicator.id} style={styles.row}><Text style={type.heading}>{indicator.label}</Text><Text style={styles.value}>— <Text style={type.small}>{indicator.unit}</Text></Text><Text style={type.small}>{evidenceLabels[indicator.status]}</Text><Text style={type.small}>{indicator.uncertainty.description}</Text></View>)}<Text style={type.body}>Sursele, metodele și limitele vor fi preluate din răspunsul API. Valorile lipsă rămân necunoscute.</Text></Screen>;
}
const styles = StyleSheet.create({ row: { paddingVertical: spacing.md, borderBottomWidth: 1, borderColor: colors.border, gap: spacing.sm }, value: { color: colors.text, fontSize: 36 } });
