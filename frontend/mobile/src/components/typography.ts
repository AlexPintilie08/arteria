import { StyleSheet } from 'react-native';
import { colors } from '@arteria/shared/tokens';
export const type = StyleSheet.create({
  title: { fontSize: 32, fontWeight: '600', color: colors.text, letterSpacing: -1 },
  heading: { fontSize: 22, fontWeight: '600', color: colors.text },
  body: { fontSize: 16, lineHeight: 25, color: colors.muted },
  small: { fontSize: 13, lineHeight: 21, color: colors.muted },
  notice: { fontSize: 13, lineHeight: 21, color: colors.warning },
});
