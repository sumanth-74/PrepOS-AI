# PrepOS AI — Scoring Engine Specification

Version: 1.0
Status: Implementation-Ready (deterministic, no LLM dependency)
Authoring lens: Founder · Chief Product Officer · UPSC Domain Expert · Learning Scientist · Principal Architect
Scope: The complete, deterministic definition of all eight platform scores. This document is the **single source of truth** for the scoring layer. A backend engineer must be able to implement every score from this document alone.

> **Architecture law (from blueprint Part 3 §11 and Part 5 §1):** these scores are computed by **deterministic engines, not LLMs**. The Learning Graph and Preparation Twin are the source of truth; AI only *interprets and explains* these numbers. No score in this document may call a language model. Every value is reproducible: same inputs → same output, always.

---

## 0. How to read this specification

Each score is defined with the exact 11 sections requested:
Business Purpose · Why it exists · Inputs · Input Weightages · Formula · Output Range · Interpretation · Examples · Update Frequency · Edge Cases · Anti-Gaming Mechanisms.

The scores form a dependency chain. Build them in this order (matches the dependency graph in the Master Plan):

```
Importance ─┐
            ├─► Mastery ──► Weakness ──┐
Retention ──┘                          ├─► Revision Priority (engine) ──► Revision Health
                                       │
Mastery + Retention + Weakness + ──────┴─► Readiness ──► Predicted Prelims / Predicted Mains
Revision Health + Assessment data
```

**Teaching note (for an engineer new to this):** a "score" here is just a pure function. You give it numbers (inputs), it returns a number 0–100 (or a band/interval). The hard part is not the arithmetic — it is (a) *normalizing* messy real inputs onto a 0–1 scale, (b) handling *missing data* (a brand-new student has almost none), and (c) preventing students from *gaming* the number. Every score section below handles all three explicitly.

---

## 1. Global Conventions (read this first — every score depends on it)

These conventions are shared infrastructure. Implement them once, in the domain layer, and reuse everywhere.

### 1.1 Symbols and units

| Symbol | Meaning | Unit |
|---|---|---|
| `t` | elapsed days since an event | days (float, can be fractional) |
| `m` | mastery score of a concept | 0–100 |
| `R` | retention score of a concept | 0–100 |
| `I` | importance score of a concept | 0–100 |
| `W` | weakness score of a concept | 0–100 |
| `S` | memory **stability** (how slowly a memory decays) | days |
| `now` | current evaluation instant | UTC timestamp |
| `exam_date` | student's target exam date | UTC date |
| `D_exam` | days until exam = `max(0, (exam_date − now).days)` | days |

### 1.2 Time and timezone rule (closes Master Plan G11/U2)

- **All timestamps are stored and computed in UTC.**
- **All "elapsed days" use UTC.** A day boundary is 00:00 UTC.
- **Per-student local timezone** (`students.timezone`, IANA string, default `Asia/Kolkata`) is used **only for display and for choosing when nightly jobs *present* results**, never for the math. This guarantees the scoring math is identical regardless of where a worker runs.
- Nightly batch jobs run at **18:30 UTC (00:00 IST)** by default; configurable per deployment.

### 1.3 Normalization helpers (the most-reused functions)

All raw inputs are mapped to `[0, 1]` before weighting. Three canonical helpers:

**Clamp**

```
clamp(x, lo, hi) = min(hi, max(lo, x))
```

**Linear min-max normalization** (maps a raw value in `[min, max]` to `[0,1]`)

```
norm(x, min, max) = clamp((x − min) / (max − min), 0, 1)      # if max == min → return 0
```

**Logistic squash** (used when we need a soft 0–1 curve around a midpoint `x0` with steepness `k`)

```
logistic(x, x0, k) = 1 / (1 + e^(−k·(x − x0)))
```

**Rounding & storage:** scores are computed in full `float64`, then **stored rounded to 2 decimals** and **displayed rounded to the nearest integer**. Never round mid-computation.

### 1.4 Confidence-weighting for sparse data (the "how new is this student?" rule)

Every score that aggregates evidence multiplies its raw value by a **data-confidence factor** `c ∈ [0,1]` and blends with a conservative prior, so a student with 2 data points does not get a wildly swingy score.

```
shrink(raw, n, k_conf, prior) = (n / (n + k_conf)) · raw + (k_conf / (n + k_conf)) · prior
```

- `n` = number of evidence events available.
- `k_conf` = "pseudo-count" controlling how fast we trust the data (per-score, given below).
- `prior` = the conservative default value for that score when no data exists.

This is a standard **Bayesian shrinkage / Laplace-smoothing** technique. It is the backbone of every cold-start and anti-gaming rule in this document.

### 1.5 Determinism, versioning, and audit (non-negotiable)

- Every scoring function is **pure**: no randomness, no wall-clock reads *inside* the function — `now` is always passed in as an argument.
- Every formula carries a **version tag** (e.g., `mastery_v1`). The version that produced a stored score is persisted alongside it (`student_concept_progress.mastery_version`). Changing a constant = a new version + a backfill migration.
- Every score write emits a domain event and an audit record: `{score_name, version, inputs_hash, old_value, new_value, reason, computed_at}`. This satisfies blueprint Part 3 §26 Rule 4 ("every AI/scoring decision must be explainable") and Part 6 §25 (audit logging).

### 1.6 Global constants table (single place to tune)

All tunable constants live in one config object, `ScoringConfig`, versioned with the engine. Defaults below are calibrated in this document.

| Constant | Default | Used by | Meaning |
|---|---|---|---|
| `MASTERY_W_MCQ` | 0.40 | Mastery | weight of MCQ evidence |
| `MASTERY_W_MAINS` | 0.30 | Mastery | weight of Mains evidence |
| `MASTERY_W_REVISION` | 0.20 | Mastery | weight of revision-recall evidence |
| `MASTERY_W_STUDY` | 0.10 | Mastery | weight of study-activity evidence |
| `MASTERY_PRIOR` | 0.0 | Mastery | mastery prior (start unknown = 0) |
| `MASTERY_K_CONF` | 8 | Mastery | events needed before trusting mastery |
| `RET_S_BASE_INTERCEPT` | 2.0 | Retention | base stability floor (days) |
| `RET_S_BASE_SLOPE` | 0.18 | Retention | stability gained per mastery point |
| `RET_REVISION_EF` | 1.6 | Retention | stability multiplier per successful revision |
| `RET_FAIL_FACTOR` | 0.6 | Retention | stability multiplier on a failed revision |
| `IMP_W_PYQ_FREQ` | 0.40 | Importance | weight: historical PYQ frequency |
| `IMP_W_TREND` | 0.25 | Importance | weight: recent-years trend |
| `IMP_W_EXAM_REL` | 0.25 | Importance | weight: structural exam relevance |
| `IMP_W_FACULTY` | 0.10 | Importance | weight: faculty/expert override |
| `IMP_TREND_WINDOW` | 5 | Importance | recent-years window for trend |
| `IMP_HALFLIFE_YEARS` | 6 | Importance | recency half-life for PYQ weighting |
| `WEAK_W_MASTERY` | 0.55 | Weakness | weight of (100−mastery) |
| `WEAK_W_RETENTION` | 0.30 | Weakness | weight of (100−retention) |
| `WEAK_W_ERROR` | 0.15 | Weakness | weight of recent error rate |
| `WEAK_OVERCONF_BONUS` | 10 | Weakness | added when overconfident |
| `READINESS_W_KNOWLEDGE` | 0.30 | Readiness | weight: knowledge sub-score |
| `READINESS_W_RETENTION` | 0.25 | Readiness | weight: retention sub-score |
| `READINESS_W_MCQ` | 0.20 | Readiness | weight: MCQ accuracy sub-score |
| `READINESS_W_WRITING` | 0.15 | Readiness | weight: Mains/writing sub-score |
| `READINESS_W_CA` | 0.10 | Readiness | weight: current-affairs sub-score |
| `READINESS_COVERAGE_FLOOR` | 0.0 | Readiness | min syllabus coverage to avoid penalty |
| `REVHEALTH_HALFLIFE_DAYS` | 30 | Revision Health | recency half-life for revision compliance |

---

## 2. Score 1 — Mastery Score

**Anchored to blueprint Part 2 §12** (the only score with explicit weights: 40% MCQ / 30% Mains / 20% Revision / 10% Study Activity). This spec makes those weights deterministic and implementable.

### 2.1 Business Purpose
Quantifies **how well a student actually understands a single syllabus concept**, on 0–100, using objective performance evidence (not self-belief).

### 2.2 Why it exists
Mastery is the backbone of the Learning Graph. The Mentor uses it to decide what to study; Weakness, Readiness, and the predictions all read it. Without an objective mastery number, the platform would be guessing what a student knows.

### 2.3 Inputs
Per `(student_id, concept_id)`:

| Input | Source | Description |
|---|---|---|
| `mcq_component` | assessment module | normalized MCQ performance on this concept |
| `mains_component` | assessment module | normalized Mains/written performance on this concept |
| `revision_component` | revision module | normalized success of revision recalls |
| `study_component` | learning-graph study events | normalized study engagement (capped, anti-gameable) |
| `n_mcq, n_mains, n_rev, n_study` | counts of each evidence type | drive confidence-weighting |

Each component is itself a normalized `[0,1]` value, defined next.

#### 2.3.1 Component definitions (all map to [0,1])

**MCQ component** — accuracy adjusted for difficulty and recency:

```
For each MCQ attempt i on this concept:
   correct_i ∈ {0,1}
   difficulty_i ∈ {easy=0.7, medium=1.0, hard=1.3}   # difficulty multiplier
   age_days_i  = days since attempt
   recency_i   = 0.5 ^ (age_days_i / 45)              # 45-day half-life

weighted_correct = Σ_i (correct_i · difficulty_i · recency_i)
weighted_total   = Σ_i (difficulty_i · recency_i)
mcq_raw = weighted_correct / weighted_total           # in [0, ~1.3] → clamp
mcq_component = clamp(mcq_raw, 0, 1)
n_mcq = count of attempts
```

**Mains component** — normalized average of AI/faculty answer scores (each answer scored 0–10 → /10), recency-weighted identically (`0.5^(age/45)`). If no Mains attempts, `n_mains = 0`.

**Revision component** — fraction of revision recalls on this concept graded "recalled" (see Retention §3 for the recall grade), recency-weighted (`0.5^(age/45)`).

**Study component (anti-gameable by design):** study activity gives only *diminishing, capped* credit, because attending/reading is weak evidence of understanding.

```
study_minutes = Σ engaged minutes on this concept (engaged = active, see §2.11)
study_component = 1 − e^(−study_minutes / 120)        # 120 min → 0.63; saturates toward 1
n_study = count of distinct study sessions
```

### 2.4 Input Weightages
Fixed by the founder blueprint and exposed as config (`MASTERY_W_*`):

| Component | Weight |
|---|---|
| MCQ | **0.40** |
| Mains | **0.30** |
| Revision | **0.20** |
| Study activity | **0.10** |

**Weight redistribution rule (critical):** Mains data is absent for most V1 students (Mains is a later phase). If a component has **no data** (`n = 0`), its weight is **redistributed proportionally to the components that *do* have data**, so the score is not dragged to zero by a structurally-missing channel.

```
active = set of components with n > 0
For each active component j:  w'_j = w_j / Σ_{k in active} w_k
```

### 2.5 Formula

```
# 1. Component values c_j and counts n_j as defined in §2.3.1
# 2. Redistribute weights over components with data (§2.4)
# 3. Evidence-weighted blend:
raw_mastery_unit = Σ_{j in active} w'_j · c_j               # in [0,1]

# 4. Confidence-shrink toward prior (cold-start safety, §1.4):
n_total = n_mcq + n_mains + n_rev + n_study
mastery_unit = shrink(raw_mastery_unit, n_total, MASTERY_K_CONF=8, prior=MASTERY_PRIOR=0.0)

# 5. Scale to 0–100:
mastery = round(100 · mastery_unit, 2)
```

### 2.6 Output Range
`0 – 100` (float, 2 decimals stored).

### 2.7 Interpretation (from Part 2 §12)

| Band | Label | Meaning for the student |
|---|---|---|
| 0–40 | Weak | Not yet understood; needs first/again study. |
| 40–70 | Moderate | Partial understanding; needs practice + revision. |
| 70–90 | Strong | Solid; maintain via spaced revision. |
| 90–100 | Expert | Exam-ready; light touch only. |

### 2.8 Examples

**Example A — strong MCQ, no Mains yet (typical V1 student)**
- MCQ: 18 attempts, recency/difficulty-weighted accuracy `mcq_component = 0.82`, `n_mcq=18`.
- Revision: `revision_component = 0.70`, `n_rev=4`.
- Study: 200 min → `1−e^(−200/120) = 0.81`, `n_study=5`.
- Mains: none → weight redistributed.
- Active weights renormalized over {MCQ .40, Rev .20, Study .10} = sum .70 → MCQ .571, Rev .286, Study .143.
- `raw = .571·.82 + .286·.70 + .143·.81 = .469 + .200 + .116 = 0.785`.
- `n_total = 27`; `shrink = (27/35)·.785 + (8/35)·0 = .771·.785 = 0.605`.
- **Mastery = 60.5 → "Moderate."** (Note how shrinkage keeps a 27-event student from looking "Strong" prematurely.)

**Example B — brand-new student, 2 MCQs only**
- `mcq_component=1.0` (got both right), `n_mcq=2`, nothing else.
- Active = MCQ only → `raw = 1.0`.
- `shrink = (2/10)·1.0 + (8/10)·0 = 0.20`.
- **Mastery = 20 → "Weak."** Correct: two lucky questions must not mint "Expert."

**Example C — mature concept, all channels**
- MCQ .88 (n=40), Mains .72 (n=6), Rev .80 (n=10), Study .9 (n=12).
- `raw = .40·.88 + .30·.72 + .20·.80 + .10·.9 = .352+.216+.160+.090 = 0.818`.
- `n_total=68`; `shrink=(68/76)·.818 = .895·.818 = 0.732`.
- **Mastery = 73.2 → "Strong."**

### 2.9 Update Frequency
- **Event-driven (real-time)** on: `AssessmentCompleted` (MCQ/Mains), `RevisionCompleted`, `StudySessionLogged`.
- **Nightly recompute** to apply recency decay (the `0.5^(age/45)` terms change daily even with no new events). Nightly job recomputes mastery for every active `(student, concept)` touched in the last 90 days.

### 2.10 Edge Cases

| Case | Handling |
|---|---|
| No data at all | `mastery = 0`, band "Weak", flagged `unrated=true` so Mentor treats as "never studied," not "failed." |
| Only study activity (no tests) | Capped: with study-only, max `mastery_unit ≈ 0.10·1.0` then shrunk → mastery stays low (≤ ~10). Studying without testing cannot exceed "Weak." |
| All-correct tiny sample | Shrinkage prevents inflation (Example B). |
| Stale concept (no events 90+ days) | Mastery is *not* decayed (mastery = understanding, which persists); **Retention** is the score that decays. Keep them separate. |
| Difficulty missing on a question | Default `difficulty=1.0` (medium). |
| Negative-marking penalty | Handled in the MCQ accuracy upstream (wrong answer = `correct=0`); mastery never goes negative. |

### 2.11 Anti-Gaming Mechanisms

1. **Study is capped and saturating** (`1−e^(−min/120)`, weight only 0.10): a student cannot grind "time on page" to high mastery. Understanding must be *demonstrated* via questions.
2. **"Engaged minutes" only:** study time counts only with periodic activity pings (scroll/interaction within a 2-minute window); idle tabs accrue nothing.
3. **Difficulty weighting:** farming easy questions yields less than hard ones (easy multiplier 0.7 vs hard 1.3).
4. **Recency decay:** old wins fade (`0.5^(age/45)`), so you cannot bank a one-time burst.
5. **Confidence shrinkage:** small samples are pulled toward 0; you must accumulate genuine evidence.
6. **Repeated-item dampening:** the *same* MCQ answered repeatedly counts once per 30-day window (dedupe by `question_id`), preventing answer-memorization farming.

---

## 3. Score 2 — Retention Score

**Anchored to Part 2 §14** (Ebbinghaus forgetting curve; reference points Day0=100, Day7=72, Day15=55, Day30=35; "revisions increase retention"). This spec uses a **stability-modulated exponential decay** — the production-standard model (FSRS/SuperMemo family) — because, unlike a static curve, it *responds to mastery and to each revision*, which the Revision Engine requires.

### 3.1 Business Purpose
Estimates **how much of a concept the student still remembers right now**, 0–100, decaying with time and restored by revision.

### 3.2 Why it exists
"Most important metric" (Part 2 §14). UPSC is a long, memory-intensive marathon; knowing *what is being forgotten* is the entire point of the Revision Engine. Retention is the input that turns a static syllabus into a living, prioritized revision queue.

### 3.3 Inputs
Per `(student_id, concept_id)`:

| Input | Source | Description |
|---|---|---|
| `m` | Mastery score | higher mastery ⇒ memory starts more stable |
| `last_event_at` | latest study OR revision timestamp | start of the current decay interval |
| `n_success` | count of *successful* revisions on this concept | each one increases stability |
| `n_fail` | count of *failed* revisions | each one decreases stability |
| `recall_grade` (on revision) | revision module | {forgot=0, hard=1, good=2, easy=3} |
| `now` | evaluation instant (passed in) | |

### 3.4 Input Weightages
Retention is not a weighted sum; it is a **decay function** whose *stability* `S` is built from weighted drivers:

| Stability driver | Effect |
|---|---|
| Mastery | sets base stability: `S_base = 2.0 + 0.18·m` days |
| Each successful revision | multiplies stability by `EF = 1.6` (spacing effect) |
| Each failed revision | multiplies stability by `0.6` (memory was weaker than thought) |
| Recall grade on last revision | fine-tunes EF: forgot→reset, hard→1.2, good→1.6, easy→2.0 |

### 3.5 Formula

```
# Step 1 — base stability from mastery (days):
S_base = RET_S_BASE_INTERCEPT(2.0) + RET_S_BASE_SLOPE(0.18) · m

# Step 2 — apply revision history to grow/shrink stability:
S = S_base
for each revision in chronological order on this concept:
    if recall_grade == forgot:  S = S_base            # reset to base (true forgetting)
    elif recall_grade == hard:  S = S · 1.2
    elif recall_grade == good:  S = S · 1.6
    elif recall_grade == easy:  S = S · 2.0
S = clamp(S, 0.5, 3650)                                # 0.5 day .. 10 years

# Step 3 — exponential decay since the last study/revision event:
t = max(0, (now − last_event_at) in days)
retention_unit = e^(−t / S)                            # in (0,1]
retention = round(100 · retention_unit, 2)
```

**Calibration to the blueprint curve.** For a freshly studied concept with no revisions and moderate mastery `m≈70`, `S_base≈14.6`, giving R(7)≈62, R(30)≈13 — a *faster* decay than the doc's illustrative 72/35. The doc's curve assumes an already-somewhat-stable memory; to reproduce it exactly, set initial stability via the **reference-curve calibration mode**:

```
# Reference/illustration mode (matches Part 2 §14 exactly): power-law form
retention_unit = (1 + t / 27.5) ^ (−1.41)
# yields  t=0→100, 7→72.6, 15→54.1, 30→35.3   (SSE ≈ 1.3 vs the doc points)
```

**Decision:** the **stability-exponential** is the *production* model (it reacts to revisions/mastery, which the Revision Engine needs); the **power-law** is provided as a documented, drop-in alternative and as the function used in UI "forgetting curve" illustrations. Both are in `ScoringConfig` under `retention_model ∈ {stability_exp, power_law}`; default `stability_exp`.

### 3.6 Output Range
`0 – 100`. Equals 100 only at `t=0` (just studied/revised); asymptotically approaches 0, never negative.

### 3.7 Interpretation

| Band | Meaning | Revision action |
|---|---|---|
| 85–100 | Fresh | none needed |
| 60–85 | Fading | schedule soon |
| 40–60 | At risk | revise within 1–2 days |
| 0–40 | Forgotten | urgent revision / re-study |

### 3.8 Examples

**Example A — studied once, 10 days ago, mastery 70, no revisions**
`S = 2 + 0.18·70 = 14.6`; `t=10`; `R = 100·e^(−10/14.6) = 100·e^(−0.685) = 50.4`. **Retention ≈ 50 ("At risk").**

**Example B — same concept after 3 good revisions, last revision 10 days ago**
`S = 14.6·1.6·1.6·1.6 = 14.6·4.096 = 59.8`; `t=10`; `R = 100·e^(−10/59.8)= 100·e^(−0.167)=84.6`. **Retention ≈ 85 ("Fresh").** Revisions visibly buy durability.

**Example C — failed last revision**
After a `forgot` grade, `S` resets to `S_base=14.6`, and `last_event_at` updates to the revision time, so `t` resets to 0 → Retention jumps to 100 *briefly* but with low stability, so it will fall fast again — correctly modeling "relearned but fragile."

### 3.9 Update Frequency
- **Lazy/on-read:** retention is a pure function of `now`; compute it whenever it is read (dashboard, Mentor, Revision queue). No write needed just because time passed.
- **Nightly materialization:** the nightly job *writes* the current retention into `student_concept_progress.retention_score` so analytics/queries are fast, and emits `RetentionRecomputed`.
- **Event-driven stability update:** on `RevisionCompleted`/`StudySessionLogged`, recompute `S` and set `last_event_at`.

### 3.10 Edge Cases

| Case | Handling |
|---|---|
| Never studied | retention = `null`/`0` with `unrated=true`; not counted as "forgotten." |
| `last_event_at` in the future (clock skew) | `t` clamped to 0 → retention 100. |
| Mastery = 0 but studied | `S_base = 2.0` (tiny) → decays within ~2 days, correctly. |
| Extremely high revision count | `S` capped at 3650 days (10 yr) to avoid overflow / "immortal memory." |
| Concept re-studied after long gap | new `StudySessionLogged` resets `t`; stability keeps prior successful-revision gains unless a `forgot` grade resets it. |
| Daylight/timezone | irrelevant — UTC only (§1.2). |

### 3.11 Anti-Gaming Mechanisms

1. **Retention cannot be raised by clicking "I revised."** A revision only updates stability/`t` if accompanied by a **recall check** (the student must answer a recall prompt; the grade feeds the EF). A failed check (`forgot`) *resets* stability — gaming backfires.
2. **Stability gains require *spaced*, *successful* recalls.** Cramming five revisions in one hour yields near-identical `t≈0` and does not multiply real durability because the recall prompts dedupe within a minimum inter-repetition interval (default 1 day); same-day repeats beyond the first are ignored for stability.
3. **No self-reported retention.** The number is derived from time + graded recall, never from the student asserting they remember.
4. **Mastery coupling:** you cannot have durable retention on a concept with low mastery, because `S_base` scales with mastery.

---

## 4. Score 3 — Importance Score

**Anchored to Part 2 §10** (`Importance = PYQ Frequency + Recent Trend + Exam Relevance + Faculty Weight`; examples Fundamental Rights=95, Governor Powers=78). This is a **concept-level, mostly student-independent** score (see §4.10 on per-student weighting).

### 4.1 Business Purpose
Ranks **how exam-relevant each syllabus concept is**, 0–100, primarily from previous-year-question (PYQ) evidence, so the platform spends student time where exam marks actually are.

### 4.2 Why it exists
UPSC/PSC success is ruthlessly about *high-yield* topics. Importance is what lets the Mentor and Revision Engine prioritize Fundamental Rights over an obscure footnote. It is the "exam relevance" half of every prioritization decision (the other half is the student's weakness).

### 4.3 Inputs
Per `concept_id` (within an `exam_id`):

| Input | Source | Description |
|---|---|---|
| `pyq_hits[]` | `pyq_mappings` + `pyq_questions` | each PYQ mapped to this concept, with `year`, `marks`, mapping `weight` |
| `exam_total_years` | exam metadata | number of years of PYQ data available |
| `exam_relevance` | `syllabus_nodes` × `exams` weights | structural weight of the concept's paper/area (e.g., GS2 weight) |
| `faculty_weight` | faculty override (0–100, optional) | expert adjustment |
| `now` | for recency | |

### 4.4 Input Weightages
Normalized weights (sum = 1.0), config `IMP_W_*`:

| Factor | Weight | Rationale |
|---|---|---|
| PYQ Frequency | **0.40** | historical evidence is the strongest signal |
| Recent Trend | **0.25** | the exam evolves; recent years matter more |
| Exam Relevance | **0.25** | structural weight of the area in the exam |
| Faculty Weight | **0.10** | expert correction, deliberately bounded |

### 4.5 Formula

```
# --- Factor 1: PYQ Frequency (recency-weighted count of appearances) ---
# Recent PYQs count more via an exponential recency weight (half-life 6 years):
for each hit:  rw = 0.5 ^ ((current_year − hit.year) / IMP_HALFLIFE_YEARS(6))
freq_raw = Σ_hits ( rw · hit.mapping_weight · marks_factor(hit.marks) )
   where marks_factor(marks) = clamp(marks / 15, 0.5, 2.0)   # bigger questions weigh more
# Normalize against the busiest concept in the same exam (percentile anchor):
freq_norm = norm(freq_raw, 0, P95_freq_raw_in_exam)          # P95 avoids one outlier saturating

# --- Factor 2: Recent Trend (is it rising or fading in the last 5 years?) ---
recent  = count of hits in last IMP_TREND_WINDOW(5) years
earlier = count of hits in the 5 years before that
trend_ratio = (recent + 1) / (earlier + 1)                   # +1 Laplace smoothing
trend_norm  = logistic(trend_ratio, x0=1.0, k=1.5)           # 1.0→0.5, rising→toward 1

# --- Factor 3: Exam Relevance (structural weight, already 0–100) ---
examrel_norm = exam_relevance / 100

# --- Factor 4: Faculty Weight (optional expert 0–100) ---
faculty_norm = (faculty_weight / 100) if provided else examrel_norm   # fallback = structural

# --- Combine ---
importance_unit = IMP_W_PYQ_FREQ(0.40)·freq_norm
                + IMP_W_TREND(0.25)·trend_norm
                + IMP_W_EXAM_REL(0.25)·examrel_norm
                + IMP_W_FACULTY(0.10)·faculty_norm
importance = round(100 · clamp(importance_unit, 0, 1), 2)
```

### 4.6 Output Range
`0 – 100`.

### 4.7 Interpretation

| Band | Meaning | Planner behavior |
|---|---|---|
| 80–100 | Critical / high-yield | always prioritized |
| 60–80 | Important | regularly scheduled |
| 40–60 | Moderate | covered, lower cadence |
| 0–40 | Low-yield | minimal time; revise only if weak+time permits |

### 4.8 Examples

**Example A — Fundamental Rights (target ≈ 95)**
- Appears frequently and recently; `freq_norm≈0.97`, `trend_norm≈0.85` (still rising), `examrel_norm=0.90` (GS2 heavy), faculty=95→0.95.
- `unit = .40·.97 + .25·.85 + .25·.90 + .10·.95 = .388+.213+.225+.095 = 0.921` → **Importance ≈ 92** (≈ the doc's 95).

**Example B — Governor Powers (target ≈ 78)**
- Moderate frequency, steady trend: `freq_norm≈0.72`, `trend_norm≈0.55`, `examrel_norm=0.85`, faculty none→fallback 0.85.
- `unit = .40·.72+.25·.55+.25·.85+.10·.85 = .288+.138+.213+.085 = 0.724` → **Importance ≈ 72** (close to 78; faculty can nudge up).

### 4.9 Update Frequency
- **Recomputed when PYQ data changes** (new PYQ ingested/mapped, faculty override) — event `PYQDataChanged`.
- **Annual roll** at the start of each cycle (the recency weights shift as `current_year` advances) — scheduled job.
- Otherwise **static** (it does not change with individual student behavior).

### 4.10 Edge Cases

| Case | Handling |
|---|---|
| Concept with **no PYQs** | `freq_norm=0`, `trend_norm=0.5` (neutral); importance driven by exam-relevance + faculty only → typically 30–45. Flag `pyq_backed=false`. |
| New exam, no PYQ history | importance = exam-relevance + faculty only; `pyq_backed=false`, surfaced to admins to add faculty weights. |
| Faculty sets an extreme value | faculty contribution capped at its 0.10 weight; one expert cannot override evidence wholesale. |
| Duplicate PYQ mappings | dedupe by `(question_id, concept_id)`. |
| Per-student importance (`student_concept_progress.importance_score`) | stores a **personalized copy**: `I_student = I_concept` by default, optionally blended with the student's exam/optional-subject selection (e.g., optional-subject concepts get `×1.0`, non-optional get `×0.9`). This resolves Master Plan U8: global importance is the truth; the per-student column is a denormalized, optionally-weighted copy. |

### 4.11 Anti-Gaming Mechanisms
Importance is **not student-influenced**, so students cannot game it. Integrity controls target *data poisoning*:
1. **Faculty weight is bounded** (0.10) and **audited** (who set it, when, why).
2. **PYQ mappings are reviewable** and weighted by mapping confidence; low-confidence mappings contribute less.
3. **P95 normalization** prevents a single mis-tagged high-mark question from saturating a concept to 100.

---

## 5. Score 4 — Weakness Score

**Closes Master Plan gap:** Weakness is referenced by the Revision Priority formula (Part 2 §15) but never defined in the source docs. Defined here from first principles, consistent with the blueprint's overconfidence concept (Part 2 §13).

### 5.1 Business Purpose
Quantifies **how much a concept is a liability for this student right now**, 0–100 (higher = weaker = more dangerous), combining poor understanding, poor memory, recent errors, and overconfidence.

### 5.2 Why it exists
Prioritization needs the *inverse* of strength. A high-importance concept the student already knows is not a priority; a high-importance concept they are weak on is. Weakness is the per-student "danger" signal that, multiplied by Importance, drives revision and planning. It also surfaces **overconfidence** (high confidence + low mastery), the most exam-dangerous state.

### 5.3 Inputs
Per `(student_id, concept_id)`:

| Input | Source | Description |
|---|---|---|
| `m` | Mastery | understanding |
| `R` | Retention | current memory |
| `error_rate` | recent MCQ wrong-rate on this concept | recency-weighted |
| `confidence` | Confidence score (Part 2 §13) | for overconfidence detection |

### 5.4 Input Weightages
Weights (sum = 1.0 for the base; overconfidence is an additive bonus), config `WEAK_W_*`:

| Driver | Weight |
|---|---|
| Lack of mastery `(100 − m)` | **0.55** |
| Lack of retention `(100 − R)` | **0.30** |
| Recent error rate | **0.15** |
| Overconfidence bonus | additive `+10` (capped at 100) |

### 5.5 Formula

```
lack_mastery   = (100 − m) / 100
lack_retention = (100 − R) / 100
error_norm     = clamp(error_rate, 0, 1)          # recent wrong-rate, recency-weighted

weakness_unit  = WEAK_W_MASTERY(0.55)·lack_mastery
               + WEAK_W_RETENTION(0.30)·lack_retention
               + WEAK_W_ERROR(0.15)·error_norm

# Overconfidence flag: confident but not masterful (Part 2 §13 example: m=40, conf=90)
overconfident  = (confidence − m) >= 25 AND m < 70
weakness = 100 · weakness_unit + (WEAK_OVERCONF_BONUS(10) if overconfident else 0)
weakness = round(clamp(weakness, 0, 100), 2)
```

### 5.6 Output Range
`0 – 100` (higher = weaker).

### 5.7 Interpretation

| Band | Meaning |
|---|---|
| 0–25 | Strength — safe |
| 25–50 | Minor gap |
| 50–75 | Real weakness — schedule work |
| 75–100 | Critical weakness / overconfidence — urgent |

### 5.8 Examples

**Example A — strong, fresh concept**
`m=85, R=80, error_rate=0.1, conf=80`. `lack_m=.15, lack_R=.20, err=.10`. `unit=.55·.15+.30·.20+.15·.10=.0825+.06+.015=.1575`. Not overconfident (conf−m=−5). **Weakness ≈ 15.8 ("Strength").**

**Example B — overconfident (the dangerous case)**
`m=40, R=55, error_rate=0.45, conf=90`. `lack_m=.60, lack_R=.45, err=.45`. `unit=.55·.60+.30·.45+.15·.45=.33+.135+.0675=.5325`→53.25; overconfident (90−40=50≥25, m<70) → +10 = **63.25 ("Real weakness")**, flagged `overconfident=true` so the Mentor explicitly warns the student.

### 5.9 Update Frequency
Recomputed whenever its inputs change (real-time on assessment/revision events; nightly with retention). It is fully derived — never stored independently of its inputs except as a materialized convenience column.

### 5.10 Edge Cases

| Case | Handling |
|---|---|
| Never studied (`unrated`) | weakness is **not** 100; set `weakness = null` and let Mentor treat as "new material to learn," distinct from "weak material to fix." (Avoids flooding the revision queue with never-seen concepts.) |
| No recent MCQs | `error_norm = 0` (no evidence of error); weakness rests on mastery+retention. |
| Confidence missing | overconfidence check skipped (no bonus). |
| Perfect everything | weakness floors at ~0. |

### 5.11 Anti-Gaming Mechanisms
Weakness is derived from already-anti-gamed inputs (Mastery, Retention), so it inherits their protections. Additionally:
1. **Overconfidence is penalized**, removing the incentive to self-report high confidence.
2. **Lowering weakness requires raising mastery/retention through demonstrated recall** — there is no direct lever.

---

## 6. Score 5 — Revision Health Score

**Anchored to Part 2 §16** (`Completed Revisions / Scheduled Revisions`, 0–100, example 92). This spec adds recency weighting and on-time credit so the number reflects *current* discipline, not lifetime average.

### 6.1 Business Purpose
A **student-level** (not per-concept) score, 0–100, measuring **how reliably the student completes the revisions the system schedules** — i.e., revision discipline.

### 6.2 Why it exists
The Revision Engine is worthless if students ignore it. Revision Health is the behavioral KPI that (a) tells the student whether their forgetting is under control, (b) feeds the Readiness Score, and (c) lets the Mentor intervene ("your revision health dropped to 48% this week").

### 6.3 Inputs
Per `student_id` over a rolling window:

| Input | Source | Description |
|---|---|---|
| `scheduled[]` | `revisions` (status, scheduled_date) | each scheduled revision |
| `completed[]` | `revisions` completed (completed_date) | with on-time vs late flag |
| `now` | for recency weighting | |

### 6.4 Input Weightages
Each revision contributes a **recency weight** (recent matters more) and an **on-time credit**:

| Element | Value |
|---|---|
| Recency weight | `0.5 ^ (age_days / REVHEALTH_HALFLIFE_DAYS=30)` |
| Completed on/before scheduled date | full credit `1.0` |
| Completed late (within 7 days) | partial credit `0.6` |
| Completed very late (>7 days) | `0.3` |
| Missed (still incomplete & overdue) | `0.0` |

### 6.5 Formula

```
window = last 60 days of scheduled revisions (configurable)
numerator = Σ_{r in scheduled∩window} ( recency_w(r) · credit(r) )
denominator = Σ_{r in scheduled∩window} ( recency_w(r) )
revision_health = round(100 · (numerator / denominator), 2)      # if denominator==0 → null
   where credit(r) = 1.0 | 0.6 | 0.3 | 0.0 per §6.4
         recency_w(r) = 0.5 ^ (days_since(scheduled_date) / 30)
```

### 6.6 Output Range
`0 – 100`. `null` when nothing has been scheduled yet (brand-new student) — display as "—", not 0.

### 6.7 Interpretation

| Band | Meaning | Mentor action |
|---|---|---|
| 85–100 | Excellent discipline | reinforce |
| 70–85 | Good | gentle nudge |
| 50–70 | Slipping | active reminder + lighten load |
| 0–50 | At risk | intervention: reduce backlog, re-plan |

### 6.8 Examples

**Example A — diligent student**
Last 60 days: 40 scheduled, 37 completed on time, 2 late (≤7d), 1 missed; ignoring recency for clarity ≈ `(37·1 + 2·0.6 + 1·0)/40 = 38.2/40 = 0.955` → **Revision Health ≈ 95.** With recency weighting, recent misses would lower this.

**Example B — slipping recently**
Older revisions all done (low recency weight), but in the last week 6 of 8 missed. Recency weighting pushes those recent misses to dominate → health falls to ~55 ("Slipping"), triggering Mentor intervention even though the *lifetime* ratio looks fine. This is exactly why recency weighting matters.

### 6.9 Update Frequency
- **Event-driven** on `RevisionCompleted` and on the nightly job that marks overdue revisions missed.
- **Nightly** recompute (recency weights change daily). Stored on the Preparation Twin's behavior profile.

### 6.10 Edge Cases

| Case | Handling |
|---|---|
| No revisions scheduled yet | `null` ("—"), not 0; a new student is not "unhealthy." |
| Revision scheduled today, not yet due | excluded from denominator until its due date passes. |
| Bulk completion of a backlog | late credit (0.6/0.3) prevents a single catch-up day from restoring full health. |
| Student manually marks complete without recall | only counts if recall check passed (ties to Retention §3.11); otherwise treated as not completed. |

### 6.11 Anti-Gaming Mechanisms
1. **On-time weighting:** mass-completing overdue items late yields only partial credit, so you cannot rescue the score by clicking everything once.
2. **Recall-gated completion:** a "completed" revision requires a passed recall check (shared with Retention), so you cannot inflate health by dismissing cards.
3. **Recency weighting:** you cannot coast on past diligence; the score reflects the *current* 30–60 day behavior.

---

## 7. Score 6 — Readiness Score

**Closes Master Plan gap G4/D3** (the headline dashboard KPI from Part 7 §17 — "single most important KPI" — had **no formula**). Defined here as a deterministic, syllabus-weighted composite.

### 7.1 Business Purpose
The **single top-of-dashboard number**, 0–100, answering "**how exam-ready is this student overall, right now?**" — an importance-weighted roll-up across the whole syllabus and across the dimensions that win the exam.

### 7.2 Why it exists
Students and institutes need one honest, motivating, hard-to-game number that moves only when real preparation improves. It is the product's "north-star" metric and the basis of the predicted scores.

### 7.3 Inputs
Per `student_id` (for a given `exam_id`):

| Sub-score | Built from | Range |
|---|---|---|
| `KnowledgeSub` | importance-weighted mean **Mastery** across syllabus concepts | 0–100 |
| `RetentionSub` | importance-weighted mean **Retention** across studied concepts | 0–100 |
| `MCQSub` | recent MCQ accuracy (recency-weighted, difficulty-adjusted) | 0–100 |
| `WritingSub` | recent Mains/essay average (0–10 → ×10); redistributed if absent | 0–100 |
| `CASub` | current-affairs coverage/accuracy (V2; redistributed if absent) | 0–100 |
| `coverage` | fraction of *high-importance* syllabus concepts with any data | 0–1 |

### 7.4 Input Weightages
Config `READINESS_W_*` (sum = 1.0); **missing sub-scores redistribute** (same rule as Mastery §2.4):

| Sub-score | Weight | Why |
|---|---|---|
| Knowledge (mastery) | **0.30** | understanding is the foundation |
| Retention | **0.25** | exam tests durable memory |
| MCQ accuracy | **0.20** | Prelims is MCQ |
| Writing (Mains) | **0.15** | Mains decides selection |
| Current Affairs | **0.10** | high-yield, cross-cutting |

### 7.5 Formula

```
# --- Sub-scores ---
# Importance-weighted means (a weak grasp of high-importance topics hurts more):
KnowledgeSub = Σ_c (I_c · m_c) / Σ_c I_c                     # over all syllabus concepts
RetentionSub = Σ_c (I_c · R_c) / Σ_c I_c                     # over concepts with data; unrated R treated as 0
MCQSub       = 100 · recency_difficulty_weighted_accuracy    # whole-exam recent MCQs
WritingSub   = 100 · (recent_mains_avg / 10)                 # if mains data exists
CASub        = 100 · ca_coverage_accuracy                    # V2

# --- Redistribute weights over available sub-scores ---
active = sub-scores with data;  w'_j = w_j / Σ_active w_k
base_readiness = Σ_{j in active} w'_j · Sub_j                # 0–100

# --- Coverage penalty (you cannot be "ready" having studied 10% of the syllabus) ---
coverage = (#high-importance concepts with mastery data) / (#high-importance concepts)
coverage_factor = 0.5 + 0.5 · coverage                       # 0% covered → ×0.5; 100% → ×1.0
readiness = round(clamp(base_readiness · coverage_factor, 0, 100), 2)
```

The **importance-weighting** and **coverage penalty** are what make Readiness honest: doing well on a few easy topics cannot produce a high score.

### 7.6 Output Range
`0 – 100`.

### 7.7 Interpretation

| Band | Meaning |
|---|---|
| 80–100 | Exam-ready (strong selection chance) |
| 65–80 | On track; close gaps |
| 50–65 | Developing; significant work remains |
| 0–50 | Early stage / large gaps |

### 7.8 Examples

**Example A — mid-stage UPSC aspirant (no Mains/CA yet)**
- `KnowledgeSub=62, RetentionSub=58, MCQSub=66`. Writing & CA absent → redistribute {0.30,0.25,0.20}=0.75 → weights .40/.333/.267.
- `base = .40·62 + .333·58 + .267·66 = 24.8 + 19.3 + 17.6 = 61.7`.
- Coverage: studied 70% of high-importance concepts → `coverage_factor = 0.5+0.5·0.70 = 0.85`.
- `readiness = 61.7 · 0.85 = 52.4` → **Readiness ≈ 52 ("Developing").** Note how the coverage penalty tempers an otherwise-60 score.

**Example B — full-channel, broad coverage**
- Subs: Knowledge 78, Retention 74, MCQ 80, Writing 65, CA 60. Coverage 0.95 → factor 0.975.
- `base = .30·78+.25·74+.20·80+.15·65+.10·60 = 23.4+18.5+16+9.75+6 = 73.65`.
- `readiness = 73.65·0.975 = 71.8` → **≈ 72 ("On track").** (Matches the Part 7 §4 dashboard mock of "Readiness 72%".)

### 7.9 Update Frequency
- **Nightly** (depends on retention, which decays daily).
- **Event-driven recompute** after any `AssessmentCompleted` so the dashboard reflects a just-finished test immediately.
- Stored on `preparation_twins.prediction_profile.readiness` with timestamp and version.

### 7.10 Edge Cases

| Case | Handling |
|---|---|
| Brand-new student | low coverage → strong coverage penalty → readiness near 0; display "Just getting started." |
| Only MCQ data | redistribute to MCQ-heavy; coverage still applies. |
| Syllabus with zero importance sums (misconfigured) | fall back to unweighted mean; raise data-quality alert. |
| Exam date passed | readiness still computes; Mentor switches messaging to "revision/consolidation mode." |

### 7.11 Anti-Gaming Mechanisms
1. **Importance weighting:** padding easy/low-yield topics barely moves the score.
2. **Coverage penalty:** you must engage *breadth* of high-yield syllabus to climb.
3. **Built only from anti-gamed sub-scores** (Mastery/Retention/MCQ), inheriting their protections.
4. **No self-report inputs** anywhere in the composite.

---

## 8. Score 7 — Predicted Prelims Score

**Anchored to Part 2 §21 / Part 7 §4** ("Predicted Prelims 84 ± 6"). Deterministic regression-style estimate with an explicit confidence interval. **No LLM** — this is a transparent linear model with calibrated coefficients (the blueprint's "prediction model" can later be retrained on real outcome data; until then these are expert-set priors, documented as such).

### 8.1 Business Purpose
Predicts the student's **likely Prelims (objective/MCQ) performance** as a point estimate **± interval**, expressed on the exam's marks/percentage scale, from current preparation state.

### 8.2 Why it exists
The "most addictive" forward-looking number (Part 7). It converts abstract scores into the currency students care about — an exam result — and quantifies uncertainty so it is honest, not a false promise.

### 8.3 Inputs
Per `student_id` (Prelims-relevant):

| Input | Source | Notes |
|---|---|---|
| `MCQSub` | Readiness sub-score | strongest predictor of Prelims |
| `KnowledgeSub` | mastery roll-up | |
| `RetentionSub` | retention roll-up | durable recall on exam day |
| `CASub` | current affairs | Prelims-heavy in UPSC |
| `coverage` | high-importance syllabus coverage | confidence driver |
| `n_eff` | effective number of MCQ attempts (recency-weighted) | confidence driver |
| `mock_scores[]` | full-length Prelims mock results, if any | strongest *calibration* anchor |

### 8.4 Input Weightages
Two parts: a **feature model** (point estimate) and an **uncertainty model** (interval).

Point-estimate coefficients (on 0–100 inputs → 0–100 predicted), config `PRED_PRELIMS_*`:

| Feature | Weight |
|---|---|
| MCQSub | **0.45** |
| KnowledgeSub | **0.25** |
| RetentionSub | **0.20** |
| CASub | **0.10** |

**Mock override/blend:** if ≥1 full-length Prelims mock exists, blend model output with recency-weighted mock mean by `mock_trust = n_eff_mocks/(n_eff_mocks+2)`:
`point = (1−mock_trust)·model + mock_trust·mock_mean`.

### 8.5 Formula

```
# --- Point estimate (0–100 scale) ---
model = PW_MCQ(0.45)·MCQSub + PW_KNOW(0.25)·KnowledgeSub
      + PW_RET(0.20)·RetentionSub + PW_CA(0.10)·CASub      # redistribute if a feature absent

if mocks exist:
    mock_mean  = recency_weighted_mean(mock_scores normalized to 0–100)
    mock_trust = n_eff_mocks / (n_eff_mocks + 2)
    point = (1 − mock_trust)·model + mock_trust·mock_mean
else:
    point = model

predicted_prelims = round(clamp(point, 0, 100), 1)

# --- Confidence interval (±, in points) ---
# Uncertainty shrinks with more data, more coverage, and more mocks:
base_sigma = 12                                            # points, expert prior
data_factor      = 1 − 0.4·clamp(n_eff / 200, 0, 1)        # lots of MCQs → tighter
coverage_factor  = 1 − 0.3·coverage                        # broad coverage → tighter
mock_factor      = 1 − 0.3·mock_trust                      # mocks → tighter
sigma = base_sigma · data_factor · coverage_factor · mock_factor
sigma = clamp(sigma, 3, 15)
interval = round(1.0·sigma, 0)                             # report ±1σ (≈68% band)
# Result presented as:  predicted_prelims ± interval
```

(Reporting ±1σ matches the doc's "84 ± 6" magnitude. A ±1.28σ 80% band is available as a config display option.)

### 8.6 Output Range
Point: `0 – 100` (mapped to the exam's marks via `exam.prelims_max` for display, e.g., UPSC GS Paper-I = 200 marks → multiply by 2). Interval: `±3 … ±15` points.

### 8.7 Interpretation
The point is the **expected** Prelims percentage on current trajectory; the interval is the honest uncertainty. The Mentor frames it as: "On your current preparation, you'd likely score **84 ± 6**. Closing your weak high-importance topics would raise the lower bound."

### 8.8 Examples

**Example A — strong, with mocks**
`MCQSub=82, KnowledgeSub=76, RetentionSub=72, CASub=68`. `model = .45·82+.25·76+.20·72+.10·68 = 36.9+19+14.4+6.8 = 77.1`. Two mocks averaging 86, `n_eff_mocks=2`→`mock_trust=0.5`. `point=0.5·77.1+0.5·86=81.6`. Coverage 0.9, `n_eff=180`: `data_factor=1−0.4·0.9=0.64`, `coverage_factor=1−0.3·0.9=0.73`, `mock_factor=1−0.3·0.5=0.85`. `sigma=12·0.64·0.73·0.85=4.76`→`±5`. **Predicted Prelims ≈ 82 ± 5.**

**Example B — early student, no mocks**
`MCQSub=55, KnowledgeSub=50, RetentionSub=48, CASub=40`. `model=.45·55+.25·50+.20·48+.10·40=24.75+12.5+9.6+4=50.85`. No mocks → `point≈51`. Coverage 0.4, `n_eff=40`: `data_factor=1−0.4·0.2=0.92`, `coverage_factor=1−0.3·0.4=0.88`, `mock_factor=1`. `sigma=12·0.92·0.88=9.7`→`±10`. **Predicted Prelims ≈ 51 ± 10** (wide, honestly uncertain).

### 8.9 Update Frequency
Nightly, and after each mock or significant MCQ batch (`AssessmentCompleted` of type prelims-mock). Stored on `prediction_profile`.

### 8.10 Edge Cases

| Case | Handling |
|---|---|
| No MCQ data | prediction suppressed; show "Take a few MCQs/a mock to unlock your prediction." Never fabricate. |
| One outlier mock | recency-weighted mean + `mock_trust` cap prevents a single 99 or 20 from dominating. |
| Coverage very low | `sigma` widens and a `low_confidence=true` flag is shown. |
| Exam scale differs (State PSC) | map 0–100 via `exam.prelims_max`; coefficients unchanged. |

### 8.11 Anti-Gaming Mechanisms
1. **Built on anti-gamed sub-scores**; no self-report.
2. **Mocks (hard to fake) dominate when available**, anchoring to realistic full-length performance.
3. **Coverage- and data-driven uncertainty** prevents a thin-but-lucky profile from showing a confident high prediction.
4. **Repeated-question dedupe** (from Mastery/MCQ) prevents inflating `MCQSub` by re-answering known items.

---

## 9. Score 8 — Predicted Mains Score

**Anchored to Part 2 §21.** Same regression-with-interval philosophy as Prelims, but **writing-weighted** and explicitly **lower-confidence** (Mains is subjective; AI Mains evaluation is a later, eval-gated phase per the Master Plan, so this prediction is conservative until real Mains data accumulates).

### 9.1 Business Purpose
Predicts likely **Mains (descriptive/written) performance**, point ± interval, on the exam's Mains scale, from writing performance plus knowledge/retention.

### 9.2 Why it exists
Mains decides final selection in UPSC/PSC. A forward estimate (with honest, wider uncertainty) guides how much answer-writing practice a student needs versus objective prep.

### 9.3 Inputs
Per `student_id` (Mains-relevant):

| Input | Source | Notes |
|---|---|---|
| `WritingSub` | Mains/essay evaluation roll-up (0–100) | strongest predictor |
| `KnowledgeSub` | mastery roll-up | content depth |
| `RetentionSub` | retention roll-up | durable recall for the exam |
| `structure_quality` | answer-structure metric from Mains analytics (Part 2 §25) | intro/body/conclusion, flow |
| `coverage` | GS/optional coverage | confidence driver |
| `n_mains_eff` | recency-weighted count of evaluated answers | confidence driver |

### 9.4 Input Weightages
Config `PRED_MAINS_*`:

| Feature | Weight |
|---|---|
| WritingSub | **0.45** |
| KnowledgeSub | **0.30** |
| RetentionSub | **0.15** |
| Structure quality | **0.10** |

### 9.5 Formula

```
model = MW_WRITING(0.45)·WritingSub + MW_KNOW(0.30)·KnowledgeSub
      + MW_RET(0.15)·RetentionSub + MW_STRUCT(0.10)·structure_quality   # redistribute if absent
predicted_mains = round(clamp(model, 0, 100), 1)

# Wider base uncertainty than Prelims (Mains scoring is subjective):
base_sigma = 16
data_factor     = 1 − 0.4·clamp(n_mains_eff / 60, 0, 1)
coverage_factor = 1 − 0.3·coverage
sigma = clamp(base_sigma · data_factor · coverage_factor, 5, 20)
interval = round(sigma, 0)                                  # ±1σ
# Result:  predicted_mains ± interval, with low_confidence=true until n_mains_eff >= 10
```

### 9.6 Output Range
Point `0 – 100` (mapped to `exam.mains_max` for display). Interval `±5 … ±20`.

### 9.7 Interpretation
Expected Mains performance on current writing trajectory, with deliberately wider bands. Until ≥10 evaluated answers exist, it is shown as a **provisional** estimate with `low_confidence=true`.

### 9.8 Examples

**Example A — practiced writer**
`WritingSub=68, KnowledgeSub=74, RetentionSub=70, structure=72`. `model=.45·68+.30·74+.15·70+.10·72=30.6+22.2+10.5+7.2=70.5`. Coverage 0.85, `n_mains_eff=30`: `data_factor=1−0.4·0.5=0.80`, `coverage_factor=1−0.3·0.85=0.745`. `sigma=16·0.80·0.745=9.5`→`±10`. **Predicted Mains ≈ 70 ± 10.**

**Example B — strong content, little writing practice**
`WritingSub` absent (no evaluated answers), `KnowledgeSub=78, RetentionSub=72, structure` absent. Redistribute to {Know .30, Ret .15}=0.45 → .667/.333. `model=.667·78+.333·72=52+24=76` → but `low_confidence=true`, `n_mains_eff=0` → `sigma` near max (`±20`), shown provisional. **≈ 76 ± 20 (provisional)** — the platform honestly says "we can't yet predict your Mains; write answers to unlock this."

### 9.9 Update Frequency
Nightly + after each `AnswerEvaluated` (Mains). Stored on `prediction_profile`.

### 9.10 Edge Cases

| Case | Handling |
|---|---|
| No evaluated Mains answers | prediction is provisional/suppressed (per policy flag); never present a confident Mains number with zero writing data. |
| AI-evaluation reliability low (eval gate not passed) | predicted Mains hidden until the Mains-evaluation eval gate (Master Plan D5) passes. |
| Optional subject vs GS | computed separately per paper if `exam` defines papers; aggregated by paper weights. |

### 9.11 Anti-Gaming Mechanisms
1. **Dominated by evaluated-answer quality**, which goes through AI + optional faculty review (hard to fake).
2. **Faculty overrides of Mains scores** (human-in-the-loop, Part 5 §19) feed `WritingSub`, correcting AI drift.
3. **Wide, data-driven uncertainty** prevents premature confident predictions.

---

## 10. How the scores interact with the four moat systems

This section is the integration contract. It ties every score to the Learning Graph, Preparation Twin, Revision Engine, and Mentor Agent, and defines the one remaining engine formula — **Revision Priority** — that consumes these scores.

### 10.1 Data ownership map

| Score | Stored where | Granularity |
|---|---|---|
| Mastery, Retention, Importance, Confidence, Weakness | `student_concept_progress` | per (student, concept) |
| Revision Health | `preparation_twins.behavior_profile` | per student |
| Readiness, Predicted Prelims, Predicted Mains | `preparation_twins.prediction_profile` | per student |
| Importance (global) | concept-level cache on `syllabus_nodes`/importance table | per (exam, concept) |

### 10.2 Interaction with the **Learning Graph** (source of truth)

The Learning Graph **is** the per-concept score store (`student_concept_progress`). It owns Mastery, Retention, Importance, Confidence, and (derived) Weakness.

- **Writes:** the Learning Graph Service is the *only* writer of these columns. Assessment/Revision/Study events flow in as domain events (`AssessmentCompleted`, `RevisionCompleted`, `StudySessionLogged`); the service recomputes Mastery (real-time) and stability/Retention, then persists with version + audit (§1.5).
- **Reads:** everything else (Twin, Revision, Mentor, Analytics, predictions) **reads** the graph; none of them write these columns. This enforces blueprint Rule 5 ("Learning Graph is source of truth").
- **Determinism guarantee:** because Retention is a pure function of `(m, last_event_at, revision_history, now)`, the graph can be *recomputed from the event log at any time* — critical for backfills when a formula version changes.

### 10.3 Interaction with the **Preparation Twin** (intelligence layer)

The Twin is a **derived, event-rebuilt projection** of the graph + history (blueprint: "Twin updates through events"). It does **not** invent numbers; it aggregates them.

- **Knowledge Profile** ← importance-weighted Mastery/Retention distributions → strongest/weakest subjects, mastery histogram.
- **Assessment Profile** ← MCQ accuracy, negative-marking risk (from guessing rate), Mains quality.
- **Behavior Profile** ← Revision Health, study consistency/streak, preferred study time.
- **Prediction Profile** ← Readiness, Predicted Prelims, Predicted Mains.
- **Rebuild trigger:** on `LearningGraphUpdated`, `RetentionRecomputed`, `RevisionCompleted`, `AssessmentCompleted`, the Twin-builder recomputes the affected profile. Rebuild is **idempotent** (same events → same Twin).

### 10.4 Interaction with the **Revision Engine** — and the Revision Priority formula

The Revision Engine consumes **Importance + Retention + Weakness + Exam Proximity** to produce the daily revision queue, then its outcomes feed back into Retention and Revision Health. This is the platform's core feedback loop.

**Revision Priority (anchored to Part 2 §15: `Importance × Retention Gap × Exam Proximity × Weakness`), made deterministic:**

```
# All factors normalized to [0,1], multiplied (a zero in any factor ⇒ not urgent):
imp_f      = I / 100                                        # importance
retgap_f   = (100 − R) / 100                                # retention gap (how much forgotten)
weak_f     = (W / 100) if W is not null else 0.5            # weakness (neutral if unrated)
prox_f     = exam_proximity(D_exam)                         # see below, in [0,1]

priority_raw = imp_f · retgap_f · weak_f · prox_f           # in [0,1]
priority = round(100 · priority_raw, 2)

# Exam proximity: urgency rises as the exam approaches (but never zero — long-term retention matters):
exam_proximity(D) = clamp(0.3 + 0.7 · (1 − D / 365), 0.3, 1.0)   # D≥365→0.3 ; D=0→1.0
```

- **Scheduling:** nightly, the engine ranks all studied concepts by `priority`, takes the **Top-N** (default 20, capped by the student's daily hours), and writes `revisions` rows (`scheduled_date = today`). Spacing respects a **minimum inter-repetition interval** (default: do not reschedule a concept revised successfully < `0.5·S` days ago).
- **Feedback:** completing a revision with a recall grade updates stability `S` (Retention §3.5) and Revision Health (§6), which changes tomorrow's priorities — the loop closes.
- **Worked example:** Fundamental Rights, `I=92, R=50` (gap .50), `W=40` (.40), exam in 120 days → `prox = 0.3+0.7·(1−120/365)=0.3+0.7·0.671=0.77`. `priority = .92·.50·.40·.77·100 = 14.2`. A low-importance fresh topic (`I=30,R=90,W=20`, same date): `.30·.10·.20·.77·100=0.46` → ranked far below. Correct behavior.

### 10.5 Interaction with the **Mentor Agent** (explainer/orchestrator)

The Mentor is the only one of the four that involves an LLM — but **it reads scores; it never computes them** (blueprint: "AI assists decisions; AI never becomes the source of truth"; "Learning Graph service never depends on AI").

- **Inputs (via tools, not DB):** `GetLearningGraphTool` (Mastery/Retention/Weakness), `GetRevisionBacklogTool` (today's `revisions` + priorities), `GetPYQInsightsTool` (Importance), Twin profiles (Readiness, predictions).
- **What the Mentor does:** assembles the daily/weekly/monthly plan by selecting from the *already-prioritized* revision queue + high-importance/low-mastery study targets + assessment suggestions; the LLM's job is **sequencing, phrasing, and explanation**, not scoring.
- **Explainability (Rule 4):** every task the Mentor emits carries the scores that justified it, e.g.:
  > "Revise **Fundamental Rights** — Importance 92, Retention dropped to 50%, exam in 120 days (priority 14.2)."
  These numbers come verbatim from this engine; the Mentor only renders them.
- **Determinism boundary:** if the LLM is unavailable, a **deterministic fallback planner** still produces a valid plan from the scores (Top-N revisions + top weak high-importance concepts), so the core loop never depends on AI availability.

### 10.6 End-to-end loop (one diagram)

```
Study / MCQ / Mains / Revision events
        │ (domain events)
        ▼
Learning Graph Service ──writes──► student_concept_progress
   Mastery (real-time)             (Mastery, Retention, Importance,
   Retention stability (S)          Confidence, Weakness)
        │ events                          │ read
        ▼                                 ▼
Preparation Twin (rebuilt)        Revision Engine (nightly)
   Knowledge/Behavior/                Revision Priority = I·gap·W·proximity
   Assessment/Prediction                → Top-N revisions
   (Readiness, Predictions,                 │ outcomes (recall grade)
    Revision Health)                         ▼
        │ read (tools)               updates S + Revision Health  ──┐
        ▼                                                            │
Mentor Agent (LLM: sequence + explain)  ◄────────────reads scores───┘
   Daily/Weekly/Monthly plan, every task justified by the numbers above
```

---

## 11. Implementation Checklist (so an engineer can build without further questions)

1. **Build `ScoringConfig`** (all constants from §1.6) as a versioned, injectable object.
2. **Implement helpers** (§1.3): `clamp`, `norm`, `logistic`, `shrink`, recency-weight `0.5^(age/H)`.
3. **Implement each score as a pure function** taking explicit inputs + `now`, returning `(value, version, inputs_hash, explanation_fields)`. Order: Importance → Mastery → Retention → Weakness → Revision Health → Readiness → Predictions.
4. **Implement Revision Priority** (§10.4) and the nightly scheduler (Top-N, min interval, daily-hours cap).
5. **Wire events** (write path in §10.2; Twin rebuild in §10.3): real-time on assessment/revision/study; nightly recompute for time-decayed scores.
6. **Persist** scores + version + audit (§1.5); make every score recomputable from the event log.
7. **Expose explanation fields** for the Mentor (§10.5) — never let the Mentor recompute.
8. **Unit tests** (per blueprint testing rules): each score gets boundary tests (0, 100, empty data), the worked examples in §§2–9 as golden tests, monotonicity tests (e.g., more correct MCQs ⇒ mastery non-decreasing), and anti-gaming tests (study-only cannot exceed cap; repeated same question deduped; late bulk revision yields partial health). Retention gets a calibration test against the §3.5 reference curve.
9. **Feature-flag** Predicted Mains behind the Mains-evaluation eval gate (Master Plan D5).

---

## Appendix A — Master constants & ranges (quick reference)

| Score | Range | Update | Storage |
|---|---|---|---|
| Mastery | 0–100 | event + nightly | `student_concept_progress.mastery_score` |
| Retention | 0–100 | on-read + nightly materialize | `student_concept_progress.retention_score` |
| Importance | 0–100 | on PYQ change + annual | concept cache + `student_concept_progress.importance_score` |
| Weakness | 0–100 (high=weak) | derived (event/nightly) | `student_concept_progress.weakness_score` |
| Revision Health | 0–100 (or null) | event + nightly | `preparation_twins.behavior_profile` |
| Readiness | 0–100 | event + nightly | `preparation_twins.prediction_profile` |
| Predicted Prelims | 0–100 ± (3–15) | nightly + mock/MCQ events | `preparation_twins.prediction_profile` |
| Predicted Mains | 0–100 ± (5–20) | nightly + AnswerEvaluated | `preparation_twins.prediction_profile` |
| Revision Priority | 0–100 | nightly | `revisions` (transient) |

## Appendix B — Decisions this spec closes (from the Master Plan)

| Master Plan item | Closed by |
|---|---|
| D2 — precise formulas for Importance/Retention/Confidence/Revision Priority | §3, §4, §5, §10.4 (Confidence detailed within Weakness/inputs) |
| D3 / G4 — Readiness Score definition | §7 |
| Weakness Score undefined | §5 (defined from first principles) |
| U1 — formulas "sum of factors without weights/normalization" | §1.3 normalization + per-score weights |
| U8 — global vs per-student importance | §4.10 |
| U2/G11 — schedule & timezone for nightly jobs | §1.2 |
| Predicted Prelims/Mains method (G6) | §8, §9 (transparent linear model + CI; retrainable later) |

## Appendix C — Source anchors

| Score | Source intent |
|---|---|
| Mastery | Part 2 §12 (40/30/20/10 weights, bands) |
| Retention | Part 2 §14 (Ebbinghaus; curve points) |
| Importance | Part 2 §10 (four factors; FR=95, Governor=78) |
| Revision Priority / Health | Part 2 §15–16 |
| Confidence / Overconfidence | Part 2 §13 |
| Readiness | Part 7 §17, Part 7 §4 ("72%") |
| Predicted Prelims/Mains | Part 2 §21, Part 7 §4 ("84 ± 6") |
| Determinism / no-LLM rule | Part 3 §11, Part 5 §1, Part 3 §26 Rules 4–7 |

---

*End of Scoring Engine Specification v1.0. Every formula here is deterministic and implementable as-is. When any constant changes, bump the score's version tag and run a backfill from the event log (§1.5). This document governs the scoring layer; the Mentor Agent may explain these numbers but must never compute or override them.*
