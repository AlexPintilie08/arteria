import { createApiClient } from '@arteria/shared/api';
export const demoMode = process.env.NEXT_PUBLIC_DEMO_MODE !== 'false';
export const api = createApiClient(process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000');
