# Aplicație Android ARTERIA — React Native + Expo

Aplicație nativă separată de site, cu TypeScript, navigație native-stack și ecrane inițiale.

- `index.ts`: înregistrarea aplicației Expo.
- `src/app/App.tsx`: navigație și configurarea aplicației.
- `src/features/`: explorare, indicatori, scenarii și comparație.
- `src/components/`: componente native reutilizabile.

Din directorul `frontend`: `npm run mobile` pornește Expo; `npm run android` deschide un emulator/dispozitiv disponibil.

Harta nativă și integrarea backend rămân de implementat. Exportul JS nu este APK. Site-ul React + Next.js se află în `../web`.
