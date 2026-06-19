# PrepOS AI — Scoring Engine Review

Version: 1.0
Status: Critical review of `SCORING_ENGINE_SPECIFICATION.md` v1.0
Reviewing lens: Senior Data Scientist · Learning Scientist · Principal Architect
Method: structural analysis of every formula + a Monte-Carlo simulation of a realistic (student × concept) population and the student-level roll-ups, to measure actual correlation and redundancy rather than assert it.

> **Bottom line up front.** The spec is mathematically sound and implementable. But it has **two clusters of statistical redundancy** that add engineering cost, dashboard clutter, and false precision without adding predictive power: (1) **Weakness** is ~93% reconstructable from Mastery + Retention; (2) the three student-level "outcome" scores — **Readiness, Predicted Prelims, Predicted Mains** — are **~0.95 mutually correlated** whenever mock/writing anchors are absent (i.e. for most V1 students). I recommend keeping all eight as *internal* computations but **collapsing the student-facing surface from 8 numbers to 3**, and demoting redundant scores to internal signals. None of these changes reduce predictive power; several *increase* it by removing double-counting.

---

## 0. How this review was produced (so the numbers are trustworthy)

I simulated a realistic population and computed each score exactly as the spec defines it, then measured the empirical correlation matrix and ran redundancy regressions (R² = "how fully is score X reconstructable from the others?").

- **Per-(student, concept) sample:** 6,000 latent-skill draws → derived Mastery, Retention, Confidence, Weakness, Importance, MCQ per the spec (incl. weight redistribution, shrinkage, stability-decay).
- **Student-level sample:** 4,000 students → derived Readiness, Predicted Prelims, Predicted Mains per the spec (incl. missing-channel redistribution and coverage penalty).

These are *structural* correlations — they arise from the formulas themselves, not from any particular dataset, so they will hold in production. Exact coefficients will shift with real data; the **ordering and magnitude class** (high/low) will not.

---

## 1. Scores that may be highly correlated

### 1.1 Measured correlation matrix — per concept

Pearson correlations across the 6,000-row simulated concept population:

|        | Mastery | Retention | Confidence | Weakness | Importance | MCQ |
|--------|:---:|:---:|:---:|:---:|:---:|:---:|
| **Mastery**    |  1.00 |  0.26 |  0.63 | **−0.84** | −0.02 | **0.88** |
| **Retention**  |  0.26 |  1.00 |  0.12 | **−0.68** | −0.01 | 0.19 |
| **Confidence** |  0.63 |  0.12 |  1.00 | −0.37 | −0.02 | 0.62 |
| **Weakness**   | −0.84 | −0.68 | −0.37 |  1.00 |  0.02 | −0.74 |
| **Importance** | −0.02 | −0.01 | −0.02 |  0.02 |  1.00 | −0.02 |
| **MCQ**        |  0.88 |  0.19 |  0.62 | −0.74 | −0.02 | 1.00 |

### 1.2 Measured correlation — student level

|  Pair | Correlation |
|---|:---:|
| Readiness ↔ Predicted Prelims | **0.96** |
| Readiness ↔ Predicted Mains | **0.95** |
| Predicted Prelims ↔ Predicted Mains | **0.95** |
| Readiness ↔ KnowledgeSub | 0.92 |
| Readiness ↔ MCQSub | 0.90 |
| KnowledgeSub ↔ MCQSub | 0.84 |

### 1.3 Interpretation of the correlations

| Correlation | Magnitude | Cause (from the formulas) | Verdict |
|---|---|---|---|
| **Mastery ↔ MCQ = 0.88** | very high | MCQ is **40%** of Mastery (largest single weight) and correlated with the other components. | Expected; MCQ is a *component*, not a peer score. Fine internally, but means MCQ-based Readiness sub-score **double-counts** Mastery (see §2.3). |
| **Weakness ↔ Mastery = −0.84**, **Weakness ↔ Retention = −0.68** | very high | Weakness = `0.55·(100−m) + 0.30·(100−R) + 0.15·err`. It is *defined* as the linear inverse of the two. | **Near-redundant** (see §2.1). |
| **Readiness ↔ Predicted Prelims/Mains ≈ 0.95** | extreme | All three roll up the same `KnowledgeSub / RetentionSub / MCQSub` with permuted weights; with no mocks/writing they are affine transforms of one another. | **Redundant as displayed numbers** until anchors exist (see §2.2). |
| **Confidence ↔ Mastery = 0.63** | moderate | Confident students tend to be skilled — but the *gap* is the signal. | **Not redundant** — but only useful as a *difference* (overconfidence), not as a standalone gauge (see §3). |
| **Mastery ↔ Retention = 0.26** | low | `S_base` scales with mastery, but Retention adds the orthogonal *time-since-study* dimension. | **Keep both** — genuinely independent information. |
| **Importance ↔ everything = ~0** | none | Importance is concept-level and student-independent by design. | **Keep** — it is the orthogonal "exam-yield" axis; carries unique signal. |

**Takeaway:** the high correlations are not accidents in the data; they are *baked into the formula definitions*. That is exactly what makes them addressable by simplification rather than by "collecting more data."

---

## 2. Scores that may be redundant

Redundancy is measured as R² — the fraction of a score's variance explained by *other scores you already compute*. High R² ⇒ the score carries little independent information.

### 2.1 Weakness Score — **redundant as an independent metric** (R² = 0.93)

| Reconstruction of Weakness from… | R² |
|---|:---:|
| Mastery + Retention | **0.925** |
| Mastery + Retention + error rate | **0.934** |

**Finding.** Weakness is **92–93% a deterministic linear recombination of Mastery and Retention** — which is unsurprising, because that is literally its formula. The only genuinely new ingredient is the **+10 overconfidence bonus**, and even that is derived from Confidence (already computed).

**This is not a bug — it is by design** (Weakness exists to be *multiplied by Importance* in Revision Priority). But it means:
- Weakness should **not** be presented to students as a separate gauge alongside Mastery and Retention — it would be showing the same information three times.
- Weakness should remain an **internal prioritization input** to the Revision Engine, not a dashboard KPI.

**Recommendation (R1):** Keep Weakness as an *internal* derived signal. Remove it from any student-facing surface. Do **not** persist it as a stored column that can drift from its inputs; compute it inline inside the Revision Priority calculation. (Predictive power unchanged — it is fully reconstructable.)

### 2.2 Predicted Prelims & Predicted Mains — **redundant with Readiness until anchored** (r ≈ 0.95)

**Finding.** With no full-length mock (Prelims) and no evaluated answers (Mains) — the state of essentially **every V1 student**, since Mains evaluation is a later phase — Predicted Prelims and Predicted Mains are built from the *same* `MCQSub / KnowledgeSub / RetentionSub` as Readiness, just with different weights. The simulation shows all three pairwise correlations ≈ 0.95.

In that unanchored regime, **Predicted Prelims ≈ a linear rescaling of Readiness**. Showing a student "Readiness 64", "Predicted Prelims 62±10", and "Predicted Mains 66±18" is presenting **one underlying quantity as three**, with spurious extra precision (the ± gives an illusion of a real forecast).

**The predictions only earn their independence once their anchors exist:** a real Prelims mock score (which is *not* a function of the other sub-scores) and real evaluated Mains answers. The spec already encodes this via `mock_trust` and `low_confidence` — the issue is purely **when we surface them**.

**Recommendation (R2):**
- **Gate the predicted scores on their anchors.** Show Predicted Prelims only after ≥1 full-length Prelims mock; show Predicted Mains only after ≥10 evaluated answers (the spec's own threshold). Before that, show **Readiness only**, with copy like "Take a full mock to unlock your predicted score."
- This removes the redundancy *exactly* in the regime where it exists, and keeps the predictions *exactly* where they add real, independent forecasting value. Predictive power is **increased**, because we stop presenting a derived number as an independent forecast.

### 2.3 Internal double-counting inside Readiness (not a separate score, but a redundancy)

**Finding.** Readiness weights `KnowledgeSub` (0.30, = importance-weighted Mastery) and `MCQSub` (0.20) — but MCQ is already 40% of Mastery, and the simulation shows `KnowledgeSub ↔ MCQSub = 0.84`. So MCQ performance is counted **twice** (once inside Mastery→Knowledge, once directly), inflating its effective weight to roughly 0.30·0.40 + 0.20 ≈ **0.32**, well above the intended 0.20.

**Recommendation (R3):** Make the Readiness sub-scores **orthogonal by construction**. Two clean options:
- **Option A (preferred):** redefine `KnowledgeSub` to use only the **non-MCQ** components of Mastery (Mains/revision/study), letting `MCQSub` be the sole MCQ channel. This makes the 0.20/0.30 weights *mean* what they say.
- **Option B:** drop `MCQSub` from Readiness entirely (MCQ already flows in via Mastery) and renormalize. Simpler, but loses the "Prelims-specific" emphasis.

Either removes the hidden over-weighting. (Predictive power preserved; weights become interpretable.)

### 2.4 Redundancy summary

| Score | Independent signal? | Redundancy verdict | Action |
|---|---|---|---|
| Mastery | Yes (core) | none | Keep, surface |
| Retention | Yes (time axis) | none (r=0.26 w/ Mastery) | Keep, surface |
| Importance | Yes (orthogonal) | none | Keep (mostly internal) |
| Confidence | Only as a *gap* | redundant as a standalone gauge | Demote to overconfidence flag (§3) |
| **Weakness** | Minimal (R²=0.93) | **redundant as a metric** | **Internalize** (R1) |
| Revision Health | Yes (behavioral, distinct) | none | Keep, surface |
| Readiness | Yes (composite KPI) | internal double-count (§2.3) | Keep, fix sub-scores (R3) |
| **Predicted Prelims** | Only when mock-anchored | **redundant w/ Readiness until anchored** | **Gate on mock** (R2) |
| **Predicted Mains** | Only when answer-anchored | **redundant w/ Readiness until anchored** | **Gate on answers** (R2) |

---

## 3. Places where users could become confused

Ranked by likelihood × harm. The core problem: the spec defines **eight scores, four of them per-concept**, and several measure subtly different things that *sound* the same to a student.

| # | Confusion | Why it confuses | Severity |
|---|---|---|---|
| **C1** | **Mastery vs Retention vs Confidence vs Weakness on the same concept node.** A student opens "Fundamental Rights" and sees four 0–100 numbers (e.g. M=82, R=50, Conf=70, Weak=35) that move differently. | Four gauges for "how good am I at this?" with no intuitive distinction between "understanding," "memory," "belief," and "danger." Most users cannot articulate the difference. | **High** |
| **C2** | **Two opposite polarities.** Mastery/Retention/Readiness are "higher = better"; **Weakness is "higher = worse."** Same 0–100 scale, inverted meaning. | A red "Weakness 75" next to a red "Mastery 25" looks like agreement but one is bad-high and the other bad-low. Classic dashboard error. | **High** |
| **C3** | **Retention can be high while Mastery is low (and vice versa).** A just-crammed weak topic shows R=95, M=30. | "I remember it but I'm bad at it?" is genuinely counterintuitive without a one-line explainer. | **Medium** |
| **C4** | **Three near-identical big numbers** (Readiness, Predicted Prelims, Predicted Mains ≈ same value) on the dashboard. | Users wonder why there are three, and which to trust; the ± on predictions implies a precision the model doesn't have pre-mock. | **Medium** (eliminated by R2) |
| **C5** | **"Importance" is about the *exam*, not the *student*.** It sits next to student scores on the node. | Students may read "Importance 92" as "I'm 92% important/good," conflating an exam property with a personal score. | **Medium** |
| **C6** | **Band boundaries differ per score** (Mastery 70–90 = "Strong"; Retention 60–85 = "Fading"; Weakness 50–75 = "Real weakness"). | The same number (e.g. 60) means different things on different gauges; color thresholds differ. | **Low–Medium** |
| **C7** | **Confidence as a displayed gauge.** Showing "Confidence 70" invites the student to treat it as an achievement, when its only purpose is to detect over/under-confidence. | Encourages self-report gaming and misreads a diagnostic as a goal. | **Medium** |

**Cross-cutting fix:** adopt a strict **display vocabulary and polarity rule** (all surfaced gauges are "higher = better"; never show a raw "Weakness" gauge), plus **one-line plain-language definitions** on hover for every surfaced number (drafts in §6.4).

---

## 4. Metrics that are difficult to explain to students

"Difficult to explain" = the honest one-sentence student explanation requires a concept the student doesn't have, or sounds arbitrary.

| Metric | Explainability | Why it's hard | Mitigation |
|---|---|---|---|
| **Mastery** | Easy | "How well you actually perform on this topic." Intuitive. | Keep as-is. |
| **Retention** | Medium | Requires the *forgetting-curve* idea ("you forget over time unless you revise"). Teachable, and motivating once taught. | Pair with the visual forgetting-curve (the spec's power-law mode) — turns a hard idea into an intuitive picture. |
| **Importance** | Easy | "How often this shows up in the real exam." Strong, motivating. | Keep; label "Exam Weight" to avoid C5. |
| **Revision Health** | Easy | "Did you do the revisions we scheduled?" Behavioral, obvious. | Keep. |
| **Readiness** | Medium | "Your overall exam-readiness." Intuitive headline, but the *internals* (importance-weighting, coverage penalty) are opaque — which is fine if we never ask the student to reproduce it. | Keep headline; expose the 3–4 driver sub-scores ("what's pulling it down") rather than the formula. |
| **Weakness** | Hard | It is a *composite of composites* (mastery + retention + error + overconfidence) with inverted polarity. No crisp one-liner that isn't just "low mastery + low retention." | **Don't show it.** Use it internally; surface its *consequence* ("Revise this — you're forgetting a high-yield topic"). |
| **Confidence** | Hard (and risky) | Explaining "we measure how confident you *seem* from self-reports and speed" invites gaming and feels surveillant. | **Don't show as a gauge.** Surface only the actionable derivative: an **"Overconfidence" warning** on specific topics. |
| **Predicted Prelims** | Medium–Hard | "Your likely score ± a range." The ± (uncertainty) is genuinely hard for lay users; pre-mock it's also not a real forecast. | Show **only after a mock**; express as a **range/band**, not a false point ("Likely 78–88"), and always with "based on N mocks." |
| **Predicted Mains** | Hard | All the Prelims difficulty **plus** subjective AI grading the student may distrust. | Show **only after ≥10 evaluated answers**; always show it as provisional + show example graded answers so the number is grounded. |

**Pattern:** the **hard-to-explain metrics (Weakness, Confidence, and unanchored predictions) are exactly the redundant ones from §2.** Internalizing them solves both problems at once.

---

## 5. Metrics that may not improve business outcomes

Business outcomes for PrepOS (from PRD + Part 8): **activation, daily/weekly engagement, retention/churn, paid conversion, institute adoption, and ultimately student exam success.** A metric "improves outcomes" only if seeing it changes student behavior in a way that helps those.

| Metric | Drives behavior? | Outcome impact | Verdict |
|---|---|---|---|
| **Readiness** | Strongly — single motivating north-star; goes up as you work. | High (engagement, retention, the "addictive" KPI per Part 7). | **Keep & feature.** |
| **Revision Health** | Strongly — a visible compliance streak drives the daily habit loop (the core retention mechanic). | High (DAU/retention). | **Keep & feature.** |
| **Mastery (per concept)** | Yes — tells the student where to act; powers "what to study." | High (directs effort, supports the Mentor's credibility). | **Keep, surface on demand.** |
| **Retention (per concept)** | Yes — the entire justification for revising; pairs with the forgetting-curve "aha." | High (drives revision, the moat). | **Keep, surface on demand.** |
| **Importance / Exam Weight** | Yes — motivates focus on high-yield topics; differentiates from "content dump" competitors. | Medium–High (focus, trust). | **Keep, mostly internal + node badge.** |
| **Predicted Prelims** *(anchored)* | Yes after a mock — concrete goalpost; strong motivator and a *conversion* hook ("unlock prediction"). | Medium–High **once anchored**; ~zero (and possibly negative via confusion) before. | **Keep, gated (R2).** |
| **Predicted Mains** *(anchored)* | Yes for serious aspirants writing answers — premium-tier value. | Medium once anchored; near-zero before. | **Keep, gated, premium (R2).** |
| **Weakness (as a displayed score)** | Weakly/negatively — a "Weakness 75" gauge can demotivate; the *action* ("revise X") drives behavior, not the number. | Low/negative as a gauge; high as an internal driver. | **Internalize (R1).** |
| **Confidence (as a displayed score)** | Weakly — invites gaming; "Confidence 70" is not actionable. | Low; the **overconfidence warning** is what helps. | **Internalize → warning only.** |

**Note on B2B (institutes).** Faculty/institute dashboards *do* benefit from aggregate Weakness and Confidence (e.g. "batch overconfidence on Polity") because faculty *can* interpret them and *act* (target a class). So the recommendation is **role-aware**: internalize/hide for students; expose *aggregated* for faculty.

---

## 6. Recommended simplifications (without reducing predictive power)

Design principle: **compute everything internally (full fidelity, all eight scores), surface little.** Predictive power lives in the engines; cognitive load lives on the screen. We cut the screen, not the engine.

### 6.1 The core recommendation — separate "engine scores" from "display scores"

| Layer | Scores | Audience |
|---|---|---|
| **Engine scores (internal, all retained)** | Mastery, Retention, Importance, Confidence, **Weakness**, Revision Priority, Readiness sub-scores | Engines, Mentor, analytics |
| **Student display scores (3 headline + 2 on-demand)** | **Headline:** Readiness · Revision Health · (anchored) Predicted Score. **On-demand per concept:** Mastery · Retention | Students |
| **Faculty display scores (aggregated)** | Above + **aggregated** Weakness & Overconfidence per batch/topic | Faculty/Institutes |

This single split resolves the redundancy (§2), the confusion (§3), and the explainability (§4) findings simultaneously, and **changes no formula** — so predictive power is fully preserved.

### 6.2 Specific changes

| ID | Recommendation | Resolves | Predictive impact |
|---|---|---|---|
| **R1** | **Internalize Weakness.** Compute it inline inside Revision Priority; never display to students; expose only *aggregated* to faculty. Don't store it as a standalone drift-prone column. | §2.1, C2, C7-adjacent, §5 | None (R²=0.93 reconstructable). |
| **R2** | **Gate predictions on their anchors.** Predicted Prelims only after ≥1 full mock; Predicted Mains only after ≥10 evaluated answers. Until then show Readiness alone. Present predictions as a **band** ("78–88"), never a bare point. | §2.2, C4, §4 | **Increases** (stops presenting a derived value as a forecast). |
| **R3** | **De-duplicate Readiness sub-scores.** Make `KnowledgeSub` use the non-MCQ mastery components so `MCQSub` is the only MCQ channel (Option A). Renormalize weights. | §2.3 | **Increases** (removes hidden 1.6× over-weighting of MCQ; weights become honest). |
| **R4** | **Demote Confidence to a flag.** Never show a "Confidence" gauge to students; surface only a per-topic **"Overconfidence" warning** when `confidence − mastery ≥ 25 and mastery < 70`. | C7, §4, §5 | None (the gap, not the level, was ever the signal). |
| **R5** | **Unify display polarity & vocabulary.** Every student-facing gauge is "higher = better." Rename "Importance" → **"Exam Weight"** on the node. Standardize band labels/colors across surfaced scores. | C2, C5, C6 | None (display only). |
| **R6** | **Pair Retention with the forgetting-curve visual.** Use the spec's `power_law` illustration mode to draw the decay + revision bumps. | C3, §4 | None (uses an already-specified function). |
| **R7** | **Per-concept: show two numbers, not four.** On a concept node show **Mastery** and **Retention** only (plus the Exam-Weight badge and an optional overconfidence flag). Weakness/Confidence are internal. | C1 | None. |
| **R8** | **Reduce Readiness sub-score sprawl in UI.** Show the headline Readiness + the **top 2 drivers dragging it down** ("Low retention in Economy; thin coverage in Ethics"), not all five sub-scores. | §4 (Readiness internals) | None. |

### 6.3 What the student dashboard becomes (before → after)

**Before (spec as written, naive surfacing):** Readiness, Predicted Prelims±, Predicted Mains±, Revision Health, and per concept {Mastery, Retention, Confidence, Importance, Weakness} = up to **5 student-level numbers + 5 per-concept numbers**.

**After (recommended):**
- **3 headline numbers:** Readiness · Revision Health · Predicted Score *(only once a mock exists; otherwise 2 headline numbers)*.
- **2 per-concept numbers** on demand: Mastery · Retention (+ Exam-Weight badge, + optional overconfidence flag).
- Everything else runs the engines and the Mentor's explanations underneath.

Roughly a **60% cut in surfaced numbers** with **zero loss of underlying signal**.

### 6.4 Plain-language definitions to ship with each surfaced score (hover/tooltip)

- **Readiness** — "How exam-ready you are right now, across the whole syllabus. Goes up as you learn, remember, and practice high-weight topics."
- **Revision Health** — "How well you're keeping up with the revisions we schedule. Your forgetting is under control when this is high."
- **Predicted Score** *(anchored)* — "Your likely exam score based on your mocks and practice. Shown as a range because no prediction is exact."
- **Mastery** (per concept) — "How well you actually perform on this topic, from your tests and revisions."
- **Retention** (per concept) — "How much of this topic you still remember today. It fades over time and jumps back up when you revise."
- **Exam Weight** (Importance) — "How often this topic appears in the real exam. Spend more time on high-weight topics."
- **Overconfidence flag** — "You rate yourself high here, but your results don't match yet. Worth a focused revision."

### 6.5 Predictive-power guarantee

None of R1–R8 alters a formula's inputs or coefficients. The engines still compute all eight scores at full fidelity; the Revision Engine and Mentor still consume Weakness, Confidence, and Importance exactly as specified. We are changing **what is shown and when**, not **what is computed**. Therefore:
- Revision prioritization quality: **unchanged** (still uses Weakness × Importance × Retention-gap × proximity).
- Readiness/prediction accuracy: **unchanged or improved** (R2/R3 remove double-counting and false-precision).
- Student outcomes: **improved** via reduced confusion and clearer calls-to-action.

---

## 7. Recommendations the spec should adopt — checklist

1. **R1 — Internalize Weakness** (engine-only; aggregate for faculty). [spec §5, §10.4]
2. **R2 — Gate Predicted Prelims/Mains on real anchors; display as bands.** [spec §8, §9]
3. **R3 — Orthogonalize Readiness sub-scores (KnowledgeSub = non-MCQ mastery).** [spec §7.5]
4. **R4 — Confidence → overconfidence flag only (no student gauge).** [spec §2/§5 inputs]
5. **R5 — Unify display polarity/vocabulary; "Importance" → "Exam Weight".** [UI layer]
6. **R6 — Ship the forgetting-curve visual with Retention.** [spec §3 power_law mode]
7. **R7 — Per-concept UI shows Mastery + Retention only.** [UI layer]
8. **R8 — Readiness UI shows headline + top-2 drivers.** [UI layer]

**Net effect:** same predictive engine, ~60% fewer numbers on screen, every surfaced number explainable in one sentence, and the two false-precision traps (unanchored predictions, double-counted MCQ) removed.

---

## Appendix A — Evidence (simulation results referenced above)

**Per-concept redundancy (R²: variance of a score explained by others):**

| Reconstruction | R² |
|---|:---:|
| Weakness ~ Mastery + Retention | 0.925 |
| Weakness ~ Mastery + Retention + error | 0.934 |
| Mastery ~ Retention (alone) | 0.069 |
| Mastery ~ MCQ (alone) | 0.772 |

**Student-level correlations:** Readiness↔PredPrelims 0.96 · Readiness↔PredMains 0.95 · PredPrelims↔PredMains 0.95 · Readiness↔Knowledge 0.92 · Readiness↔MCQ 0.90 · Knowledge↔MCQ 0.84.

*Method note:* coefficients come from a structural Monte-Carlo (6,000 concept rows; 4,000 student rows) implementing the spec's formulas. They quantify redundancy that is intrinsic to the formula definitions; production values will differ in the decimals but not in the high/low classification that drives every recommendation here.

## Appendix B — Mapping of findings → recommendations

| Finding | Recommendation(s) |
|---|---|
| Weakness ~93% reconstructable (§2.1) | R1 |
| Predictions ~95% collinear w/ Readiness pre-anchor (§2.2) | R2 |
| MCQ double-counted in Readiness (§2.3) | R3 |
| Confidence redundant as a gauge (§1.3, §2.4) | R4 |
| 4 numbers per concept / polarity flip (C1, C2) | R5, R7 |
| Retention counterintuitive (C3) | R6 |
| Three identical headline numbers (C4) | R2 |
| "Importance" misread as personal (C5) | R5 |
| Hard-to-explain metrics = redundant metrics (§4) | R1, R2, R4 |
| Some metrics don't drive outcomes (§5) | R1, R4 (role-aware) |

---

*End of Scoring Engine Review v1.0. All recommendations preserve the deterministic engine in `SCORING_ENGINE_SPECIFICATION.md`; they change the **presentation and gating** of scores, not their computation. Suggested next step: fold R1–R8 into a spec v1.1 (engine-vs-display split in §10, prediction gating in §§8–9, Readiness sub-score fix in §7).*
