# PrepOS AI — Scoring Engine Specification v1.1

Version: 1.1
Status: Implementation-Ready · Supersedes v1.0 for presentation/gating; **engine math unchanged except R3**
Supersedes: `SCORING_ENGINE_SPECIFICATION.md` (v1.0)
Driven by: approved recommendations R1–R8 in `SCORING_ENGINE_REVIEW.md`
Authoring lens: Founder · CPO · UPSC Domain Expert · Learning Scientist · Principal Architect

> **Scope of this version.** v1.1 introduces the **Engine Scores vs Display Scores** architecture, applies review recommendations **R1, R2, R4, R5, R6, R7, R8 exactly as proposed**, and applies **R3 via Option A** (recalculated Readiness). It adds **prediction gating rules**, **UI specifications**, **impacted API contracts**, and **migration notes**.
>
> **What does NOT change (guaranteed):** the Learning Graph, Revision Engine, Mentor Agent, and Preparation Twin **architectures are untouched**. All eight scores are still computed at full fidelity by deterministic engines (no LLM). The only formula whose *output value* changes is Readiness (R3 Option A); every other score's computation is byte-for-byte identical to v1.0.

---

## 0. Reading guide & relationship to v1.0

This document is a **delta + override layer** on top of v1.0. To implement v1.1:

1. Implement everything in v1.0 **§1 (Global Conventions), §2 (Mastery), §3 (Retention), §4 (Importance), §5 (Weakness), §6 (Revision Health), §8/§9 (Predictions), §10 (Interactions/Revision Priority)** unchanged.
2. **Replace** v1.0 §7 (Readiness formula) with **§4 of this document** (R3 Option A).
3. **Add** the new layers defined here: Engine/Display split (§3), prediction gating (§5), UI specs (§6), API contracts (§7).
4. Apply the small per-score presentation overrides in §2 (R1/R4/R5/R6/R7/R8).

Where this document and v1.0 disagree, **v1.1 wins**. Where v1.1 is silent, **v1.0 applies verbatim**.

| v1.0 section | v1.1 status |
|---|---|
| §1 Global Conventions | Unchanged (+ new constants in §8 here) |
| §2 Mastery | Engine: unchanged. **New derived view `MasteryNonMCQ`** added (§4.2 here) for Readiness only. |
| §3 Retention | Unchanged. **R6**: ship forgetting-curve visual (UI §6). |
| §4 Importance | Unchanged. **R5**: display label becomes "Exam Weight." |
| §5 Weakness | Engine: unchanged. **R1**: removed from student display; internal + faculty-aggregate only. |
| §6 Revision Health | Unchanged (stays a headline display score). |
| §7 Readiness | **CHANGED — R3 Option A** (see §4 here). Scale preserved 0–100. |
| §8 Predicted Prelims | Engine: unchanged. **R2**: gated on mock anchor (see §5). |
| §9 Predicted Mains | Engine: unchanged. **R2**: gated on evaluated-answer anchor (see §5). |
| §10 Interactions / Revision Priority | Unchanged. Weakness still consumed internally exactly as before. |

---

## 1. Change log (v1.0 → v1.1) — recommendation acceptance

| Rec | Title | Decision | Where applied |
|---|---|---|---|
| **R1** | Internalize Weakness | **Accepted as proposed** | §3 (Engine/Display), §2.5, §6.4, §7 |
| **R2** | Gate predictions on anchors; show as bands | **Accepted as proposed** | §5 (gating), §6, §7 |
| **R3** | De-duplicate Readiness sub-scores | **Accepted — Option A** (KnowledgeSub excludes MCQ; MCQSub independent; Readiness recalculated; 0–100 scale preserved) | §4 |
| **R4** | Confidence → overconfidence flag only | **Accepted as proposed** | §3, §2.4, §6.4 |
| **R5** | Unify display polarity/vocabulary; "Importance" → "Exam Weight" | **Accepted as proposed** | §2.3, §6.2 |
| **R6** | Ship forgetting-curve visual with Retention | **Accepted as proposed** | §6.3 |
| **R7** | Per-concept UI shows Mastery + Retention only | **Accepted as proposed** | §6.2 |
| **R8** | Readiness UI shows headline + top-2 drivers | **Accepted as proposed** | §6.2 |

**Predictive-power statement (unchanged from review):** R1, R2, R4–R8 are presentation/gating only and change no computed engine value. R3 Option A changes the Readiness *value* but **preserves the 0–100 scale** and **removes** the hidden MCQ double-count (effective MCQ weight corrected from ~0.32 back to the intended 0.20); validated population mean shift ≈ −0.06 points (negligible), and Knowledge↔MCQ sub-score correlation drops 0.95 → 0.76 (the residual is genuine shared skill, not formula coupling).

---

## 2. Per-score presentation overrides (R1, R4, R5, R6, R7, R8)

The **engine computation of every score is exactly as in v1.0**. This section only changes *who sees what* and *how it is labeled*.

### 2.1 Mastery (engine unchanged; display unchanged + R7)
- **Engine:** v1.0 §2 verbatim (40% MCQ / 30% Mains / 20% Revision / 10% Study, weight redistribution, shrinkage).
- **Display:** remains a per-concept **on-demand** display score (R7). Shown with Retention on the concept node; nothing else on the node except the Exam-Weight badge and the optional overconfidence flag.

### 2.2 Retention (engine unchanged; R6)
- **Engine:** v1.0 §3 verbatim (stability-modulated exponential; `power_law` illustration mode retained).
- **Display:** per-concept on-demand display score, **paired with the forgetting-curve visualization** (R6) rendered via the `power_law` mode (`retention_unit = (1 + t/27.5)^(−1.41)`), with markers at each successful revision showing the stability "bumps."

### 2.3 Importance → "Exam Weight" (R5; engine unchanged)
- **Engine:** v1.0 §4 verbatim. Internal name stays `importance`. Per-student copy rule (v1.0 §4.10) unchanged.
- **Display:** the **student-facing label is "Exam Weight"** everywhere a concept badge appears. Never shown as a 0–100 personal gauge; rendered as a small badge/band ("High / Medium / Low yield") on the node to avoid the "I'm 92% good" misread (review C5).

### 2.4 Confidence → overconfidence flag only (R4; engine unchanged)
- **Engine:** Confidence is still computed per v1.0 (self-assessment + response speed + consistency) and still feeds Weakness's overconfidence bonus.
- **Display (student):** **no Confidence gauge is ever shown.** The only surfaced derivative is a per-concept boolean **Overconfidence flag**, raised exactly when `confidence − mastery ≥ 25 AND mastery < 70` (identical to v1.0 §5.5). Rendered as a small warning chip on the concept node.

### 2.5 Weakness → internal + faculty-aggregate (R1; engine unchanged)
- **Engine:** Weakness is still computed per v1.0 §5 **and still consumed by Revision Priority** (v1.0 §10.4) exactly as before — prioritization quality is unchanged.
- **Storage change (R1):** Weakness is **no longer persisted as a standalone student-facing column** that can drift from its inputs. It is computed **on demand** (inline within Revision Priority and within faculty aggregation). The `student_concept_progress.weakness_score` column is **deprecated** for display and may be retained only as a nullable materialized cache for analytics (see migration §8).
- **Display (student):** **never shown.** Its consequence is surfaced instead, via the Mentor/Revision queue ("Revise X — you're forgetting a high-yield topic").
- **Display (faculty):** surfaced **only in aggregate** (batch/topic level) — see §3 and §6.5.

### 2.6 Revision Health (unchanged)
- Engine and display per v1.0 §6. Remains a **student headline** display score. (Higher = better; no change.)

---

## 3. Engine Scores vs Display Scores Architecture (new in v1.1)

This is the central structural addition. It cleanly separates **what the system computes** (full fidelity, all scores) from **what each role sees** (a curated, role-appropriate subset). It changes no engine math; it formalizes a presentation boundary.

### 3.1 Definitions

- **Engine Score** — computed and stored/derived by the deterministic scoring engines; consumed by the Learning Graph, Revision Engine, Preparation Twin, Mentor, analytics, and predictions. **Not necessarily shown to any user.** Source of truth.
- **Display Score** — a value surfaced in a UI for a specific **role**. Always derived from Engine Scores; never an independent computation. A Display Score is a *projection* of Engine Scores plus presentation rules (labels, bands, polarity, gating).

**Invariant:** every Display Score is a pure function of Engine Scores. No UI ever computes a score; it only renders Engine Scores through the display rules here. (This preserves blueprint Rule 4/7 and the v1.0 §1.5 determinism guarantee.)

### 3.2 Engine Scores (internal — all retained at full fidelity)

| Engine Score | Computed per | Granularity | Primary consumers |
|---|---|---|---|
| **Mastery** | v1.0 §2 | (student, concept) | Learning Graph, Readiness, Weakness, Mentor |
| **Retention** | v1.0 §3 | (student, concept) | Revision Engine, Readiness, Mentor |
| **Importance** | v1.0 §4 | (exam, concept) + per-student copy | Revision Priority, Readiness, Mentor |
| **Confidence** | v1.0 §2/§5 inputs | (student, concept) | Weakness (overconfidence), Twin |
| **Weakness** | v1.0 §5 (now on-demand, R1) | (student, concept) | Revision Priority, faculty aggregates |
| **Revision Priority** | v1.0 §10.4 | (student, concept) | Revision Engine scheduler |
| **Readiness Sub-scores** | §4 here (R3 Option A): `MasteryNonMCQ`-based `KnowledgeSub`, `RetentionSub`, `MCQSub`, `WritingSub`, `CASub`, `coverage` | per student | Readiness, Predictions, Mentor "drivers" |

> **Note:** "Readiness Subscores" are Engine Scores (per the approved list). The headline **Readiness** value itself is a **Display Score** (it is what students see), computed from these Engine sub-scores.

### 3.3 Display Scores — Student

| Display Score | Source Engine Score(s) | Visibility rule |
|---|---|---|
| **Readiness** | Readiness sub-scores (§4) | Always (headline) |
| **Revision Health** | Revision Health (v1.0 §6) | Always once any revision scheduled; else "—" |
| **Predicted Prelims** | Predicted Prelims (v1.0 §8) | **Only after Prelims mock anchor** (§5.1) |
| **Predicted Mains** | Predicted Mains (v1.0 §9) | **Only after evaluated-answer anchor** (§5.2) |
| **Mastery (concept)** | Mastery (v1.0 §2) | On-demand (concept node) |
| **Retention (concept)** | Retention (v1.0 §3) | On-demand (concept node) + forgetting-curve (R6) |
| **Exam Weight (concept)** | Importance (v1.0 §4) | On-demand badge (R5) |

**Explicitly NOT shown to students:** Confidence (gauge), Weakness (gauge), Revision Priority (raw), Readiness sub-scores (raw numbers — only the **top-2 drivers** per R8).

### 3.4 Display Scores — Faculty

Faculty/institute users see student Display Scores **plus** role-appropriate aggregates (faculty *can* interpret and act on these; students cannot — review §5 role-aware finding):

| Faculty Display Score | Source Engine Score(s) | Granularity |
|---|---|---|
| **(All student Display Scores)** | as §3.3 | per student |
| **Aggregated Weakness** | Weakness (v1.0 §5) | batch × topic/subject (mean/percentile) |
| **Aggregated Overconfidence** | overconfidence flag rate (from Confidence vs Mastery) | batch × topic |
| **Batch Readiness Distribution** | Readiness (§4) | batch (histogram / percentiles) |
| **Topic Risk Heatmaps** | Importance × mean Weakness × low mean Retention | batch × syllabus grid |

Aggregation rules: see §6.5. All faculty aggregates are **tenant- and batch-scoped** (blueprint multi-tenant rule) and are **derived** (never new computations).

### 3.5 Where the boundary is enforced (architecture, no engine change)

- **Engine Scores** are produced by the existing Learning Graph Service / Revision Engine / Twin builder (unchanged) and persisted/derived per v1.0 §10.1.
- A new **Score Presentation layer** (application layer, read-side only) maps Engine Scores → Display Scores per role, applying labels, bands, polarity (all "higher = better" for students, R5), gating (§5), and aggregation (§6.5).
- The Mentor still reads **Engine Scores** via tools (v1.0 §10.5) — it is not limited to Display Scores. The presentation layer governs **UI**, not the Mentor's reasoning inputs.

```
Engines (UNCHANGED)                      Presentation layer (NEW, read-only)
Learning Graph / Revision / Twin   ──►   Score Presentation Service
  produce Engine Scores                    ├─ Student projection  → Student Display Scores
  (Mastery, Retention, Importance,         │     (labels, bands, gating, top-2 drivers)
   Confidence, Weakness, RevPriority,      └─ Faculty projection  → Faculty Display Scores
   Readiness subscores)                          (tenant/batch-scoped aggregates)
        │
        └────────────► Mentor Agent (reads Engine Scores via tools, unchanged)
```

---

## 4. Readiness — Recalculated (R3, Option A)

**This replaces v1.0 §7.5.** Everything else in v1.0 §7 (purpose, range, interpretation bands, update frequency, anti-gaming) is **unchanged**.

### 4.1 The change in one sentence
v1.0's `KnowledgeSub` used **full Mastery**, which already contains 40% MCQ — so MCQ was counted twice (once in Knowledge, once in MCQSub). v1.1 redefines `KnowledgeSub` to use **`MasteryNonMCQ`** (Mastery computed from the non-MCQ channels only), leaving **MCQSub** as the sole MCQ channel. Weights and 0–100 scale are preserved.

### 4.2 New derived Engine value: `MasteryNonMCQ`

`MasteryNonMCQ` is Mastery computed by the **identical v1.0 §2 procedure**, but over the **non-MCQ components only** (`mains`, `revision`, `study`), with their weights renormalized to sum to 1.0 and the same shrinkage rule.

```
# Identical machinery to v1.0 §2.5, restricted to non-MCQ components:
components = {mains: 0.30, revision: 0.20, study: 0.10}      # base weights (sum 0.60)
active = components with n_j > 0
w'_j   = w_j / Σ_{k in active} w_k                            # renormalize over present non-MCQ channels
raw_nonmcq_unit = Σ_{j in active} w'_j · c_j                  # c_j = the SAME component values as v1.0 §2.3.1
n_nonmcq = n_mains + n_rev + n_study
masterynonmcq_unit = shrink(raw_nonmcq_unit, n_nonmcq, MASTERY_K_CONF=8, prior=0.0)
MasteryNonMCQ = round(100 · masterynonmcq_unit, 2)
```

- `MasteryNonMCQ` is an **Engine Score** (a Readiness sub-score input). It is **not** shown to students. The displayed per-concept **Mastery** remains full v1.0 Mastery (unchanged).
- If a concept has **no non-MCQ data** (only MCQs), `MasteryNonMCQ` is `null` for that concept → excluded from `KnowledgeSub`'s weighted mean (handled in §4.3). The MCQ signal for that concept still enters Readiness via `MCQSub`.

### 4.3 Recalculated Readiness formula (v1.1)

```
# --- Sub-scores (Engine Scores) ---
# R3 Option A: KnowledgeSub now uses MasteryNonMCQ (NO MCQ inside it):
KnowledgeSub = Σ_c (I_c · MasteryNonMCQ_c) / Σ_c I_c
               # sum over concepts c that HAVE non-MCQ data (MasteryNonMCQ_c ≠ null)
               # if NO concept has non-MCQ data → KnowledgeSub is absent (redistribute, see below)

RetentionSub = Σ_c (I_c · R_c) / Σ_c I_c                      # unchanged from v1.0
MCQSub       = 100 · recency_difficulty_weighted_accuracy     # unchanged from v1.0 (sole MCQ channel)
WritingSub   = 100 · (recent_mains_avg / 10)                  # unchanged; absent ⇒ redistribute
CASub        = 100 · ca_coverage_accuracy                     # unchanged; absent ⇒ redistribute

# --- Weights (UNCHANGED numerically; scale preserved) ---
# Knowledge 0.30 · Retention 0.25 · MCQ 0.20 · Writing 0.15 · CA 0.10
active = sub-scores with data
w'_j   = w_j / Σ_{k in active} w_k                            # redistribute over present sub-scores
base_readiness = Σ_{j in active} w'_j · Sub_j                 # 0–100

# --- Coverage penalty (UNCHANGED from v1.0) ---
coverage        = (#high-importance concepts with mastery data) / (#high-importance concepts)
coverage_factor = 0.5 + 0.5 · coverage
readiness = round(clamp(base_readiness · coverage_factor, 0, 100), 2)
```

**Why the scale is preserved.** `MasteryNonMCQ ∈ [0,100]` exactly like full Mastery, so `KnowledgeSub ∈ [0,100]` exactly as before. The five weights are numerically unchanged and still sum to 1.0 (with the same redistribution rule). Therefore `base_readiness ∈ [0,100]` and `readiness ∈ [0,100]` — identical bounds to v1.0. **No rescaling constant is needed** (validated: population mean shift ≈ −0.06 pts).

**Why this removes the double-count.** In v1.0 the effective MCQ weight inside Readiness (no-Writing/CA case) was `0.30·0.40 + 0.20 ≈ 0.32`. In v1.1, MCQ contributes **0** to `KnowledgeSub`, so its effective weight is exactly its intended `0.20`. The other channels (Mains/Revision/Study) now carry the full `KnowledgeSub` weight, as the 0.30 label always implied.

### 4.4 `coverage` clarification under R3
`coverage` is unchanged: "fraction of high-importance concepts with **any mastery data**" (MCQ *or* non-MCQ). A concept with only MCQ data still counts toward coverage and still contributes to `MCQSub`; it simply does not contribute to `KnowledgeSub` (which now needs non-MCQ evidence). This is intentional: "knowledge depth" beyond raw MCQ accuracy requires non-MCQ evidence.

### 4.5 Worked examples (recalculated)

**Example A — mid-stage UPSC aspirant (no Mains/CA), with non-MCQ data**
- Per-concept: full Mastery rollup gave `KnowledgeSub(v1.0)=62`. Now using non-MCQ channels, suppose `MasteryNonMCQ` rollup `KnowledgeSub(v1.1)=59` (slightly lower, since the strong MCQ signal is removed from it). `RetentionSub=58`, `MCQSub=66`.
- Writing & CA absent → active {K 0.30, R 0.25, MCQ 0.20} sum 0.75 → weights .40/.333/.267.
- `base = .40·59 + .333·58 + .267·66 = 23.6 + 19.3 + 17.6 = 60.5`.
- Coverage 0.70 → `coverage_factor = 0.85`. `readiness = 60.5·0.85 = 51.4` → **Readiness ≈ 51** (v1.0 gave ≈ 52; difference ≈ 1 pt, as expected — MCQ no longer double-lifts the score).

**Example B — full-channel, broad coverage**
- `KnowledgeSub(v1.1)=76` (non-MCQ), `RetentionSub=74`, `MCQSub=80`, `WritingSub=65`, `CASub=60`. Coverage 0.95 → factor 0.975.
- `base = .30·76+.25·74+.20·80+.15·65+.10·60 = 22.8+18.5+16+9.75+6 = 73.05`.
- `readiness = 73.05·0.975 = 71.2` → **≈ 71** (v1.0 gave ≈ 72; ≈ 1 pt lower; still matches the "~72%" dashboard intent within rounding).

### 4.6 Versioning
- Readiness formula version becomes **`readiness_v1_1`** (config `READINESS_FORMULA_VERSION`).
- A new Engine value `masterynonmcq_v1` is introduced (reuses Mastery machinery; `MASTERY_*` constants unchanged).
- No new tunable weights are introduced; the five `READINESS_W_*` constants are **unchanged**.

---

## 5. Prediction Gating Rules (R2; new in v1.1)

Predictions are **computed** by the engine whenever inputs exist (v1.0 §8/§9 unchanged), but are **displayed** only after their independent anchor exists. This removes the ~0.95 redundancy with Readiness in the unanchored regime (review §2.2) and prevents false precision.

### 5.1 Predicted Prelims — visibility gate

```
PRELIMS_MOCK_THRESHOLD = 1        # config: minimum full-length Prelims mocks (default 1)

prelims_display_state =
    HIDDEN     if n_prelims_mocks < PRELIMS_MOCK_THRESHOLD
    VISIBLE    otherwise
```

- **`n_prelims_mocks`** = count of completed **full-length Prelims mock** assessments (assessment type = `prelims_mock`), recency-weighted count `n_eff_mocks` used for `mock_trust` as in v1.0 §8.4.
- **HIDDEN state UI:** show a locked card — *"Take a full-length Prelims mock to unlock your Predicted Prelims."* Show **Readiness** as the live forward signal instead.
- **VISIBLE state UI:** render as a **band, not a bare point** (R2): display `[point − interval, point + interval]` (e.g., "Likely **78–88**"), always annotated "based on N mocks." The point may be shown secondarily inside the band.
- Engine continues to compute the value while HIDDEN (so the moment the gate opens, the number is ready and already mock-anchored).

### 5.2 Predicted Mains — visibility gate

```
MAINS_ANSWER_THRESHOLD = 10       # config: minimum evaluated Mains answers (default 10; = v1.0 low_confidence threshold)

mains_display_state =
    HIDDEN     if n_mains_eval < MAINS_ANSWER_THRESHOLD
    HIDDEN     if mains_eval_quality_gate_passed == false      # Master Plan D5 (unchanged dependency)
    VISIBLE    otherwise
```

- **`n_mains_eval`** = count of evaluated Mains/essay answers (AI- or faculty-graded), recency-weighted `n_mains_eff` for uncertainty (v1.0 §9.5).
- **HIDDEN state UI:** locked card — *"Write and submit at least 10 answers to unlock your Predicted Mains."* (Premium-tier gating applies per business plan.)
- **VISIBLE state UI:** band format (R2), always annotated provisional until `n_mains_eval` is comfortably above threshold; show example graded answers alongside (review §4 mitigation).
- The dependency on the **Mains-evaluation quality gate** (Master Plan D5) is **unchanged** from v1.0 §9.10.

### 5.3 Gating summary table

| Prediction | Gate metric | Default threshold | Pre-gate UI | Post-gate UI |
|---|---|---|---|---|
| Predicted Prelims | `n_prelims_mocks` | ≥ 1 mock | Locked card + show Readiness | Band "low–high (±band based on N mocks)" |
| Predicted Mains | `n_mains_eval` AND D5 gate | ≥ 10 answers + quality gate | Locked card | Provisional band + example graded answers |

### 5.4 Why gating preserves/improves predictive power
- The engine value is identical to v1.0; we only suppress *display* until an **independent** anchor (mock/answer) differentiates the prediction from Readiness.
- Post-gate, the prediction is dominated by `mock_trust`/answer data (v1.0 blend), so it carries genuine, non-redundant forecasting signal.
- Net: students never see a "prediction" that is merely Readiness in disguise (review §2.2), and once shown, it is a real, anchored forecast.

---

## 6. UI Specifications (new in v1.1)

These specify the **student** and **faculty** surfaces implied by R5–R8 and the Engine/Display split. They constrain the frontend (Next.js/shadcn per blueprint Part 7) but introduce **no new computation**.

### 6.1 Global display rules (R5)
1. **Polarity:** every student-facing gauge is **"higher = better."** Weakness (higher = worse) is never shown to students.
2. **Vocabulary:** `Importance` renders as **"Exam Weight"**; `MasteryNonMCQ`, `Confidence`, `Weakness`, `Revision Priority`, raw sub-scores are **never labeled or shown** to students.
3. **Bands & color:** standardized 4-band color scale (Green/Teal/Amber/Red) applied consistently; each surfaced score uses its v1.0 interpretation bands (Mastery §2.7, Retention §3.7, Readiness §7.7, Revision Health §6.7).
4. **Tooltips:** every surfaced number carries the one-line plain-language definition from review §6.4 (reproduced in §6.4 here).

### 6.2 Student dashboard layout

**Headline row (always):**
- **Readiness** — large dial, 0–100, with band label; below it the **top-2 drivers** dragging it down (R8), e.g., *"Low retention in Economy · Thin coverage in Ethics."* Drivers are computed by ranking the (weight × shortfall) contribution of each Readiness sub-score / weakest high-importance subjects (read-only projection of Engine Scores).
- **Revision Health** — dial, 0–100, band label; "—" if no revisions scheduled yet.
- **Predicted Score card** — **only if** a prediction is VISIBLE (§5). If both predictions HIDDEN, this slot shows the locked-card CTA ("Take a mock to unlock your prediction") instead of a number.

**Concept node (Learning Graph screen, on-demand) — R7:**
- Shows exactly **two gauges: Mastery and Retention**, plus:
  - **Exam Weight** badge (High/Medium/Low) — R5.
  - **Overconfidence** warning chip if the flag is set (R4) — *"You rate this high but results don't match yet."*
- Shows **nothing else** (no Weakness, no Confidence, no Revision Priority, no MasteryNonMCQ).

### 6.3 Retention forgetting-curve visual (R6)
- On a concept's Retention view, render the **forgetting curve** using `power_law` mode (`R(t) = 100·(1 + t/27.5)^(−1.41)`), with:
  - the current point marked at "today,"
  - vertical "revision bump" markers at each successful revision (where stability `S` increased),
  - a projected dashed curve forward to the exam date.
- Purpose: make Retention (review C3 "counterintuitive") intuitive and motivate revision.

### 6.4 Tooltip copy (ship verbatim; from review §6.4)
- **Readiness** — "How exam-ready you are right now, across the whole syllabus. Goes up as you learn, remember, and practice high-weight topics."
- **Revision Health** — "How well you're keeping up with the revisions we schedule. Your forgetting is under control when this is high."
- **Predicted Score** *(anchored)* — "Your likely exam score based on your mocks and practice. Shown as a range because no prediction is exact."
- **Mastery** — "How well you actually perform on this topic, from your tests and revisions."
- **Retention** — "How much of this topic you still remember today. It fades over time and jumps back up when you revise."
- **Exam Weight** — "How often this topic appears in the real exam. Spend more time on high-weight topics."
- **Overconfidence flag** — "You rate yourself high here, but your results don't match yet. Worth a focused revision."

### 6.5 Faculty surfaces (R1 role-aware; §3.4)

All faculty views are **tenant- and batch-scoped** and are **aggregations** of Engine Scores (no new computation).

| View | Definition | Aggregation |
|---|---|---|
| **Aggregated Weakness** | per (batch, subject/topic): mean and 75th-percentile of student **Weakness** (Engine §5) over students in the batch with data | mean, p75; min student-count threshold = 5 to display (privacy) |
| **Aggregated Overconfidence** | per (batch, topic): **share of students** whose overconfidence flag is set (Confidence−Mastery ≥ 25 ∧ Mastery < 70) | proportion 0–100% |
| **Batch Readiness Distribution** | per batch: histogram + p10/p50/p90 of student **Readiness** (§4) | histogram (deciles), percentiles |
| **Topic Risk Heatmap** | grid (rows = subjects/topics, cols = batches): risk = `Importance × mean(Weakness) × (1 − mean(Retention)/100)`, normalized 0–100 | cell color by risk band |

- **Min-cohort rule:** any aggregate over fewer than 5 students renders as "insufficient data" (prevents de-anonymizing individuals; aligns with DPDP concerns in Master Plan G9).
- Faculty can still drill into an individual student's **student Display Scores** (§3.3) — never into raw Weakness/Confidence per concept beyond what students themselves can see, except via the aggregate views above.

---

## 7. API Contracts Impacted (new in v1.1)

These are the **contract-level** changes (request/response shape and semantics). No engine endpoint's computation changes; the read endpoints gain gating/labels and drop internal scores from student payloads. (Endpoints follow blueprint Part 6 §22 `/api/v1` conventions.)

### 7.1 `GET /api/v1/analytics/dashboard` (student) — CHANGED
- **Removes** from the student payload: any per-concept `weakness_score`, `confidence_score`, `revision_priority`, and raw Readiness sub-scores.
- **Adds**: `readiness.drivers` (top-2), and a `predictions` object with **display state** rather than always-present numbers.

```jsonc
// Response (student) — v1.1 shape
{
  "readiness": {
    "value": 71,                       // Display Score (R3-recalculated)
    "band": "on_track",
    "drivers": [                       // R8: top-2 negative contributors
      { "label": "Low retention in Economy", "subject_id": "..." },
      { "label": "Thin coverage in Ethics",  "subject_id": "..." }
    ]
  },
  "revision_health": { "value": 84, "band": "good" },   // or "value": null → "—"
  "predictions": {
    "prelims": {
      "state": "hidden",               // "hidden" | "visible"   (§5.1)
      "unlock_hint": "Take a full-length Prelims mock to unlock your Predicted Prelims.",
      "band": null                     // when visible: { "low": 78, "high": 88, "based_on_mocks": 2 }
    },
    "mains": {
      "state": "hidden",               // §5.2
      "unlock_hint": "Submit at least 10 answers to unlock your Predicted Mains.",
      "band": null
    }
  }
}
```

### 7.2 `GET /api/v1/learning-graph/concepts/{concept_id}` (student) — CHANGED
- Student payload returns **only** display-relevant fields (R7):

```jsonc
{
  "concept_id": "...",
  "mastery":   { "value": 82, "band": "strong" },     // full v1.0 Mastery (display)
  "retention": { "value": 50, "band": "at_risk",
                 "forgetting_curve": {                  // R6 data for the visual
                   "model": "power_law", "tau": 27.5, "beta": 1.41,
                   "revision_markers": [ { "t_days": 7 }, { "t_days": 21 } ],
                   "exam_date": "2028-06-01" } },
  "exam_weight": { "band": "high" },                    // R5 (Importance, badge only)
  "overconfidence": true                                // R4 (flag only; no Confidence value)
  // NO weakness_score, confidence_score, masterynonmcq, revision_priority in student payload
}
```

- **Internal/Mentor endpoints** (e.g., `POST /internal/learning-graph/update`, tool-backing reads) **still return full Engine Scores** including Weakness/Confidence/MasteryNonMCQ — unchanged, because the Mentor reads Engine Scores (§3.5).

### 7.3 `GET /api/v1/mentor/today|week|month` — UNCHANGED contract, clarified semantics
- No shape change. Mentor explanations already cite Engine Scores (v1.0 §10.5). Clarification: Mentor may reference Retention/Importance ("Exam Weight") in student-facing copy, but must **not** surface a raw "Weakness"/"Confidence" number in student-facing text (use the consequence phrasing). This is a content rule, not a contract change.

### 7.4 New faculty endpoints (additive) — §3.4 / §6.5
```
GET /api/v1/faculty/batches/{batch_id}/weakness?dimension=subject|topic
GET /api/v1/faculty/batches/{batch_id}/overconfidence?dimension=topic
GET /api/v1/faculty/batches/{batch_id}/readiness-distribution
GET /api/v1/faculty/batches/{batch_id}/risk-heatmap
```
- All are **read-only aggregations** of Engine Scores, tenant/batch-scoped, enforcing the **min-cohort = 5** rule (return `{"status":"insufficient_data"}` below threshold). RBAC: `faculty` / `institute_admin` only.

### 7.5 Config surface (additive)
New `ScoringConfig` keys (all with defaults; no existing key changes):

| Key | Default | Purpose |
|---|---|---|
| `READINESS_FORMULA_VERSION` | `readiness_v1_1` | selects R3 Option A formula |
| `PRELIMS_MOCK_THRESHOLD` | `1` | Predicted Prelims visibility gate |
| `MAINS_ANSWER_THRESHOLD` | `10` | Predicted Mains visibility gate |
| `FACULTY_MIN_COHORT` | `5` | min students for any faculty aggregate |
| `PREDICTION_DISPLAY_FORMAT` | `band` | `band` \| `point_band` |

---

## 8. Migration Notes — Scoring Spec v1.0 → v1.1

A controlled, reversible migration. **No engine architecture changes**; the work is (a) one formula version bump (Readiness), (b) a presentation/gating layer, (c) faculty aggregates, (d) deprecating the stored Weakness column for display.

### 8.1 Data & schema changes

| Change | Action | Reversible? |
|---|---|---|
| Readiness version | Add `readiness_version` to `preparation_twins.prediction_profile` records; backfill on next nightly recompute. | Yes (revert formula version) |
| `MasteryNonMCQ` | Computed on the fly from existing components in the event log; **no new stored column required** (optional materialized cache `student_concept_progress.mastery_nonmcq` for query speed). | Yes |
| `student_concept_progress.weakness_score` | **Deprecate for display** (R1). Keep column nullable for analytics cache, OR stop writing it and compute on demand. Recommended: stop writing; compute inline. | Yes (resume writes) |
| Faculty aggregates | New read-side views/materialized rollups; additive. | Yes (drop views) |
| Config keys (§7.5) | Add with defaults. | Yes |

**No destructive migration.** All Engine Scores remain recomputable from the event log (v1.0 §1.5), so Readiness can be backfilled and reverted at will.

### 8.2 Backfill procedure (Readiness R3 Option A)
1. Deploy v1.1 engine with `READINESS_FORMULA_VERSION=readiness_v1_1` behind a flag.
2. Run a **shadow recompute**: compute `readiness_v1_1` alongside `readiness_v1_0` for all active students; log the delta distribution (expected mean shift ≈ −0.06 pts; |Δ| typically ≤ 2 pts).
3. Verify deltas are within tolerance (alert if any |Δ| > 5 pts → indicates a data anomaly, e.g., a concept with only MCQ data dominating Knowledge previously).
4. Flip the flag; the nightly job writes `readiness_v1_1` going forward. Old values retained with their version tag for audit.

### 8.3 Rollout sequence (safe order)
1. **Engine + config** (Readiness v1.1, MasteryNonMCQ, gating thresholds) — no UI yet, shadow-compute only.
2. **API read-side** (§7.1–7.2): start returning Display-Score-shaped payloads; **feature-flag** so old clients keep working until frontend ships.
3. **Frontend** (§6): student dashboard (headline + drivers), concept node (Mastery/Retention/Exam Weight/overconfidence), forgetting-curve visual, prediction locked-cards/bands.
4. **Faculty** (§3.4/§6.5/§7.4): aggregates + heatmaps behind RBAC + min-cohort rule.
5. **Decommission** student-facing Weakness/Confidence fields once all clients are on v1.1.

### 8.4 Backward compatibility & risk
- **API:** breaking change to student `dashboard`/`concept` payloads (fields removed). Mitigated by feature-flagged dual-shape responses during step 2–3; version the endpoints if external consumers exist.
- **Predictions:** students who previously saw an (unanchored) predicted number will now see a **locked card** until they take a mock/write answers. This is intended (removes false precision) but is a **visible UX change** — pair with an in-app explainer ("Predictions now unlock after a mock, so they're real forecasts").
- **Readiness:** values move by ≈1 pt on average (some concepts more). Communicate as a **precision improvement**, not a regression. Keep both versions in audit so any student question is answerable.
- **Mentor:** unaffected (still reads Engine Scores); only its **student-facing wording** must avoid raw Weakness/Confidence numbers (content rule, §7.3).

### 8.5 Test additions (on top of v1.0 §11 tests)
- **Readiness R3 golden tests:** the two recalculated examples in §4.5 (≈51, ≈71).
- **Scale-invariance test:** `readiness_v1_1 ∈ [0,100]` across random populations; population mean shift vs v1.0 within ±1 pt.
- **De-duplication test:** corr(`KnowledgeSub_v1_1`, `MCQSub`) < corr(`KnowledgeSub_v1_0`, `MCQSub`) on a fixed seed (assert the drop).
- **Gating tests:** Predicted Prelims `state=hidden` when `n_prelims_mocks=0`, flips to `visible` at threshold; Predicted Mains respects both the answer threshold AND the D5 quality gate.
- **Presentation/leak tests:** student `dashboard`/`concept` payloads contain **no** `weakness_score`/`confidence_score`/`masterynonmcq`/`revision_priority` (assert absence); faculty aggregates return `insufficient_data` below cohort of 5.
- **Polarity test:** every student Display Score is "higher = better" (no inverted gauge reaches the student payload).

---

## 9. Guarantees (restate)

1. **Learning Graph, Revision Engine, Mentor Agent, Preparation Twin architectures: unchanged.** v1.1 adds a read-side presentation layer and one formula version; it does not alter how these systems compute, store, or interact (v1.0 §10 holds verbatim).
2. **All eight scores still computed deterministically, no LLM.**
3. **Revision prioritization unchanged** — Weakness still feeds Revision Priority exactly as in v1.0 §10.4 (R1 changes display/storage, not consumption).
4. **Predictive power preserved or improved** — R1/R2/R4–R8 are presentation/gating; R3 Option A removes double-counting while preserving the 0–100 Readiness scale.
5. **Fully reversible** — every change is flag-gated and recomputable from the event log.

---

## Appendix A — v1.1 quick reference

| Score | Engine (compute) | Student display | Faculty display |
|---|---|---|---|
| Mastery | v1.0 §2 (unchanged) | concept, on-demand | per student |
| MasteryNonMCQ | **NEW** §4.2 (Readiness input) | hidden | hidden |
| Retention | v1.0 §3 (unchanged) | concept + curve (R6) | per student |
| Importance | v1.0 §4 (unchanged) | "Exam Weight" badge (R5) | per student + heatmap input |
| Confidence | v1.0 (unchanged) | hidden → overconfidence flag (R4) | overconfidence aggregate |
| Weakness | v1.0 §5 (unchanged compute; on-demand, R1) | **hidden** | **aggregate only** |
| Revision Priority | v1.0 §10.4 (unchanged) | hidden | hidden |
| Readiness sub-scores | §4 (R3 Option A) | hidden (top-2 drivers only, R8) | distribution input |
| **Readiness** | §4 (R3-recalculated) | **headline** | batch distribution |
| **Revision Health** | v1.0 §6 (unchanged) | **headline** | per student |
| **Predicted Prelims** | v1.0 §8 (unchanged) | **gated** (§5.1), band | per student (gated) |
| **Predicted Mains** | v1.0 §9 (unchanged) | **gated** (§5.2), band | per student (gated) |

## Appendix B — Recommendation → section index

| Rec | Implemented in |
|---|---|
| R1 (internalize Weakness) | §2.5, §3.2–3.4, §6.5, §7.2, §8.1 |
| R2 (gate predictions, bands) | §5, §6.2, §7.1, §8.4 |
| R3 Option A (Readiness recalculated) | §4, §7.5, §8.2, §8.5 |
| R4 (Confidence → flag) | §2.4, §3.3, §6.2/§6.4 |
| R5 (polarity + "Exam Weight") | §2.3, §6.1–6.2 |
| R6 (forgetting-curve visual) | §2.2, §6.3, §7.2 |
| R7 (concept node = Mastery + Retention) | §3.3, §6.2, §7.2 |
| R8 (Readiness headline + top-2 drivers) | §3.3, §6.2, §7.1 |

---

*End of Scoring Engine Specification v1.1. This version changes presentation, gating, and the Readiness formula (R3 Option A) only; the Learning Graph, Revision Engine, Mentor Agent, and Preparation Twin architectures and all other score computations remain exactly as defined in v1.0. Implement v1.0 first, then apply this delta layer.*
