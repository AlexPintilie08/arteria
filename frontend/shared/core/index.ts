export type * from './contracts.ts';
export { createApiClient, ApiError } from './api.ts';
export {
  neighborhoods, layers, evidenceLabels, alternativeLabels,
  emptyIndicators, createDemoAnalysis,
  neighborhoodGeometries, demoIssuesByNeighborhood,
  type NeighborhoodGeometry, type DemoStudyIssue
} from './fixtures.ts';

