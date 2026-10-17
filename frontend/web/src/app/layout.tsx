import type { Metadata, Viewport } from 'next';
import type { ReactNode } from 'react';
import '@fontsource/manrope/400.css';
import '@fontsource/manrope/600.css';
import '@fontsource/space-grotesk/500.css';
import '@arteria/shared/web.css';
import './globals.css';

export const metadata: Metadata = {
  title: 'ARTERIA — Iași',
  description: 'ARTERIA by ARION. Explorează Iași și pregătește scenarii pentru un oraș mai accesibil.',
};
export const viewport: Viewport = { themeColor: '#101820' };
export default function RootLayout({ children }: { children: ReactNode }) {
  return <html lang="ro"><body>{children}</body></html>;
}
