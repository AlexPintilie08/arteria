import { fileURLToPath } from 'node:url';

/** @type {import('next').NextConfig} */
const config = {
  transpilePackages: ['@arteria/shared'],
  turbopack: { root: fileURLToPath(new URL('..', import.meta.url)) },
};
export default config;
