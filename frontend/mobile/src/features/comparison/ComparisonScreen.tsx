import { Text } from 'react-native';
import { Screen } from '../../components/Screen';
import { type } from '../../components/typography';
export function ComparisonScreen() {
  return <Screen><Text style={type.title}>Înainte. După.{ '\n' }Cu dovezi.</Text><Text style={type.body}>Evaluează un scenariu validat pentru a compara indicatorii cu situația inițială.</Text><Text style={type.notice}>Nicio evaluare disponibilă. SUMO: nicio rulare.</Text><Text style={type.small}>O înregistrare redată va afișa explicit „Replay”, identificatorul și timpul rulării originale.</Text></Screen>;
}
