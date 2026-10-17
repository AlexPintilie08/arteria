import { NavigationContainer, DarkTheme } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { colors } from '@arteria/shared/tokens';
import { ExploreScreen } from '../features/map/ExploreScreen';
import { AnalysisScreen } from '../features/analysis/AnalysisScreen';
import { ScenariosScreen } from '../features/scenarios/ScenariosScreen';
import { ComparisonScreen } from '../features/comparison/ComparisonScreen';
import type { RootStackParamList } from './navigation';
const Stack = createNativeStackNavigator<RootStackParamList>();
const theme = { ...DarkTheme, colors: { ...DarkTheme.colors, primary: colors.accent, background: colors.background, card: colors.surface, text: colors.text, border: colors.border } };
export default function App() {
  return <SafeAreaProvider><StatusBar style="light" /><NavigationContainer theme={theme} linking={{ prefixes: ['arteria://'], config: { screens: { Explore: '', Analysis: 'analysis/:neighborhoodId', Scenarios: 'scenarios', Comparison: 'comparison' } } }}><Stack.Navigator screenOptions={{ headerTintColor: colors.text, headerStyle: { backgroundColor: colors.surface }, contentStyle: { backgroundColor: colors.background } }}><Stack.Screen name="Explore" component={ExploreScreen} options={{ title: 'ARTERIA' }} /><Stack.Screen name="Analysis" component={AnalysisScreen} options={{ title: 'Indicatori' }} /><Stack.Screen name="Scenarios" component={ScenariosScreen} options={{ title: 'Scenarii' }} /><Stack.Screen name="Comparison" component={ComparisonScreen} options={{ title: 'Comparație' }} /></Stack.Navigator></NavigationContainer></SafeAreaProvider>;
}
