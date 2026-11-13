# Decisions as interview answers

### Why the name casegate and not evalgate?  (docs/adr/0001-name-casegate.md)
**Answer:** the brief's name `evalgate` was taken on PyPI three times, so the project uses `casegate` everywhere.
**Trade-off:** a less obvious name in exchange for a name that a search finds as mine.
**Evidence:** PyPI `evalgate` 0.3.0, `evalgate-ai` 0.6.0, `evalgate-cli` 0.2.0 existed on 2026-11-11 (FACTS.md §2).
**At 10x:** no change.

### Why must every scorer pass, and not a weighted score?  (docs/adr/0002-case-passes-when-every-scorer-passes.md)
**Answer:** a case passes only when every scorer passes; the mean score is for reports only.
**Trade-off:** adding a scorer can only make a case harder to pass; no partial credit across scorers.
**Evidence:** with weights, a good judge score can hide a wrong tool trajectory; with all-must-pass, every failed case names a failed scorer and a reason.
**At 10x:** keep it; add per-scorer pass rates to spot a scorer that fails too often.

### Why are errors not failures?  (docs/adr/0003-errors-are-not-failures.md)
**Answer:** error repeats leave the pass-rate denominator and have their own gate limit, `--max-errors` (default 0).
**Trade-off:** two numbers to read instead of one.
**Evidence:** if errors counted as fails, an API outage would look like a regression; if they were ignored, an outage could pass the gate in silence.
**At 10x:** alert on error rate separately and retry whole runs, not only calls.

### Why a tiny two-adapter judge client and not litellm?  (docs/adr/0004-judge-client-two-adapters.md)
**Answer:** a `JudgeClient` protocol with an Anthropic adapter and an OpenAI-compatible adapter.
**Trade-off:** each new provider needs about 60 lines.
**Evidence:** the current Anthropic SDK rejects `temperature` (FACTS.md §4.3), so the adapters must differ anyway; litellm would make the library too big to read in one sitting.
**At 10x:** batch judge calls (Message Batches at half price).

### Why two caches and not one?  (docs/adr/0005-two-caches.md)
**Answer:** target outputs and judge results are cached apart, keyed by content.
**Trade-off:** two key schemes to get right.
**Evidence:** a rubric edit then re-grades the same outputs and costs only judge calls, about $0.0021 each (FACTS.md §4.2), instead of re-running the agent.
**At 10x:** move the cache to object storage shared by CI runs.

### Why set the tolerance from measured variance?  (docs/adr/0006-gate-tolerance-from-measured-variance.md)
**Answer:** max-drop = 2 × the measured std of the suite pass rate across 5 repeats, at least 0.02.
**Trade-off:** no formal statistical test; the tolerance must be re-measured when the suite changes.
**Evidence:** with 15 cases and 1 repeat, one flipped case moves the pass rate by 6.7 points, so a fixed 0.03 fails on noise. Measured std: 0.037 over 5 repeats (`evals/baseline.json` `summary.pass_rate_std`), so max-drop is 0.08 (`evals/tolerance.json` `max_drop`). It was 0.14 before the toy-agent@5 citation fix cut the noise (`04-failures.md`). The live gate passed the baseline against itself; at 0.08 it lets a drop of one case (0.067) through and blocks two (0.133) (FACTS.md §8).
**At 10x:** more cases shrink the noise; add a paired test per case.

### Why the "Lab instrument" look?  (docs/adr/0007-design-direction-lab-instrument.md)
**Answer:** dark, one signal colour, monospace, chosen from three live options.
**Trade-off:** less loud than the hazard-stripe option.
**Evidence:** the hazard stripes competed with the red/green status signal; the light option fought the dark terminal used in the videos.
**At 10x:** no change.

### Why read the baseline from the base branch?  (docs/adr/0008-baseline-from-base-branch.md)
**Answer:** on a pull request, the gate compares with `evals/baseline.json` from `main`, and a PR that edits the baseline needs the label `baseline-update`.
**Trade-off:** baseline updates are a separate, labelled step.
**Evidence:** otherwise a regression PR could lower its own bar in the same diff.
**At 10x:** store baselines as signed artifacts per release.

### Why no temperature 0 for the judge?  (FACTS.md §4.3)
**Answer:** the Anthropic API version 2026-10-21 and SDK 2.8.0 reject sampling parameters, so the judge uses structured output, a strict prompt and optional median-of-k samples.
**Trade-off:** judge scores vary; casegate measures that instead of hiding it.
**Evidence:** 0.8, 0.85, 0.8 on the same reply (FACTS.md §4.2).
**At 10x:** k = 3 samples on must-pass cases only, as the toy suite already does.

### Why HyperFrames for the launch videos and not Remotion or a screen recording?  (launch/SPEC.md, launch/REVIEW.md)
**Answer:** the videos are HTML compositions rendered by HyperFrames, so the real 3D logo scene, the DESIGN tokens and the IBM Plex fonts are the same code and files as the site.
**Trade-off:** HyperFrames needs every animation to be seek-safe (a function of time only), so the logo cycle and the case label had to be written as pure functions of the frame (`launch/film/compositions/gate.html:145-150` `cycleFrame`, `launch/film/compositions/run.html:97-101`).
**Evidence:** `launch-film.mp4` measures 45.000000 s at 30 fps, 1350 frames, and the thud peak lands 0 frames from the arm drop (`docs/assets/runs/launch-assets-m5.json`, launch/REVIEW.md "Sync").
**At 10x:** one shared data file for the frame times, so picture, sound clips and the bed script read the same numbers.

### Why rebuild the PR comment in HTML and not show the screenshot?  (launch/REVIEW.md "Creative calls")
**Answer:** the card is set in HTML at about 1.6× from the real comment text, because the 828 px screenshot goes soft at 1080p.
**Trade-off:** a transcription can hold a typo, and the screen is no longer a pixel copy of GitHub.
**Evidence:** every value on the card is in `docs/assets/demo-pr-regression/casegate-comment.md` (BLOCKED) or `docs/assets/pr-comment-passed.png` (PASSED); launch/SPEC.md lists the source of each figure.
**At 10x:** render the comment from the Markdown with the same code GitHub uses, so the card cannot drift from the text.
