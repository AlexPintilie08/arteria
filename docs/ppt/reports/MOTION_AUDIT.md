# ARTERIA — motion audit

Audit and implementation: 18 October 2026. The authoritative file is the 10-slide `../ARTERIA.pptx`. The prior 13-slide working deck, including its Q&A appendices, is in `../archive/premium-motion-20261018/`.

## Shared transition and motion rules

All ten slides use PowerPoint **Fade Smoothly** at **0.45 seconds** and remain manually advanced. No slide advances on a timer. Text remains in its final position and appears through native opacity **Fade** (0.32–0.52 seconds). There are no moving text effects. Native **Wipe** (0.28 seconds) is reserved for four workflow and architecture connectors. Short 0.08–0.12 second delays stagger content without requiring presenter input.

Every content sequence starts automatically when its slide opens. Subsequent objects follow the previous reveal. There are **zero content-reveal clicks**; presenter clicks advance only to the next slide. “With Previous” is listed as **auto**, “After Previous” as **after**. Effect timing is recorded in `motion-plan.json`; PowerPoint COM readback is in `motion-com.json`.

## Slide-by-slide sequence

1. **Opening:** title Fade on entry (0.52 s), subtitle Fade after 0.10 s (0.42 s), product image Fade after 0.10 s (0.42 s). Supporting disclosures stay visible.
2. **The problem:** intervention node Fade on entry (0.40 s); four categories and their connectors follow with 0.08 s stagger (0.32 s each); the concluding question and disclosure Fade last (0.32 s).
3. **Existing alternatives:** comparison rows Fade in order (0.32 s each, 0.08 s stagger); the ARTERIA workflow statement follows (0.35 s, 0.10 s delay).
4. **The solution:** stage 1 Fades on entry (0.34 s); each connector Wipes after its stage (0.28 s); stages 2 and 3 Fade in order with 0.08 s stagger (0.34 s each).
5. **Product demonstration:** screenshot Fade on entry (0.45 s); three workflow labels follow in order (0.32 s each, 0.08 s stagger). Demo and synthetic-data disclosures stay visible.
6. **Technical architecture:** frontend Fades on entry (0.34 s); backend, connector, simulation, connector and status disclosure follow in order; the separately labelled planned LLM appears last. Nodes use 0.32–0.35 s Fade; connectors use 0.28 s Wipe.
7. **Business model:** customer segment Fade on entry (0.32 s); price and value/cost assumptions follow (0.32 s each, 0.08 s stagger). Unvalidated assumptions remain clear.
8. **Market validation:** Iași first case Fade on entry (0.34 s); outreach and continuation criterion follow (0.32 s each, 0.08 s stagger). No traction claim is introduced.
9. **Team:** all three member groups use equal Fade entrances (0.42 s), starting on entry with 0.12 s stagger. Names and roles keep equal prominence.
10. **Next step and close:** three priorities Fade in order (0.32 s each, 0.08 s stagger); the jury request follows (0.35 s, 0.12 s delay) and remains on screen.

## Deck-wide result

The plan contains **42 editable native effects: 38 Fade and 4 Wipe**. All reveal triggers are automatic or after-previous; no content group waits for a click. Object effects and stagger delays total **16.88 seconds** across the presentation; slide transitions add 4.50 seconds if the presenter advances immediately. These sequences fit within the existing 180-second speaking budget and do not advance slides automatically. Detailed structural validation and playback limits are in `PREMIUM_MOTION_QA.md`.
