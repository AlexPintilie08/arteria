"""Generate a reproducible proposal evidence example without network access."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .analysis import analyze_snapshot
from .demo import fixture_snapshot, load_cached_snapshot
from .impact import evaluate_candidates
from .proposal_catalog import get_intervention_catalog
from .proposal_context import build_proposal_context
from .proposal_validation import validate_proposal_set
from .proposals import prepare_candidate_options


def run_proposal_demo(source: str = "fixture") -> dict[str, Any]:
    """Run analysis, candidate evaluation, packet generation, and validation offline."""
    if source not in {"fixture", "cache"}:
        raise ValueError("source must be 'fixture' or 'cache'; neither mode downloads OSM data.")
    data = fixture_snapshot() if source == "fixture" else load_cached_snapshot()
    analysis = analyze_snapshot(data)
    candidate_evaluation = evaluate_candidates(data, analysis=analysis)
    packet = build_proposal_context(data, analysis, candidate_evaluation)
    options = prepare_candidate_options(analysis, candidate_evaluation)
    validation = validate_proposal_set(options, data=data, candidate_evaluation=candidate_evaluation)
    return {
        "schema_version": "arteria.proposal-demo.v1",
        "demo": {
            "source_mode": source,
            "source": data.metadata.get("source"),
            "retrieved_at": data.metadata.get("retrieved_at"),
            "network_requests_made": False,
            "area_id": data.area.area_id,
        },
        "capability_catalog": get_intervention_catalog(),
        "evidence_packet": packet,
        "candidate_options": options,
        "validation": validation,
        "limitations": [
            "A candidate option is a hypothetical graph edit, not a construction recommendation.",
            "Candidate impacts are calculated from graph-node samples and are not observed journeys or traffic measurements.",
            "Physical feasibility and construction cost remain unknown or unsupported.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=("fixture", "cache"), default="fixture")
    parser.add_argument("--output", help="optional JSON file path for the generated packet and options")
    args = parser.parse_args()
    result = run_proposal_demo(args.source)
    serialized = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(serialized, encoding="utf-8", newline="\n")
        print(f"Proposal demo JSON: {path}")
    else:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        print(serialized, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
