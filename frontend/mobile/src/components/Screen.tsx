import type { PropsWithChildren } from 'react';
import { ScrollView, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { colors, spacing } from '@arteria/shared/tokens';
export function Screen({ children }: PropsWithChildren) {
  return <SafeAreaView style={styles.safe} edges={['bottom', 'left', 'right']}><ScrollView contentContainerStyle={styles.content}>{children}</ScrollView></SafeAreaView>;
}
const styles = StyleSheet.create({ safe: { flex: 1, backgroundColor: colors.background }, content: { padding: spacing.lg, gap: spacing.lg, flexGrow: 1 } });
