# ARTERIA — premium motion QA

Date: 18 October 2026, Europe/Bucharest. The sole active editable master is `../ARTERIA.pptx`; its static ten-page PDF export is `../ARTERIA-Submission.pdf`.

## Guidance and implementation basis

Read before editing:

- Repository PowerPoint editing and QA instructions: [`.agents/skills/pptx/SKILL.md](../../../.agents/skills/pptx/SKILL.md) — edit existing decks through their native package, preserve source styles and content, validate the PowerPoint package, and render every slide for visual inspection.
- Presentations skill: [`presentations/SKILL.md`](C:/Users/fagat/.codex/plugins/cache/openai-primary-runtime/presentations/26.1015.12040/skills/presentations/SKILL.md) and its [`template_following.md`](C:/Users/fagat/.codex/plugins/cache/openai-primary-runtime/presentations/26.1015.12040/skills/presentations/references/template_following.md) — work from a copy, preserve the supplied design, and check exported slides against the source.

Microsoft's PowerPoint object-model reference confirms the native Fade and Wipe effect IDs; `Sequence.AddEffect` targets a shape and accepts an animation trigger; `Timing` exposes duration and delay; and `SlideShowTransition` supports transition duration and manual advance. The build uses these documented interfaces:

- [MsoAnimEffect enumeration](https://learn.microsoft.com/en-us/office/vba/api/powerpoint.msoanimeffect)
- [Sequence.AddEffect](https://learn.microsoft.com/en-us/office/vba/api/powerpoint.sequence.addeffect)
- [Timing object](https://learn.microsoft.com/en-us/office/vba/api/powerpoint.timing)
- [SlideShowTransition object](https://learn.microsoft.com/en-us/office/vba/api/powerpoint.slideshowtransition)
- [SlideShowSettings.Run](https://learn.microsoft.com/en-us/office/vba/api/powerpoint.slideshowsettings.run) and [SlideShowView.Next](https://learn.microsoft.com/en-us/office/vba/api/powerpoint.slideshowview.next)

The implementation applies editable native entrance effects to existing semantic groups. Text stays at its final position and appears with opacity Fade; there are no Float or other moving text effects. No video overlay or rendered replacement is used. Morph is not used because the consecutive slides do not share a meaningful matched composition. Exit, emphasis and motion-path effects were reviewed and omitted; the story calls for clear entrances and stable final states.

## Prior issues and final motion

The 13-slide working deck previously used Fade Smoothly transitions at 0.55 seconds. It had 43 native object effects, but slides 3, 6, 7, 8 and 10 required three or four separate reveal clicks; slide 2 alternated click and automatic triggers between branches. The implementation and exact before/after order for every slide are in [`MOTION_AUDIT.md`](MOTION_AUDIT.md).

The final deck uses PowerPoint **Fade Smoothly**, 0.45 seconds, on all ten slides. Every slide remains manually advanced, with no automatic slide advance. It contains 42 native editable object effects: **38 Fade and 4 Wipe**. Wipe is reserved for four diagram connectors; all connectors appear only after their related stage. Every content reveal starts automatically on slide entry and then follows the prior reveal with short delays. There are **zero content-reveal clicks**; presenter clicks only advance to the next slide. The current implementation and explicit future LLM disclosure remain separate on slide 6.

The motion timeline records each target, trigger, delay and duration in `motion-plan.json`. PowerPoint COM readback is in `motion-com.json`. `apply_motion.ps1` removes the existing sequence before creating this plan, applies one consistent transition, and verifies the expected ten-slide count. Object effects plus their stagger delays total **16.88 seconds** across the presentation; transitions add **4.50 seconds** when every slide advances. The longest reveal sequence is 2.61 seconds on slide 6. The speaker-note budget remains **180 seconds**: 25, 20, 10, 50, 30, 10, 10, 10 and 15 seconds for slides 2–10; slide 1 is pre-roll. The presenter can speak while effects run, and no slide progresses by itself.

## Validation and playback

The complete build was run from the source scripts: `build_deck.py` created the corrected working deck; `audited_content.py` derived its exact ten-slide submission; PowerPoint 16.0 COM applied motion and exported the slide renders and PDF; `qa_deck.py` and the repository PowerPoint package validator passed before publishing.

Structural and content checks confirmed:

- Exactly ten slides and ten speaker-note sets in the authoritative deck.
- All 42 animation targets resolve to existing slide shapes. The number, effect ID, trigger, duration and delay for each sequence match the generated plan; no duplicate or orphaned target was found. No content effect uses a click trigger.
- All ten slides use Fade Smoothly at 0.45 seconds, retain manual advance and have no timed advance.
- Text and speaker notes match the previously audited ten-slide submission recursively through grouped objects. PowerPoint reports 116 text regions checked, with zero overflow and zero out-of-canvas objects.
- The PDF export has ten pages. The deck and PDF are generated in the same rebuild. Only `ARTERIA.pptx` remains as an active PPTX in `docs/ppt/`.
- The prior 13-slide audited deck, pre-motion ten-slide deck and PDF, previous motion deck and PDF, and previous preview are preserved under `archive/premium-motion-20261018/`.
- The build pipeline reproduced the final result from source. The published SHA-256 is recorded in `canonical-publication.json`.

PowerPoint 16.0 COM started a native slide show and stepped through all ten slides. Content sequences completed automatically on entry, and all manual slide advances worked without reveal clicks. This confirms the native timeline can run and advance as intended. Intermediate animation frames were **not visually inspected** because this session had no screen-capture surface. Static PNG and PDF renders confirm final states and layout only; they cannot prove the appearance of motion between frames. A presenter should preview F5 once on the target display before the three-minute pitch.

## Rebuild and compatibility

Run `docs/ppt/scripts/rebuild.ps1` on Windows with desktop PowerPoint and the bundled Python runtime. The script creates the ten-slide master and synchronized PDF only after motion, rendering, text-bound and package checks pass. It moves redundant editable versions to the motion archive and updates the README. No other PowerPoint window is closed by the scripts. `ARTERIA-Submission.pdf` is a static PDF and does not carry animation behavior.
