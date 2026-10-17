# Hackathon roadmap

The sequence prioritizes a working end-to-end demo and keeps geographic analysis reusable across Iași neighborhoods. Dates and effort should be adapted to the hackathon length; each stage should end with a demonstrable result.

## 1. Agree on one bounded scenario

Choose a small, data-supported Iași area and one evidence-backed mobility question. Record the boundary, source snapshot, licensing notes, available layers, and a measurable baseline. Keep the workflow generic enough to accept another area identifier.

## 2. Establish the vertical slice

Build the smallest useful MapLibre map, area selection, typed API client, FastAPI contract, and one reproducible network preparation path. Return one or two honest, unit-labeled indicators and provenance. Make unavailable data visible as unknown.

## 3. Add constrained interventions and comparison

Implement a small versioned catalog of supported intervention types. Generate structured minimal, moderate, and transformative proposals using the cloud model, validate every proposal, then apply one selected change to a scenario copy. Recompute a deterministic geographic indicator and show Before/After with assumptions. If model access is unavailable, keep the workflow demonstrable with an explicitly labeled non-LLM proposal fixture; do not label it as AI-generated.

## 4. Finish the functional demo

Add issue selection on the map, clear provenance and uncertainty displays, loading/error states, and an end-to-end walkthrough. Test another neighborhood boundary or area identifier to verify that the first scenario did not hard-code the application to one location.

## 5. Expand urban analysis modules

Add walking and cycling accessibility, connectivity, transit access, parking, green-space, buildings, and points-of-interest measures as appropriate to data quality. Prioritize methods with explainable inputs and units. Document coverage and limitations before adding more indicators.

## 6. Add SUMO when inputs support it

Create a bounded vehicle demand scenario with documented assumptions. Add a small live CPU run if it fits interactive timing, plus a reproducible offline run with fixed inputs and captured versions. Show stored run replay with an explicit replay label. Keep geographic calculations available without SUMO.

## 7. Polish and harden

Improve map performance, layer hierarchy, transitions, responsive behavior, and Before/After visualization. Validate API errors, geometry constraints, provenance propagation, and failure paths. Review data licensing, provider secret handling, and reproducibility before a public demo.

## Demo completion criteria

- A user can select an area in Iași and see at least one sourced analysis result.
- The user can select an issue, request or inspect constrained intervention alternatives, and apply a supported option.
- The application recalculates at least one real geographic indicator and compares it with the baseline.
- Unknown data, estimates, and calculated results are visibly distinct.
- No LLM output is presented as a simulation measurement.
- The same workflow accepts another area without changing its core implementation.
