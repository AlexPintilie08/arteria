import { evidenceLabels } from '@arteria/shared/fixtures';
import type { EvidenceStatus } from '@arteria/shared/contracts';
export function EvidenceBadge({ status }: { status: EvidenceStatus }) {
  return <span className={`evidence evidence--${status}`}>{evidenceLabels[status]}</span>;
}
