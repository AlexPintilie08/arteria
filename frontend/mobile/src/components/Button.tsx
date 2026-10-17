import { Pressable, StyleSheet, Text } from 'react-native';
import { colors, radius } from '@arteria/shared/tokens';
export function Button({ label, onPress, secondary = false, disabled = false }: { label: string; onPress: () => void; secondary?: boolean; disabled?: boolean }) {
  return <Pressable accessibilityRole="button" accessibilityState={{ disabled }} disabled={disabled} onPress={onPress} style={({ pressed }) => [styles.button, secondary && styles.secondary, (pressed || disabled) && styles.dim]}><Text style={[styles.label, secondary && styles.secondaryLabel]}>{label}</Text></Pressable>;
}
const styles = StyleSheet.create({
  button: { minHeight: 48, borderRadius: radius.control, backgroundColor: colors.accent, padding: 16, alignItems: 'center', justifyContent: 'center' },
  secondary: { backgroundColor: colors.raised, borderWidth: 1, borderColor: colors.border },
  dim: { opacity: 0.65 }, label: { color: colors.onAccent, fontSize: 15, fontWeight: '600' }, secondaryLabel: { color: colors.text },
});
