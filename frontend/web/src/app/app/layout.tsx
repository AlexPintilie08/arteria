import type { Metadata } from 'next';
import type { ReactNode } from 'react';
import 'maplibre-gl/dist/maplibre-gl.css';
import '../../styles.css';

export const metadata: Metadata = { title: 'Spațiu de lucru — ARTERIA' };
export default function ProductLayout({ children }: { children: ReactNode }) { return children; }
