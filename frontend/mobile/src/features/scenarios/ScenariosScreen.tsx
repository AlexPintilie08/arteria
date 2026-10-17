import { Text, View } from 'react-native';
import { alternativeLabels } from '@arteria/shared/fixtures';
import { Screen } from '../../components/Screen';
import { type } from '../../components/typography';
export function ScenariosScreen() {
  return <Screen><Text style={type.title}>O schimbare, trei perspective.</Text><Text style={type.body}>Selectează o problemă susținută de date înainte de a solicita alternative.</Text>{Object.entries(alternativeLabels).map(([key, label]) => <View key={key}><Text style={type.heading}>{label}</Text><Text style={type.small}>În așteptarea validării backendului</Text></View>)}<Text style={type.notice}>Nicio propunere AI generată. Efectele unei propuneri rămân ipoteze până la evaluare.</Text></Screen>;
}
