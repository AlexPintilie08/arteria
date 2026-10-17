import { Text, View, Pressable, StyleSheet } from 'react-native';
import { useState } from 'react';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { neighborhoods } from '@arteria/shared/fixtures';
import { colors, spacing, radius } from '@arteria/shared/tokens';
import type { RootStackParamList } from '../../app/navigation';
import { Screen } from '../../components/Screen';
import { Button } from '../../components/Button';
import { type } from '../../components/typography';
import { MapPlaceholder } from './MapPlaceholder';
export function ExploreScreen({ navigation }: NativeStackScreenProps<RootStackParamList, 'Explore'>) {
  const [selectedId, setSelectedId] = useState('copou');
  const selected = neighborhoods.find((area) => area.id === selectedId) ?? neighborhoods[0]!;
  return <Screen><Text style={type.small}>ARTERIA by ARION · Iași</Text><Text style={type.title}>Înțelege locul.{ '\n' }Modelează viitorul.</Text><MapPlaceholder center={selected.center} /><Text style={type.heading}>Alege un reper</Text><View style={styles.areas}>{neighborhoods.map((area) => <Pressable key={area.id} accessibilityRole="radio" accessibilityState={{ checked: selectedId === area.id }} onPress={() => setSelectedId(area.id)} style={({ pressed }) => [styles.area, selectedId === area.id && styles.selected, pressed && styles.pressed]}><Text style={styles.label}>{area.name}</Text></Pressable>)}</View><Text style={type.small}>Repere orientative; limitele geografice nu sunt încă validate.</Text><Button label="Explorează indicatorii" onPress={() => navigation.navigate('Analysis', { neighborhoodId: selectedId })} /><Button label="Scenarii de intervenție" secondary onPress={() => navigation.navigate('Scenarios')} /><Button label="Comparație înainte / după" secondary onPress={() => navigation.navigate('Comparison')} /></Screen>;
}
const styles = StyleSheet.create({ areas: { gap: spacing.sm }, area: { minHeight: 48, padding: spacing.md, borderWidth: 1, borderColor: colors.border, borderRadius: radius.control, backgroundColor: colors.surface }, selected: { borderColor: colors.accent, backgroundColor: colors.raised }, pressed: { opacity: .7 }, label: { color: colors.text, fontSize: 16 } });
