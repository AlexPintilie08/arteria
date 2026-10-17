# Structură și integrare

```text
frontend/
  web/src/
    app/
      layout.tsx     document și stiluri de bază
      page.tsx       / — prezentarea ARTERIA
      app/page.tsx   /app — produsul cu hartă și inspector
    components/      UI web
    features/        workspace, map, analysis, scenarios, comparison
    lib/             client și configurare web
  mobile/src/
    app/             native-stack și deep links
    components/      primitive native și safe areas
    features/        experiențele native
    lib/             configurare Expo publică
  shared/
    core/            contracte, HTTP, fixtures etichetate
    tokens/          tokenuri TypeScript și CSS
    tests/           transport și verificare browser

docs/frontend/       brief, instrucțiuni și prompt pentru AI
```

Contractele și limbajul vizual sunt comune; componentele DOM și native rămân separate. Workspace-urile expun sursa TS către Next.js și Metro fără build separat. Expo configurează automat monorepo-ul; nu adăuga aliasuri sau `watchFolders` fără o problemă demonstrată.

## Ce funcționează în bază

Web: shell adaptiv, navigație, repere Iași, selecție de straturi pentru cerere și previzualizare cu indicatori necunoscuți și surse inspectabile. MapLibre lazy-loaded reacționează la reper și redimensionare. Fără URL de stil, canvas neutru local, fără tiles sau geometrii inventate.

Site-ul folosește Next.js App Router: `app/page.tsx` este prezentarea publică la `/`; `app/app/page.tsx` este produsul la `/app`. Componenta interactivă se află în `features/workspace/Workspace.tsx`. Harta nu se montează pe prezentare și este importată prin `next/dynamic` cu `ssr: false` doar în produs. MapLibre 6 primește URL-ul workerului prin `new URL(..., import.meta.url)` și `setWorkerUrl`, conform [documentației oficiale](https://maplibre.org/maplibre-gl-js/docs/). Next.js generează resursa locală.

Android: Expo, native-stack, explorare, indicatori, scenarii, comparație, deep links `arteria://`, safe areas și controale de minimum 48dp. Harta nativă și apelurile UI la backend nu sunt implementate. Clientul HTTP și configurația sunt pregătite.

Comun: tipurile celor trei operații, POST cu timeout/anulare/erori, fixtures fără rezultate inventate și tokenuri. Tipizarea nu validează JSON la runtime. Backendul este autoritatea pentru geometrii și intervenții.

## Pornire

Node 22.12+ sau Node 24, din `frontend`:

```powershell
npm ci
npm run dev
```

Web: `http://localhost:3000`, implicit demo UI fără backend. Opțional copiază `web/.env.example` în `web/.env`; repornește Next.js după modificări. `NEXT_PUBLIC_MAP_STYLE_URL` trebuie să indice un stil MapLibre autorizat, cu atribuire corectă. Nu se livrează o sursă de tiles de producție în această inițializare.

Expo: `npm run mobile`. `npm run android` necesită emulator/dispozitiv disponibil. Expo Go trebuie să corespundă SDK-ului. SDK 58 a fost ales din template-ul oficial verificat în npm la inițializare.

Emulator Android → PC prin `10.0.2.2`; telefon fizic → IP-ul LAN al PC-ului. Pentru telefon, backendul necesită bind pe rețea și acces firewall; webul necesită CORS pentru originea locală. `EXPO_PUBLIC_*` și `NEXT_PUBLIC_*` sunt publice, fără secrete.

## Verificare și build

```powershell
npm run check
npm run export:android --workspace @arteria/mobile
```

Exportul Metro validează bundle-ul, nu produce APK și nu dovedește comportamentul nativ. Profiluri EAS pregătite în `mobile/eas.json`. Pentru APK: configurează propriul proiect/cont EAS, apoi `eas build --platform android --profile preview` din aplicația mobilă. Nu s-a creat proiect cloud. Profilul development necesită instalarea `expo-dev-client` înainte de utilizare.

În sandboxul Windows, Hermes poate să nu poată scrie în directorul temporar implicit. Pentru verificarea locală s-a setat `TEMP` și `TMP` la `frontend/.qa/tmp` înainte de export; exportul Hermes a trecut astfel, fără modificarea surselor sau dezactivarea compilării bytecode. Telemetria Expo a fost dezactivată pentru verificare. Nu a fost disponibil un emulator Android.

Audit npm la inițializare: 22 constatări tranzitive (15 high, 7 moderate), în lanțul Expo/Metro și uneltele native. `npm audit` propune inclusiv downgrade la Expo 44 / RN 0.72; nu s-a aplicat `--force`, deoarece ar rupe setul compatibil SDK 58. Dependențele native sunt fixate conform `expo/bundledNativeModules.json`; reevaluați patch-urile oficiale înainte de distribuirea aplicației. MapLibre este încărcat separat de interfața inițială prin Next.js dynamic import.

Scriptul `shared/tests/browser-smoke.cjs` poate verifica webul cu un Playwright instalat local: setați `PLAYWRIGHT_MODULE` la modul dacă nu este în rezoluția Node, apoi `node shared/tests/browser-smoke.cjs` cu serverul pornit. Folosește Chrome instalat, fără descărcarea unui browser; `PLAYWRIGHT_CHANNEL` poate selecta alt canal. Capturile sunt salvate în `.qa/`, ignorat de Git.

## Următoarele integrări

1. Backend: ID-uri și limite reale ale zonelor, schema Issue, legătura cu baseline și erori. Reperele `preview-*` nu sunt trimise în live; butonul web rămâne dezactivat până la integrare.
2. Hartă: stil autorizat, atribuiri, GeoJSON/tiles și disponibilitate. Checkbox-urile pregătesc cererea; nu comută straturi vizuale inexistente.
3. `/analyze`: validare runtime și stare de date pe ambele platforme. Nu construi baseline ID din analysis ID; contractul draft nu oferă încă legătura implementată.
4. Problemă → `/propose` → intervenție acceptată → `/evaluate`; comparații numai între valori compatibile.
5. MapLibre nativ: compatibilitate Expo/RN și plugin verificate înainte de instalare, apoi development build. Fără MapLibre GL JS în native.
6. Finisare vizuală, accesibilitate și test Android. Folosește `AI_INTERFACE_PROMPT.md` pentru interfața completă.
