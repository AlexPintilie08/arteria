import { Text, View, StyleSheet } from 'react-native';
import { colors, radius, spacing } from '@arteria/shared/tokens';
import { type } from '../../components/typography';
/** Native map adapter boundary. Do not import maplibre-gl (DOM/WebGL) here. */
export function MapPlaceholder({ center }: { center: [number, number] }) {
  return <View style={styles.canvas}><Text style={type.heading}>Iași, în perspectivă.</Text><Text style={type.body}>Spațiul pentru harta nativă este pregătit.</Text><Text style={type.notice}>Hartă neconectată · fără date geografice</Text><Text style={type.small}>{center[1].toFixed(3)}° N / {center[0].toFixed(3)}° E</Text></View>;
}
const styles = StyleSheet.create({ canvas: { minHeight: 260, padding: spacing.lg, gap: spacing.md, justifyContent: 'center', backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border, borderRadius: radius.panel } });
