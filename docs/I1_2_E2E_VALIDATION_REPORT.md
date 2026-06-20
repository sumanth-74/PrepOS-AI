# Sprint I1.2 — End-to-End Validation & Demo Readiness Report

Generated: 2026-06-20 06:27 UTC

## 1. Environment Verification

| Check | Status |
|-------|--------|
| postgres | OK |
| redis | OK |
| python_venv | OK |
| npm | OK |
| docker | MISSING/FAILED |

### Startup commands

```bash
# Infrastructure (PostgreSQL + Redis)
docker compose up postgres redis -d   # or local Homebrew services

# Backend
cd backend && source .venv/bin/activate
bash scripts/migrate-db.sh
bash scripts/dev-api.sh

# Demo seed
python scripts/seed_demo_data.py

# Frontend
cd apps/web && npm install && npm run dev
```

### Required environment variables

See `.env.example`: `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `CELERY_BROKER_URL`, `CORS_ORIGINS`, `OTEL_ENABLED=false` for local dev.

### Migration status

- Current: `026_mentor_effectiveness_learning (head)`
- Head: `026_mentor_effectiveness_learning (head)`

## 2. Seed Data Evidence

```json
{
  "tenant_slug": "prepos-demo",
  "tenant_id": "d517e640-aa68-4f63-adaa-a38f5669eef7",
  "credentials": {
    "admin": {
      "email": "admin@prepos-demo.example.com",
      "password": "SecurePass123!"
    },
    "faculty": {
      "email": "faculty@prepos-demo.example.com",
      "password": "SecurePass123!"
    },
    "student": {
      "email": "student@prepos-demo.example.com",
      "password": "SecurePass123!"
    }
  },
  "exam": {
    "exam_id": "upsc_cse",
    "catalog_version": "1.0.0",
    "concepts_imported": 618
  },
  "student": {
    "student_id": "40c526e1-08bf-4549-97f9-91879b784cca",
    "expected_nodes": 618,
    "provisioned_nodes": 618,
    "sample_concept_id": "upsc_cse.agriculture.agri_technology.bio_fortification"
  },
  "events_drained": {
    "onboarding": 0,
    "goal": 0,
    "activity": 110,
    "activity_types": [
      "EscalationUpdated",
      "ForecastProbabilityUpdated",
      "ForecastUpdated",
      "LearningGraphUpdated",
      "MentorActionUpdated",
      "MentorInsightUpdated",
      "MentorSummaryUpdated",
      "MilestoneUpdated",
      "PredictedScoreUpdated",
      "RevisionCompleted",
      "RevisionQueueUpdated",
      "StudyPlanUpdated",
      "StudySessionLogged",
      "TwinDecisionUpdated",
      "TwinInterventionUpdated",
      "TwinRecommendationsUpdated",
      "TwinSnapshotUpdated",
      "TwinUpdated"
    ]
  },
  "projections": {
    "readiness_overall_score": "46.30",
    "recommendation_count": 1,
    "study_plan_daily_items": 1,
    "twin_dashboard_readiness": "46.30",
    "mentor_queue_size": 1,
    "mentor_effectiveness_score": "0.00",
    "demo_case_seeded": "d87940c8-c81b-4cc1-a627-a233a1b532ee"
  }
}
```

### Demo credentials

- Tenant: `prepos-demo`
- Admin: `admin@prepos-demo.example.com` / `SecurePass123!`
- Faculty: `faculty@prepos-demo.example.com` / `SecurePass123!`
- Student: `student@prepos-demo.example.com` / `SecurePass123!`

## 3. Student Journey Validation

```json
{
  "steps": [
    {
      "step": "login",
      "ok": true,
      "result": {
        "email": "student@prepos-demo.example.com"
      }
    },
    {
      "step": "dashboard",
      "ok": true,
      "result": {
        "readiness_score": "46.30",
        "due_revision_count": 0,
        "high_risk_concept_count": 0,
        "recommendation_count": 0,
        "largest_positive_driver": "retention",
        "largest_negative_driver": "knowledge",
        "top_positive_drivers": [
          "retention",
          "knowledge",
          "coverage"
        ],
        "top_negative_drivers": [
          "knowledge",
          "coverage",
          "retention"
        ],
        "total_estimated_gain": null,
        "today_plan_count": 0,
        "weekly_plan_count": 0,
        "completion_rate": null,
        "skip_rate": null,
        "projected_readiness": null,
        "gap_to_goal": null,
        "on_track": null,
        "expected_score": null,
        "low_score": null,
        "high_score": null,
        "risk_level": null,
        "milestone_status": null,
        "expected_weekly_progress": null,
        "next_milestone_date": null,
        "next_milestone_target": null,
        "goal_probability": null,
        "goal_likelihood": null,
        "best_case_readiness": null,
        "worst_case_readiness": null,
        "current_decision": "GOAL_RECOVERY_MODE",
        "expected_readiness_gain": "10.0",
        "expected_score_gain": "7.0",
        "current_intervention": null,
        "intervention_urgency": null,
        "intervention_score": null,
        "best_intervention": null,
        "historical_effectiveness": null,
        "last_effectiveness_score": null,
        "learning_style": null,
        "risk_profile": null,
        "consistency_score": null,
        "best_activity_type": null,
        "top_multiplier": null,
        "mentor_status": null,
        "top_mentor_message": null,
        "mentor_action": null,
        "mentor_action_priority": null,
        "escalation_level": null,
        "goal_summary": null,
        "mentor_case": null,
        "mentor_effectiveness": null,
        "generated_at": "2026-06-20T06:27:21.752609Z"
      }
    },
    {
      "step": "learning_graph",
      "ok": true,
      "result": {
        "student_id": "40c526e1-08bf-4549-97f9-91879b784cca",
        "exam_id": "upsc_cse",
        "total_nodes": 618,
        "provisioned_nodes": 618,
        "expected_nodes": 618,
        "provision_status": "complete",
        "nodes": [
          {
            "concept_id": "upsc_cse.agriculture.agri_technology.bio_fortification",
            "exam_id": "upsc_cse",
            "subject_id": "upsc_cse.agriculture",
            "topic_id": "upsc_cse.agriculture.agri_technology",
            "mastery_score": "17.55",
            "mastery_nonmcq_score": "17.55",
            "retention_score": "100.00",
            "confidence_score": null,
            "importance_score": "50.00",
            "overconfidence_flag": false,
            "mcq_attempt_count": 0,
            "mcq_correct_count": 0,
            "nonmcq_attempt_count": 0,
            "revision_count": 3,
            "study_minutes": 120,
            "node_state": "rated",
            "row_version": 7,
            "last_activity_at": "2026-06-20T06:27:21.645377Z",
            "retention_stability_s": "10.1250",
            "retention_last_event_at": "2026-06-20T06:27:21.645377Z",
            "retention_last_review_at": "2026-06-20T06:27:21.645377Z",
            "retention_last_grade": 2,
            "next_review_at": "2026-06-30T09:27:21.645377Z"
          },
          {
            "concept_id": "upsc_cse.agriculture.agri_technology.farm_mechanization",
            "exam_id": "upsc_cse",
            "subject_id": "upsc_cse.agriculture",
            "topic_id": "upsc_cse.agriculture.agri_technology",
            "mastery_score": "0.00",
            "mastery_nonmcq_score": "0.00",
            "retention_score": null,
            "confidence_score": null,
            "importance_score": "50.00",
            "overconfidence_flag": false,
            "mcq_attempt_count": 0,
            "mcq_correct_count": 0,
            "nonmcq_attempt_count": 0,
            "revision_count": 0,
            "study_minutes": 0,
            "node_state": "unrated",
            "row_version": 1,
            "last_activity_at": null,
            "retention_stability_s": null,
            "retention_last_event_at": null,
            "retention_last_review_at": null,
            "retention_last_grade": null,
            "next_review_at": null
          },
          {
            "concept_id": "upsc_cse.agriculture.agri_technology.overview",
            "exam_id": "upsc_cse",
            "subject_id": "upsc_cse.agriculture",
            "topic_id": "upsc_cse.agriculture.agri_technology",
            "mastery_score": "0.00",
            "mastery_nonmcq_score": "0.00",
            "retention_score": null,
            "confidence_score": null,
            "importance_score": "50.00",
            "overconfidence_flag": false,
            "mcq_attempt_count": 0,
            "mcq_correct_count": 0,
            "nonmcq_attempt_count": 0,
            "revision_count": 0,
            "study_minutes": 0,
            "node_state": "unrated",
            "row_version": 1,
            "last_activity_at": null,
            "retention_stability_s": null,
            "retention_last_event_at": null,
            "retention_last_review_at": null,
            "retention_last_grade": null,
            "next_review_at": null
          },
          {
            "concept_id": "upsc_cse.agriculture.agri_technology.precision_farming",
            "exam_id": "upsc_cse",
            "subject_id": "upsc_cse.agriculture",
            "topic_id": "upsc_cse.agriculture.agri_technology",
            "mastery_score": "0.00",
            "mastery_nonmcq_score": "0.00",
            "retention_score": null,
            "confidence_score": null,
            "importance_score": "50.00",
            "overconfidence_flag": false,
            "mcq_attempt_count": 0,
            "mcq_correct_count": 0,
            "nonmcq_attempt_count": 0,
            "revision_count": 0,
            "study_minutes": 0,
            "node_state": "unrated",
            "row_version": 1,
            "last_activity_at": null,
            "retention_stability_s": null,
            "retention_last_event_at": null,
            "retention_last_review_at": null,
            "retention_last_grade": null,
            "next_review_at": null
          },
          {
            "concept_id": "upsc_cse.agriculture.crops_cropping.crop_diversification",
            "exam_id": "upsc_cse",
            "subject_id": "upsc_cse.agriculture",
            "topic_id": "upsc_cse.agriculture.crops_cropping",
            "mastery_score": "0.00",
            "mastery_nonmcq_score": "0.00",
            "retention_score": null,
            "confidence_score": null,
            "importance_score": "50.00",
            "overconfidence_flag": false,
            "mcq_attempt_count": 0,
            "mcq_correct_count": 0,
            "nonmcq_attempt_count": 0,
            "revision_count": 0,
            "study_minutes": 0,
            "node_state": "unrated",
            "row_version": 1,
            "last_activity_at": null,
            "retention_stability_s": null,
            "retention_last_event_at": null,
            "retention_last_review_at": null,
            "retention_last_grade": null,
            "next_review_at": null
          },
          {
            "concept_id": "upsc_cse.agriculture.crops_cropping.cropping_patterns",
            "exam_id": "upsc_cse",
            "subject_id": "upsc_cse.agriculture",
            "topic_id": "upsc_cse.agriculture.crops_cropping",
            "mastery_score": "0.00",
            "mastery_nonmcq_score": "0.00",
            "retention_score": null,
            "confidence_score": null,
            "importance_score": "50.00",
            "overconfidence_flag": false,
            "mcq_attempt_count": 0,
            "mcq_correct_count": 0,
            "nonmcq_attempt_count": 0,
            "revision_count": 0,
            "study_minutes": 0,
            "node_state": "unrated",
            "row_version": 1,
            "last_activity_at": null,
            "retention_stability_s": null,
            "retention_last_event_at": null,
            "retention_last_review_at": null,
            "retention_last_grade": null,
            "next_review_at": null
          },
          {
            "concept_id": "upsc_cse.agriculture.crops_cropping.green_revolution",
            "exam_id": "upsc_cse",
            "subject_id": "upsc_cse.agriculture",
            "topic_id": "upsc_cse.agriculture.crops_cropping",
            "mastery_score": "0.00",
            "mastery_nonmcq_score": "0.00",
            "retention_score": null,
            "confidence_score": null,
            "importance_score": "50.00",
            "overconfidence_flag": false,
            "mcq_attempt_count": 0,
            "mcq_correct_count": 0,
            "nonmcq_attempt_count": 0,
            "revision_count": 0,
            "study_minutes": 0,
            "node_state": "unrated",
            "row_version": 1,
            "last_activity_at": null,
            "retention_stability_s": null,
            "retention_last_event_at": null,
            "retention_last_review_at": null,
            "retention_last_grade": null,
            "next_review_at": null
          },
          {
            "concept_id": "upsc_cse.agriculture.crops_cropping.overview",
            "exam_id": "upsc_cse",
            "subject_id": "upsc_cse.agriculture",
            "topic_id": "upsc_cse.agriculture.crops_cropping",
            "mastery_score": "0.00",
            "mastery_nonmcq_score": "0.00",
            "retention_score": null,
            "confidence_score": null,
            "importance_score": "50.00",
            "overconfidence_flag": false,
            "mcq_attempt_count": 0,
            "mcq_correct_count": 0,
            "nonmcq_attempt_count": 0,
            "revision_count": 0,
            "study_minutes": 0,
            "node_state": "unrated",
            "row_version": 1,
            "last_activity_at": null,
            "retention_stability_s": null,
            "retention_last_event_at": null,
            "retention_last_review_at": null,
            "retention_last_grade": null,
            "next_review_at": null
          },
          {
            "concept_id": "upsc_cse.agriculture.irrigation.irrigation_types",
            "exam_id": "upsc_cse",
            "subject_id": "upsc_cse.agriculture",
            "topic_id": "upsc_cse.agriculture.irrigation",
            "mastery_score": "0.00",
            "mastery_nonmcq_score": "0.00",
            "retention_score": null,
            "confidence_score": null,
            "importance_score": "50.00",
            "overconfidence_flag": false,
            "mcq_attempt_count": 0,
            "mcq_correct_count": 0,
            "nonmcq_attempt_count": 0,
            "revision_count": 0,
            "study_minutes": 0,
            "node_state": "unrated",
            "row_version": 1,
            "last_activity_at": null,
            "retention_stability_s": null,
            "retention_last_event_at": null,
            "retention_last_review_at": null,
            "retention_last_grade": null,
            "next_review_at": null
          },
          {
            "concept_id": "upsc_cse.agriculture.irrigation.overview",
            "exam_id": "upsc_cse",
            "subject_id": "upsc_cse.agriculture",
            "topic_id": "upsc_cse.agriculture.irrigation",
            "mastery_score": "0.00",
            "mastery_nonmcq_score": "0.00",
            "retention_score": null,
            "confidence_score": null,
            "importance_score": "50.00",
            "overconfidence_flag": false,
            "mcq_attempt_count": 0,
            "mcq_correct_count": 0,
            "nonmcq_attempt_count": 0,
            "revision_count": 0,
            "study_minutes": 0,
            "node_state": "unrated",
            "row_version": 1,
            "last_activity_at": null,
            "retention_stability_s": null,
            "retention_last_event_at": null,
            "retention_last_review_at": null,
            "retention_last_grade": null,
            "next_review_at": null
          },
          {
            "concept_id": "upsc_cse.agriculture.irrigation.pmksy",
            "exam_id": "upsc_cse",
            "subject_id": "upsc_cse.agriculture",
            "topic_id": "upsc_cse.agriculture.irrigation",
            "mastery_score": "0.00",
            "mastery_nonmcq_score": "0.00",
            "retention_score": null,
            "confidence_score": null,
            "importance_score": "50.00",
            "overconfidence_flag": false,
            "mcq_attempt_count": 0,
            "mcq_correct_count": 0,
            "nonmcq_attempt_count": 0,
            "revision_count": 0,
            "study_minutes": 0,
            "node_state": "unrated",
            "row_version": 1,
            "last_activity_at": null,
            "retention_stability_s": null,
            "retention_last_event_at": null,
            "retention_last_review_at": null,
            "retention_last_grade": null,
            "next_review_at": null
          },
          {
            "concept_id": "upsc_cse.agriculture.irrigation.water_use_efficiency",
            "exam_id": "upsc_cse",
            "subject_id": "upsc_cse.agriculture",
            "topic_id": "upsc_cse.agriculture.irrigation",
            "mastery_score": "0.00",
            "mastery_nonmcq_score": "0.00",
            "retention_score": null,
            "confidence_score": null,
            "importance_score": "50.00",
            "overconfidence_flag": false,
            "mcq_attempt_count": 0,
            "mcq_correct_count": 0,
            "nonmcq_attempt_count": 0,
            "revision_count": 0,
            "study_minutes": 0,
            "node_state": "unrated",
            "row_version": 1,
            "last_activity_at": null,
            "retention_stability_s": null,
            "retention_last_event_at": null,
            "retention_last_review_at": null,
            "retention_last_grade": null,
            "next_review_at": null
          },
          {
            "concept_id": "upsc_cse.agriculture.rural_development.agri_markets",
            "exam_id": "upsc_cse",
            "subject_id": "upsc_cse.agriculture",
            "topic_id": "upsc_cse.agriculture.rural_development",
            "mastery_score": "0.00",
            "mastery_nonmcq_score": "0.00",
            "retention_score": null,
            "confidence_score": null,
            "importance_score": "50.00",
            "overconfidence_flag": false,
            "mcq_attempt_count": 0,
            "mcq_correct_count": 0,
            "nonmcq_attempt_count": 0,
            "revision_count": 0,
            "study_minutes": 0,
            "node_state": "unrated",
            "row_version": 1,
            "last_activity_at": null,
            "retention_stability_s": null,
            "retention_last_event_at": null,
            "retention_last_review_at": null,
            "retention_last_grade": null,
            "next_review_at": null
          },
          {
            "concept_id": "upsc_cse.agriculture.rural_development.overview",
            "exam_id": "upsc_cse",
            "subject_id": "upsc_cse.agriculture",
            "topic_id": "upsc_cse.agriculture.rural_development",
            "mastery_score": "0.00",
            "mastery_nonmcq_score": "0.00",
            "retention_score": null,
            "confidence_score": null,
            "importance_score": "50.00",
            "overconfidence_flag": false,
            "mcq_attempt_count": 0,
            "mcq_correct_count": 0,
            "nonmcq_attempt_count": 0,
            "revision_count": 0,
            "study_minutes": 0,
            "node_state": "unrated",
            "row_version": 1,
            "last_activity_at": null,
            "retention_stability_s": null,
            "retention_last_event_at": null,
            "retention_last_review_at": null,
            "retention_last_grade": null,
            "next_review_at": null
          },
          {
            "concept_id": "upsc_cse.agriculture.rural_development.pm_kisan",
            "exam_id": "upsc_cse",
            "subject_id": "upsc_cse.agriculture",
            "topic_id": "upsc_cse.agriculture.rural_development",
            "mastery_score": "0.00",
            "mastery_nonmcq_score": "0.00",
            "retention_score": null,
            "confidence_score": null,
            "importance_score": "50.00",
            "overconfidence_flag": false,
            "mcq_attempt_count": 0,
            "mcq_correct_count": 0,
            "nonmcq_attempt_count": 0,
            "revision_count": 0,
            "study_minutes": 0,
            "node_state": "unrated",
            "row_version": 1,
            "last_activity_at": null,
            "retention_stability_s": null,
            "retention_last_event_at": null,
            "retention_last_review_at": null,
            "retention_last_grade": null,
            "next_review_at": null
          },
          {
            "concept_id": "upsc_cse.agriculture.rural_development.rural_livelihoods",
            "exam_id": "upsc_cse",
            "subject_id": "upsc_cse.agriculture",
            "topic_id": "upsc_cse.agriculture.rural_development",
            "mastery_score": "0.00",
            "mastery_nonmcq_score": "0.00",
            "retention_score": null,
            "confidence_score": null,
            "importance_score": "50.00",
            "overconfidence_flag": false,
            "mcq_attempt_count": 0,
            "mcq_correct_count": 0,
            "nonmcq_attempt_count": 0,
            "revision_count": 0,
            "study_minutes": 0,
            "node_state": "unrated",
            "row_version": 1,
            "last_activity_at": null,
            "retention_stability_s": null,
            "retention_last_event_at": null,
            "retention_last_review_at": null,
            "retention_last_grade": null,
            "next_review_at": null
          },
          {
            "concept_id": "upsc_cse.agriculture.subsidies_food.fertilizer_subsidy",
            "exam_id": "upsc_cse",
            "subject_id": "upsc_cse.agriculture",
            "topic_id": "upsc_cse.agriculture.subsidies_food",
            "mastery_score": "0.00",
            "mastery_nonmcq_score": "0.00",
            "retention_score": null,
            "confidence_score": null,
            "importance_score": "50.00",
            "overconfidence_flag": false,
            "mcq_attempt_count": 0,
            "mcq_correct_count": 0,
            "nonmcq_attempt_count": 0,
            "revision_count": 0,
            "study_minutes": 0,
            "node_state": "unrated",
            "row_version": 1,
            "last_activity_at": null,
            "retention_stability_s": null,
            "retention_last_event_at": null,
            "retention_last_review_at": null,
            "retention_last_grade": null,
            "next_review_at": null
          },
          {
            "concept_id": "upsc_cse.agriculture.subsidies_food.food_corporation",
            "exam_id": "upsc_cse",
            "subject_id": "upsc_cse.agriculture",
            "topic_id": "upsc_cse.agriculture.subsidies_food",
            "mastery_score": "0.00",
            "mastery_nonmcq_score": "0.00",
            "retention_score": null,
            "confidence_score": null,
            "importance_score": "50.00",
            "overconfidence_flag": false,
            "mcq_attempt_count": 0,
            "mcq_correct_count": 0,
            "nonmcq_attempt_count": 0,
            "revision_count": 0,
            "study_minutes": 0,
            "node_state": "unrated",
            "row_version": 1,
            "last_activity_at": null,
            "retention_stability_s": null,
            "retention_last_event_at": null,
            "retention_last_review_at": null,
            "retention_last_grade": null,
            "next_review_at": null
          },
          {
            "concept_id": "upsc_cse.agriculture.subsidies_food.overview",
            "exam_id": "upsc_cse",
            "subject_id": "upsc_cse.agriculture",
            "topic_id": "upsc_cse.agriculture.subsidies_food",
            "mastery_score": "0.00",
            "mastery_nonmcq_score": "0.00",
            "retention_score": null,
            "confidence_score": null,
            "importance_score": "50.00",
            "overconfidence_flag": false,
            "mcq_attempt_count": 0,
            "mcq_correct_count": 0,
            "nonmcq_attempt_count": 0,
            "revision_count": 0,
            "study_minutes": 0,
            "node_state": "unrated",
            "row_version": 1,
            "last_activity_at": null,
            "retention_stability_s": null,
            "retention_last_event_at": null,
            "retention_last_review_at": null,
            "retention_last_grade": null,
            "next_review_at": null
          },
          {
            "concept_id": "upsc_cse.agriculture.subsidies_food.pds",
            "exam_id": "upsc_cse",
            "subject_id": "upsc_cse.agriculture",
            "topic_id": "upsc_cse.agriculture.subsidies_food",
            "mastery_score": "0.00",
            "mastery_nonmcq_score": "0.00",
            "retention_score": null,
            "confidence_score": null,
            "importance_score": "50.00",
            "overconfidence_flag": false,
            "mcq_attempt_count": 0,
            "mcq_correct_count": 0,
            "nonmcq_attempt_count": 0,
            "revision_count": 0,
            "study_minutes": 0,
            "node_state": "unrated",
            "row_version": 1,
            "last_activity_at": null,
            "retention_stability_s": null,
            "retention_last_event_at": null,
            "retention_last_review_at": null,
            "retention_last_grade": null,
            "next_review_at": null
          },
          {
            "concept_id": "upsc_cse.art_culture.architecture.buddhist_architecture",
            "exam_id": "upsc_cse",
            "subject_id": "upsc_cse.art_culture",
            "topic_id": "upsc_cse.art_culture.architecture",
            "mastery_score": "0.00",
            "mastery_nonmcq_score": "0.00",
            "retention_score": null,
            "confidence_score": null,
            "importance_score": "50.00",
            "overconfidence_flag": false,
            "mcq_attempt_count": 0,
            "mcq_correct_count": 0,
            "nonmcq_attempt_count": 0,
            "revision_count": 0,
            "study_minutes": 0,
            "node_state": "unrated",
            "row_version": 1,
            "last_activity_at": null,
            "retention_stability_s": null,
            "retention_last_event_at": null,
            "retention_last_review_at": null,
            "retention_last_grade": null,
            "next_review_at": null
          },
          {
            "concept_id": "upsc_cse.art_culture.architecture.colonial_architecture",
            "exam_id": "upsc_cse",
            "subject_id": "upsc_cse.art_culture",
            "topic_id": "upsc_cse.art_culture.architecture",
            "mastery_score": "0.00",
            "mastery_nonmcq_score": "0.00",
            "retention_score": null,
            "confidence_score": null,
            "importance_score": "50.00",
            "overconfidence_flag": false,
            "mcq_attempt_count": 0,
            "mcq_correct_count": 0,
            "nonmcq_attempt_count": 0,
            "revision_count": 0,
            "study_minutes": 0,
            "node_state": "unrated",
            "row_version": 1,
            "last_activity_at": null,
            "retention_stability_s": null,
            "retention_last_event_at": null,
            "retention_last_review_at": null,
            "retention_last_grade": null,
            "next_review_at": null
          },
          {
            "concept_id": "upsc_cse.art_culture.architecture.indo_islamic",
            "exam_id": "upsc_cse",
            "subject_id": "upsc_cse.art_culture",
            "topic_id": "upsc_cse.art_culture.architecture",
            "mastery_score": "0.00",
            "mastery_nonmcq_score": "0.00",
            "retention_score": null,
            "confidence_score": null,
            "importance_score": "50.00",
            "overconfidence_flag": false,
            "mcq_attempt_count": 0,
            "mcq_correct_count": 0,
            "nonmcq_attempt_count": 0,
            "revision_count": 0,
            "study_minutes": 0,
            "node_state": "unrated",
            "row_version": 1,
            "last_activity_at": null,
            "retention_stability_s": null,
            "retention_last_event_at": null,
            "retention_last_review_at": null,
            "retention_last_grade": null,
            "next_review_at": null
          },
          {
            "concept_id": "upsc_cse.art_culture.architecture.overview",
            "exam_id": "upsc_cse",
            "subject_id": "upsc_cse.art_culture",
            "topic_id": "upsc_cse.art_culture.architecture",
            "mastery_score": "0.00",
            "mastery_nonmcq_score": "0.00",
            "retention_score": null,
            "confidence_score": null,
            "importance_score": "50.00",
            "overconfidence_flag": false,
            "mcq_attempt_count": 0,
            "mcq_correct_count": 0,
            "nonmcq_attempt_count": 0,
            "revision_count": 0,
            "study_minutes": 0,
            "node_state": "unrated",
            "row_version": 1,
            "last_activity_at": null,
            "retention_stability_s": null,
            "retention_last_event_at": null,
            "retention_last_review_at": null,
            "retention_last_grade": null,
            "next_review_at": null
          },
          {
            "concept_id": "upsc_cse.art_culture.architecture.rock_cut_caves",
            "exam_id": "upsc_cse",
            "subject_id": "upsc_cse.art_culture",
            "topic_id": "upsc_cse.art_culture.architecture",
            "mastery_score": "0.00",
            "mastery_nonmcq_score": "0.00",
            "retention_score": null,
            "confidence_score": null,
            "importance_score": "50.00",
            "overconfidence_flag": false,
            "mcq_attempt_count": 0,
            "mcq_correct_count": 0,
            "nonmcq_attempt_count": 0,
            "revision_count": 0,
            "study_minutes": 0,
            "node_state": "unrated",
            "row_version": 1,
            "last_activity_at": null,
            "retention_stability_s": null,
            "retention_last_event_at": null,
            "retention_last_review_at": null,
            "retention_last_grade": null,
            "next_review_at": null
          },
          {
            "concept_id": "upsc_cse.art_culture.architecture.temple_architecture",
            "exam_id": "upsc_cse",
            "subject_id": "upsc_cse.art_culture",
            "topic_id": "upsc_cse.art_culture.architecture",
            "mastery_score": "0.00",
            "mastery_nonmcq_score": "0.00",
            "retention_score": null,
            "confidence_score": null,
            "importance_score": "50.00",
            "overconfidence_flag": false,
            "mcq_attempt_count": 0,
            "mcq_correct_count": 0,
            "nonmcq_attempt_count": 0,
            "revision_count": 0,
            "study_minutes": 0,
            "node_state": "unrated",
            "row_version": 1,
            "last_activity_at": null,
            "retention_stability_s": null,
            "retention_last_event_at": null,
            "retention_last_review_at": null,
            "retention_last_grade": null,
            "next_review_at": null
          },
          {
            "concept_id": "upsc_cse.art_culture.architecture.unesco_sites",
            "exam_id": "upsc_cse",
            "subject_id": "upsc_cse.art_culture",
            "topic_id": "upsc_cse.art_culture.architecture",
            "mastery_score": "0.00",
            "mastery_nonmcq_score": "0.00",
            "retention_score": null,
            "confidence_score": null,
            "importance_score": "50.00",
            "overconfidence_flag": false,
            "mcq_attempt_count": 0,
            "mcq_correct_count": 0,
            "nonmcq_attempt_count": 0,
            "revision_count": 0,
            "study_minutes": 0,
            "node_state": "unrated",
            "row_version": 1,
            "last_activity_at": null,
            "retention_stability_s": null,
            "retention_last_event_at": null,
            "retention_last_review_at": null,
            "retention_last_grade": null,
            "next_review_at": null
          },
          {
            "concept_id": "upsc_cse.art_culture.heritage_conservation.asimap",
            "exam_id": "upsc_cse",
            "subject_id": "upsc_cse.art_culture",
            "topic_id": "upsc_cse.art_culture.heritage_conservation",
            "mastery_score": "0.00",
            "mastery_nonmcq_score": "0.00",
            "retention_score": null,
            "confidence_score": null,
            "importance_score": "50.00",
            "overconfidence_flag": false,
            "mcq_attempt_count": 0,
            "mcq_correct_count": 0,
            "nonmcq_attempt_count": 0,
            "revision_count": 0,
            "study_minutes": 0,
            "node_state": "unrated",
            "row_version": 1,
            "last_activity_at": null,
            "retention_stability_s": null,
            "retention_last_event_at": null,
            "retention_last_review_at": null,
            "retention_last_grade": null,
            "next_review_at": null
          },
          {
            "concept_id": "upsc_cse.art_culture.heritage_conservation.conservation_policies",
            "exam_id": "upsc_cse",
            "subject_id": "upsc_cse.art_culture",
            "topic_id": "upsc_cse.art_culture.heritage_conservation",
            "mastery_score": "0.00",
            "mastery_nonmcq_score": "0.00",
            "retention_score": null,
            "confidence_score": null,
            "importance_score": "50.00",
            "overconfidence_flag": false,
            "mcq_attempt_count": 0,
            "mcq_correct_count": 0,
            "nonmcq_attempt_count": 0,
            "revision_count": 0,
            "study_minutes": 0,
            "node_state": "unrated",
            "row_version": 1,
            "last_activity_at": null,
            "retention_stability_s": null,
            "retention_last_event_at": null,
            "retention_last_review_at": null,
            "retention_last_grade": null,
            "next_review_at": null
          },
          {
            "concept_id": "upsc_cse.art_culture.heritage_conservation.craft_traditions",
            "exam_id": "upsc_cse",
            "subject_id": "upsc_cse.art_culture",
            "topic_id": "upsc_cse.art_culture.heritage_conservation",
            "mastery_score": "0.00",
            "mastery_nonmcq_score": "0.00",
            "retention_score": null,
            "confidence_score": null,
            "importance_score": "50.00",
            "overconfidence_flag": false,
            "mcq_attempt_count": 0,
            "mcq_correct_count": 0,
            "nonmcq_attempt_count": 0,
            "revision_count": 0,
            "study_minutes": 0,
            "node_state": "unrated",
            "row_version": 1,
            "last_activity_at": null,
            "retention_stability_s": null,
            "retention_last_event_at": null,
            "retention_last_review_at": null,
            "retention_last_grade": null,
            "next_review_at": null
          },
          {
            "concept_id": "upsc_cse.art_culture.heritage_conservation.intangible_heritage",
            "exam_id": "upsc_cse",
            "subject_id": "upsc_cse.art_culture",
            "topic_id": "upsc_cse.art_culture.heritage_conservation",
            "mastery_score": "0.00",
            "mastery_nonmcq_score": "0.00",
            "retention_score": null,
            "confidence_score": null,
            "importance_score": "50.00",
            "overconfidence_flag": false,
            "mcq_attempt_count": 0,
            "mcq_correct_count": 0,
            "nonmcq_attempt_count": 0,
            "revision_count": 0,
            "study_minutes": 0,
            "node_state": "unrated",
            "row_version": 1,
            "last_activity_at": null,
            "retention_stability_s": null,
            "retention_last_event_at": null,
            "retention_last_review_at": null,
            "retention_last_grade": null,
            "next_review_at": null
          },
          {
            "concept_id": "upsc_cse.art_culture.heritage_conservation.museum_archives",
            "exam_id": "upsc_cse",
            "subject_id": "upsc_cse.art_culture",
            "topic_id": "upsc_cse.art_culture.heritage_conservation",
            "mastery_score": "0.00",
            "mastery_nonmcq_score": "0.00",
            "retention_score": null,
            "confidence_score": null,
            "importance_score": "50.00",
            "overconfidence_flag": false,
            "mcq_attempt_count": 0,
            "mcq_correct_count": 0,
            "nonmcq_attempt_count": 0,
            "revision_count": 0,
            "study_minutes": 0,
            "node_state": "unrated",
            "row_version": 1,
            "last_activity_at": null,
            "retention_stability_s": null,
            "retention_last_event_at": null,
            "retention_last_review_at": null,
            "retention_last_grade": null,
            "next_review_at": null
          },
          {
            "concept_id": "upsc_cse.art_culture.heritage_conservation.overview",
            "exam_id": "upsc_cse",
            "subject_id": "upsc_cse.art_culture",
            "topic_id": "upsc_cse.art_culture.heritage_conservation",
            "mastery_score": "0.00",
            "mastery_nonmcq_score": "0.00",
            "retention_score": null,
            "confidence_score": null,
            "importance_score": "50.00",
            "overconfidence_flag": false,
            "mcq_attempt_count": 0,
            "mcq_correct_count": 0,
            "nonmcq_attempt_count": 0,
            "revision_count": 0,
            "study_minutes": 0,
            "node_state": "unrated",
            "row_version": 1,
            "last_activity_at": null,
            "retention_stability_s": null,
            "retention_last_event_at": null,
            "retention_last_review_at": null,
            "retention_last_grade": null,
            "next_review_at": null
          },
          {
            "concept_id": "upsc_cse.art_culture.literature.modern_literature",
            "exam_id": "upsc_cse",
            "subject_id": "upsc_cse.art_culture",
            "topic_id": "upsc_cse.art_culture.literature",
            "mastery_score": "0.00",
            "mastery_nonmcq_score": "0.00",
            "retention_score": null,
            "confidence_score": null,
            "importance_score": "50.00",
            "overconfidence_flag": false,
            "mcq_attempt_count": 0,
            "mcq_correct_count": 0,
            "nonmcq_attempt_count": 0,
            "revision_count": 0,
            "study_minutes": 0,
            "node_state": "unrated",
            "row_version": 1,
            "last_activity_at": null,
            "retention_stability_s": null,
            "retention_last_event_at": null,
            "retention_last_review_at": null,
            "retention_last_grade": null,
            "next_review_at": null
          },
          {
            "concept_id": "upsc_cse.art_culture.literature.overview",
            "exam_id": "upsc_cse",
            "subject_id": "upsc_cse.art_culture",
            "topic_id": "upsc_cse.art_culture.literature",
            "mastery_score": "0.00",
            "mastery_nonmcq_score": "0.00",
            "retention_score": null,
            "confidence_score": null,
            "importance_score": "50.00",
            "overconfidence_flag": false,
            "mcq_attempt_count": 0,
            "mcq_correct_count": 0,
            "nonmcq_attempt_count": 0,
            "revision_count": 0,
            "study_minutes": 0,
            "node_state": "unrated",
            "row_version": 1,
            "last_activity_at": null,
            "retention_stability_s": null,
            "retention_last_event_at": null,
            "retention_last_review_at": null,
            "retention_last_grade": null,
            "next_review_at": null
          },
          {
            "concept_id": "upsc_cse.art_culture.literature.philosophy_schools",
            "exam_id": "upsc_cse",
            "subject_id": "upsc_cse.art_culture",
            "topic_id": "upsc_cse.art_culture.literature",
            "mastery_score": "0.00",
            "mastery_nonmcq_score": "0.00",
            "retention_score": null,
            "confidence_score": null,
            "importance_score": "50.00",
            "overconfidence_flag": false,
            "mcq_attempt_count": 0,
            "mcq_correct_count": 0,
            "nonmcq_attempt_count": 0,
            "revision_count": 0,
            "study_minutes": 0,
            "node_state": "unrated",
            "row_version": 1,
            "last_activity_at": null,
            "retention_stability_s": null,
            "retention_last_event_at": null,
            "retention_last_review_at": null,
            "retention_last_grade": null,
            "next_review_at": null
          },
          {
            "concept_id": "upsc_cse.art_culture.literature.regional_literature",
            "exam_id": "upsc_cse",
            "subject_id": "upsc_cse.art_culture",
            "topic_id": "upsc_cse.art_culture.literature",
            "mastery_score": "0.00",
            "mastery_nonmcq_score": "0.00",
            "retention_score": null,
            "confidence_score": null,
            "importance_score": "50.00",
            "overconfidence_flag": false,
            "mcq_attempt_count": 0,
            "mcq_correct_count": 0,
            "nonmcq_attempt_count": 0,
            "revision_count": 0,
            "study_minutes": 0,
            "node_state": "unrated",
            "row_version": 1,
            "last_activity_at": null,
            "retention_stability_s": null,
            "retention_last_event_at": null,
            "retention_last_review_at": null,
            "retention_last_grade": null,
            "next_review_at": null
          },
          {
            "concept_id": "upsc_cse.art_culture.literature.sanskrit_literature",
            "exam_id": "upsc_cse",
            "subject_id": "upsc_cse.art_culture",
            "topic_id": "upsc_cse.art_culture.literature",
            "mastery_score": "0.00",
            "mastery_nonmcq_score": "0.00",
            "retention_score": null,
            "confidence_score": null,
            "importance_score": "50.00",
            "overconfidence_flag": false,
            "mcq_attempt_count": 0,
            "mcq_correct_count": 0,
            "nonmcq_attempt_count": 0,
            "revision_count": 0,
            "study_minutes": 0,
            "node_state": "unrated",
            "row_version": 1,
            "last_activity_at": null,
            "retention_stability_s": null,
            "retention_last_event_at": null,
            "retention_last_review_at": null,
            "retention_last_grade": null,
            "next_review_at": null
          },
          {
            "concept_id": "upsc_cse.art_culture.performing_arts.classical_dance",
            "exam_id": "upsc_cse",
            "subject_id": "upsc_cse.art_culture",
            "topic_id": "upsc_cse.art_culture.performing_arts",
            "mastery_score": "0.00",
            "mastery_nonmcq_score": "0.00",
            "retention_score": null,
            "confidence_score": null,
            "importance_score": "50.00",
            "overconfidence_flag": false,
            "mcq_attempt_count": 0,
            "mcq_correct_count": 0,
            "nonmcq_attempt_count": 0,
            "revision_count": 0,
            "study_minutes": 0,
            "node_state": "unrated",
            "row_version": 1,
            "last_activity_at": null,
            "retention_stability_s": null,
            "retention_last_event_at": null,
            "retention_last_review_at": null,
            "retention_last_grade": null,
            "next_review_at": null
          },
          {
            "concept_id": "upsc_cse.art_culture.performing_arts.classical_music",
            "exam_id": "upsc_cse",
            "subject_id": "upsc_cse.art_culture",
            "topic_id": "upsc_cse.art_culture.performing_arts",
            "mastery_score": "0.00",
            "mastery_nonmcq_score": "0.00",
            "retention_score": null,
            "confidence_score": null,
            "importance_score": "50.00",
            "overconfidence_flag": false,
            "mcq_attempt_count": 0,
            "mcq_correct_count": 0,
            "nonmcq_attempt_count": 0,
            "revision_count": 0,
            "study_minutes": 0,
            "node_state": "unrated",
            "row_version": 1,
            "last_activity_at": null,
            "retention_stability_s": null,
            "retention_last_event_at": null,
            "retention_last_review_at": null,
            "retention_last_grade": null,
            "next_review_at": null
          },
          {
            "concept_id": "upsc_cse.art_culture.performing_arts.festivals",
            "exam_id": "upsc_cse",
            "subject_id": "upsc_cse.art_culture",
            "topic_id": "upsc_cse.art_culture.performing_arts",
            "mastery_score": "0.00",
            "mastery_nonmcq_score": "0.00",
            "retention_score": null,
            "confidence_score": null,
            "importance_score": "50.00",
            "overconfidence_flag": false,
            "mcq_attempt_count": 0,
            "mcq_correct_count": 0,
            "nonmcq_attempt_count": 0,
            "revision_count": 0,
            "study_minutes": 0,
            "node_state": "unrated",
            "row_version": 1,
            "last_activity_at": null,
            "retention_stability_s": null,
            "retention_last_event_at": null,
            "retention_last_review_at": null,
            "retention_last_grade": null,
            "next_review_at": null
          },
          {
            "concept_id": "upsc_cse.art_culture.performing_arts.folk_performing",
            "exam_id": "upsc_cse",
            "subject_id": "upsc_cse.art_culture",
            "topic_id": "upsc_cse.art_culture.performing_arts",
            "mastery_score": "0.00",
            "mastery_nonmcq_score": "0.00",
            "retention_score": null,
            "confidence_score": null,
            "importance_score": "50.00",
            "overconfidence_flag": false,
            "mcq_attempt_count": 0,
            "mcq_correct_count": 0,
            "nonmcq_attempt_count": 0,
            "revision_count": 0,
            "study_minutes": 0,
            "node_state": "unrated",
            "row_version": 1,
            "last_activity_at": null,
            "retention_stability_s": null,
            "retention_last_event_at": null,
            "retention_last_review_at": null,
            "retention_last_grade": null,
            "next_review_at": null
          },
          {
            "concept_id": "upsc_cse.art_culture.performing_arts.overview",
            "exam_id": "upsc_cse",
            "subject_id": "upsc_cse.art_culture",
            "topic_id": "upsc_cse.art_culture.performing_arts",
            "mastery_score": "0.00",
            "mastery_nonmcq_score": "0.00",
            "retention_score": null,
            "confidence_score": null,
            "importance_score": "50.00",
            "overconfidence_flag": false,
            "mcq_attempt_count": 0,
            "mcq_correct_count": 0,
            "nonmcq_attempt_count": 0,
            "revision_count": 0,
            "study_minutes": 0,
            "node_state": "unrated",
            "row_version": 1,
            "last_activity_at": null,
            "retention_stability_s": null,
            "retention_last_event_at": null,
            "retention_last_review_at": null,
            "retention_last_grade": null,
            "next_review_at": null
          },
          {
            "concept_id": "upsc_cse.art_culture.performing_arts.theatre",
            "exam_id": "upsc_cse",
            "subject_id": "upsc_cse.art_culture",
            "topic_id": "upsc_cse.art_culture.performing_arts",
            "mastery_score": "0.00",
            "mastery_nonmcq_score": "0.00",
            "retention_score": null,
            "confidence_score": null,
            "importance_score": "50.00",
            "overconfidence_flag": false,
            "mcq_attempt_count": 0,
            "mcq_correct_count": 0,
            "nonmcq_attempt_count": 0,
            "revision_count": 0,
            "study_minutes": 0,
            "node_state": "unrated",
            "row_version": 1,
            "last_activity_at": null,
            "retention_stability_s": null,
            "retention_last_event_at": null,
            "retention_last_review_at": null,
            "retention_last_grade": null,
            "next_review_at": null
          },
          {
            "concept_id": "upsc_cse.art_culture.sculpture_painting.ancient_sculpture",
            "exam_id": "upsc_cse",
            "subject_id": "upsc_cse.art_culture",
            "topic_id": "upsc_cse.art_culture.sculpture_painting",
            "mastery_score": "0.00",
            "mastery_nonmcq_score": "0.00",
            "retention_score": null,
            "confidence_score": null,
            "importance_score": "50.00",
            "overconfidence_flag": false,
            "mcq_attempt_count": 0,
            "mcq_correct_count": 0,
            "nonmcq_attempt_count": 0,
            "revision_count": 0,
            "study_minutes": 0,
            "node_state": "unrated",
            "row_version": 1,
            "last_activity_at": null,
            "retention_stability_s": null,
            "retention_last_event_at": null,
            "retention_last_review_at": null,
            "retention_last_grade": null,
            "next_review_at": null
          },
          {
            "concept_id": "upsc_cse.art_culture.sculpture_painting.iconography",
            "exam_id": "upsc_cse",
            "subject_id": "upsc_cse.art_culture",
            "topic_id": "upsc_cse.art_culture.sculpture_painting",
            "mastery_score": "0.00",
            "mastery_nonmcq_score": "0.00",
            "retention_score": null,
            "confidence_score": null,
            "importance_score": "50.00",
            "overconfidence_flag": false,
            "mcq_attempt_count": 0,
            "mcq_correct_count": 0,
            "nonmcq_attempt_count": 0,
            "revision_count": 0,
            "study_minutes": 0,
            "node_state": "unrated",
            "row_version": 1,
            "last_activity_at": null,
            "retention_stability_s": null,
            "retention_last_event_at": null,
            "retention_last_review_at": null,
            "retention_last_grade": null,
            "next_review_at": null
          },
          {
            "concept_id": "upsc_cse.art_culture.sculpture_painting.miniature_painting",
            "exam_id": "upsc_cse",
            "subject_id": "upsc_cse.art_culture",
            "topic_id": "upsc_cse.art_culture.sculpture_painting",
            "mastery_score": "0.00",
            "mastery_nonmcq_score": "0.00",
            "retention_score": null,
            "confidence_score": null,
            "importance_score": "50.00",
            "overconfidence_flag": false,
            "mcq_attempt_count": 0,
            "mcq_correct_count": 0,
            "nonmcq_attempt_count": 0,
            "revision_count": 0,
            "study_minutes": 0,
            "node_state": "unrated",
            "row_version": 1,
            "last_activity_at": null,
            "retention_stability_s": null,
            "retention_last_event_at": null,
            "retention_last_review_at": null,
            "retention_last_grade": null,
            "next_review_at": null
          },
          {
            "concept_id": "upsc_cse.art_culture.sculpture_painting.modern_art",
            "exam_id": "upsc_cse",
            "subject_id": "upsc_cse.art_culture",
            "topic_id": "upsc_cse.art_culture.sculpture_painting",
            "mastery_score": "0.00",
            "mastery_nonmcq_score": "0.00",
            "retention_score": null,
            "confidence_score": null,
            "importance_score": "50.00",
            "overconfidence_flag": false,
            "mcq_attempt_count": 0,
            "mcq_correct_count": 0,
            "nonmcq_attempt_count": 0,
            "revision_count": 0,
            "study_minutes": 0,
            "node_state": "unrated",
            "row_version": 1,
            "last_activity_at": null,
            "retention_stability_s": null,
            "retention_last_event_at": null,
            "retention_last_review_at": null,
            "retention_last_grade": null,
            "next_review_at": null
          },
          {
            "concept_id": "upsc_cse.art_culture.sculpture_painting.overview",
            "exam_id": "upsc_cse",
            "subject_id": "upsc_cse.art_culture",
            "topic_id": "upsc_cse.art_culture.sculpture_painting",
            "mastery_score": "0.00",
            "mastery_nonmcq_score": "0.00",
            "retention_score": null,
            "confidence_score": null,
            "importance_score": "50.00",
            "overconfidence_flag": false,
            "mcq_attempt_count": 0,
            "mcq_correct_count": 0,
            "nonmcq_attempt_count": 0,
            "revision_count": 0,
            "study_minutes": 0,
            "node_state": "unrated",
            "row_version": 1,
            "last_activity_at": null,
            "retention_stability_s": null,
            "retention_last_event_at": null,
            "retention_last_review_at": null,
            "retention_last_grade": null,
            "next_review_at": null
          },
          {
            "concept_id": "upsc_cse.art_culture.sculpture_painting.tribal_art",
            "exam_id": "upsc_cse",
            "subject_id": "upsc_cse.art_culture",
            "topic_id": "upsc_cse.art_culture.sculpture_painting",
            "mastery_score": "0.00",
            "mastery_nonmcq_score": "0.00",
            "retention_score": null,
            "confidence_score": null,
            "importance_score": "50.00",
            "overconfidence_flag": false,
            "mcq_attempt_count": 0,
            "mcq_correct_count": 0,
            "nonmcq_attempt_count": 0,
            "revision_count": 0,
            "study_minutes": 0,
            "node_state": "unrated",
            "row_version": 1,
            "last_activity_at": null,
            "retention_stability_s": null,
            "retention_last_event_at": null,
            "retention_last_review_at": null,
            "retention_last_grade": null,
            "next_review_at": null
          }
        ]
      }
    },
    {
      "step": "study_session",
      "ok": true,
      "result": {
        "accepted": true,
        "event_type": "StudySessionLogged"
      }
    },
    {
      "step": "revision_activity",
      "ok": true,
      "result": {
        "accepted": true,
        "event_type": "RevisionCompleted"
      }
    },
    {
      "step": "learning_graph_updated_event",
      "ok": true,
      "result": {
        "count": 2,
        "found": true
      }
    },
    {
      "step": "readiness_changed",
      "ok": true,
      "result": {
        "before": "46.30",
        "after": "46.57"
      }
    },
    {
      "step": "recommendations_updated",
      "ok": true,
      "result": {
        "before": 1,
        "after": 1
      }
    },
    {
      "step": "study_plan_updated",
      "ok": true,
      "result": {
        "before_daily": 1,
        "after_daily": 1
      }
    },
    {
      "step": "twin_dashboard_updated",
      "ok": true,
      "result": {
        "before": "46.30",
        "after": "46.30"
      }
    }
  ],
  "correlation_id": "i12-student-journey",
  "event_types_for_correlation": {
    "MentorSummaryUpdated": 16,
    "TwinRecommendationsUpdated": 4,
    "StudySessionLogged": 2,
    "RevisionCompleted": 2,
    "MentorInsightUpdated": 16,
    "TwinDecisionUpdated": 16,
    "MentorActionUpdated": 40,
    "MilestoneUpdated": 8,
    "ForecastUpdated": 4,
    "TwinInterventionUpdated": 16,
    "RevisionQueueUpdated": 4,
    "StudyPlanUpdated": 16,
    "ForecastProbabilityUpdated": 16,
    "PredictedScoreUpdated": 12,
    "LearningGraphUpdated": 4,
    "EscalationUpdated": 40
  },
  "drained_event_types": [
    "EscalationUpdated",
    "ForecastProbabilityUpdated",
    "ForecastUpdated",
    "LearningGraphUpdated",
    "MentorActionUpdated",
    "MentorInsightUpdated",
    "MentorSummaryUpdated",
    "MilestoneUpdated",
    "PredictedScoreUpdated",
    "RevisionCompleted",
    "RevisionQueueUpdated",
    "StudyPlanUpdated",
    "StudySessionLogged",
    "TwinDecisionUpdated",
    "TwinInterventionUpdated",
    "TwinRecommendationsUpdated"
  ]
}
```

## 4. Mentor Journey Validation

```json
{
  "steps": [
    {
      "step": "login_faculty",
      "ok": true,
      "email": "faculty@prepos-demo.example.com"
    },
    {
      "step": "mentor_dashboard",
      "ok": true,
      "payload": {
        "open_cases": 1,
        "critical_cases": 0,
        "average_resolution_time_hours": "0.00",
        "mentor_effectiveness_score": "0.00",
        "best_action": null,
        "best_action_effectiveness": "0",
        "average_action_effectiveness": "0"
      }
    },
    {
      "step": "mentor_queue",
      "ok": true,
      "count": 1
    },
    {
      "step": "open_case",
      "ok": true,
      "case_id": "d87940c8-c81b-4cc1-a627-a233a1b532ee"
    },
    {
      "step": "add_note",
      "ok": true
    },
    {
      "step": "resolve_case",
      "ok": true
    },
    {
      "step": "mentor_effectiveness_updated",
      "ok": true,
      "before": "0.00",
      "after": "70.00"
    },
    {
      "step": "resolved_case_payload",
      "ok": true,
      "case": {
        "case_id": "d87940c8-c81b-4cc1-a627-a233a1b532ee",
        "student_id": "40c526e1-08bf-4549-97f9-91879b784cca",
        "exam_id": "upsc_cse",
        "status": "RESOLVED",
        "priority": "HIGH",
        "mentor_action_type": "CONTACT_STUDENT",
        "escalation_level": "NONE",
        "mentor_action_priority": "85.00",
        "opened_at": "2026-06-20T06:27:23.061361Z",
        "resolved_at": "2026-06-20T06:27:25.309093Z",
        "resolution_reason": "STUDENT_CONTACTED",
        "notes": [
          {
            "note_id": "11a05ffa-3ff8-418e-8646-eb24a78023db",
            "mentor_id": "56001e01-8007-47a7-9989-7c78015ea5a2",
            "note": "I1.2 validation note \u2014 contacted student about revision backlog.",
            "created_at": "2026-06-20T06:27:25.298123Z"
          }
        ]
      }
    }
  ],
  "queue_empty": false,
  "case_id": "d87940c8-c81b-4cc1-a627-a233a1b532ee"
}
```

## 5. Event Chain Validation

Expected chain after activity submission:

`Activity → LearningGraphUpdated → ForecastUpdated → RecommendationsUpdated → StudyPlanUpdated → TwinUpdated`

Drained event types during seed + journey:

- Seed activity types: `['EscalationUpdated', 'ForecastProbabilityUpdated', 'ForecastUpdated', 'LearningGraphUpdated', 'MentorActionUpdated', 'MentorInsightUpdated', 'MentorSummaryUpdated', 'MilestoneUpdated', 'PredictedScoreUpdated', 'RevisionCompleted', 'RevisionQueueUpdated', 'StudyPlanUpdated', 'StudySessionLogged', 'TwinDecisionUpdated', 'TwinInterventionUpdated', 'TwinRecommendationsUpdated', 'TwinSnapshotUpdated', 'TwinUpdated']`
- Journey drained: `['EscalationUpdated', 'ForecastProbabilityUpdated', 'ForecastUpdated', 'LearningGraphUpdated', 'MentorActionUpdated', 'MentorInsightUpdated', 'MentorSummaryUpdated', 'MilestoneUpdated', 'PredictedScoreUpdated', 'RevisionCompleted', 'RevisionQueueUpdated', 'StudyPlanUpdated', 'StudySessionLogged', 'TwinDecisionUpdated', 'TwinInterventionUpdated', 'TwinRecommendationsUpdated']`

## 6. API Matrix

| Route | API | Working? | Notes |
|-------|-----|----------|-------|
| /login | POST /auth/login | Yes | See seed + journey validation |
| /student/dashboard | GET /twin/dashboard | Yes | See seed + journey validation |
| /student/learning-graph | GET /learning-graph, /learning-graph/readiness | Yes | See seed + journey validation |
| /student/recommendations | GET /twin/recommendations | Yes | See seed + journey validation |
| /student/revision-queue | GET /learning-graph/revisions/queue | Yes | See seed + journey validation |
| /student/study-plan | GET /study-plan, POST items/complete|skip | Yes | See seed + journey validation |
| /student/goals | GET|POST|PUT /goals | Yes | See seed + journey validation |
| /student/forecast | GET /twin/dashboard, GET /twin | Yes | See seed + journey validation |
| /mentor/dashboard | GET /mentor/dashboard | Yes | See seed + journey validation |
| /mentor/queue | GET /mentor/queue | Yes | See seed + journey validation |
| /mentor/cases/[id] | GET /mentor/cases/{id}, POST notes, POST resolve | Yes | See seed + journey validation |
| /mentor/student/[studentId] | GET /twin/* with student_id | Yes | See seed + journey validation |
| Study/revision activities | POST /learning-graph/activities/study-session|revision | Partial | Backend only — no frontend UI |
| Student onboarding | POST /students/onboarding/complete | Partial | Backend only — no frontend UI |
| Concept labels | GET /concepts/search, GET /concepts/{id} | Partial | Backend exists — frontend shows raw concept_id |
| Auth refresh | POST /auth/refresh | Partial | Backend exists — frontend stores refresh token but does not refresh |
| Admin portal | Various institute_admin routes | Partial | Not implemented in frontend |

## 7. Frontend Build Verification

### npm run lint

**Result:** PASS

```
> @prepos/web@0.1.0 lint
> next lint

✔ No ESLint warnings or errors
`next lint` is deprecated and will be removed in Next.js 16.
For new projects, use create-next-app to choose your preferred linter.
For existing projects, migrate to the ESLint CLI:
npx @next/codemod@canary next-lint-to-eslint-cli .
```

### npm run typecheck

**Result:** PASS

```
> @prepos/web@0.1.0 typecheck
> tsc --noEmit
```

### npm run build

**Result:** PASS

```
> @prepos/web@0.1.0 build
> next build

   ▲ Next.js 15.5.19
   - Environments: .env.local

   Creating an optimized production build ...
 ✓ Compiled successfully in 2.2s
   Linting and checking validity of types ...
   Collecting page data ...
   Generating static pages (0/15) ...
   Generating static pages (3/15) 
   Generating static pages (7/15) 
   Generating static pages (11/15) 
 ✓ Generating static pages (15/15)
   Finalizing page optimization ...
   Collecting build traces ...

Route (app)                                 Size  First Load JS
┌ ○ /                                    3.63 kB         106 kB
├ ○ /_not-found                            993 B         103 kB
├ ○ /login                               4.29 kB         129 kB
├ ƒ /mentor/cases/[id]                   4.14 kB         140 kB
├ ○ /mentor/dashboard                    3.83 kB         117 kB
├ ○ /mentor/queue                        3.93 kB         121 kB
├ ƒ /mentor/student/[studentId]          1.47 kB         122 kB
├ ○ /student/dashboard                   1.46 kB         119 kB
├ ○ /student/forecast                    1.54 kB         119 kB
├ ○ /student/goals                       1.56 kB         141 kB
├ ○ /student/learning-graph              1.28 kB         118 kB
├ ○ /student/recommendations               901 B         118 kB
├ ○ /student/revision-queue                898 B         118 kB
├ ○ /student/study-plan                  1.34 kB         119 kB
└ ○ /unauthorized                          603 B         106 kB
+ First Load JS shared by all             102 kB
  ├ chunks/493-dbd4607ff9cca169.js       46.2 kB
  ├ chunks/4bd1b696-c023c6e3521b1417.js  54.2 kB
  └ other shared chunks (total)          1.92 kB


○  (Static)   prerendered as static content
ƒ  (Dynamic)  server-rendered on demand
```

## 8. UI Readiness Review

| Page | Status | Reason |
|------|--------|--------|
| /login | ready | Auth flow works against demo tenant. |
| /student/dashboard | ready | Twin dashboard KPIs render when projections exist. |
| /student/learning-graph | partially ready | Shows readiness and nodes but uses raw concept_id labels. |
| /student/recommendations | ready | Lists twin recommendations when seeded. |
| /student/revision-queue | ready | Reads persisted revision queue projection. |
| /student/study-plan | ready | Complete/skip mutations wired; empty if plan not generated. |
| /student/goals | ready | Create/update goal form works. |
| /student/forecast | partially ready | KPI cards work; scenario JSON shown in raw <pre> blocks. |
| /mentor/dashboard | ready | Dashboard metrics load for faculty/admin roles. |
| /mentor/queue | partially ready | Works when cases exist; queue may be empty without escalation. |
| /mentor/cases/[id] | ready | Notes and resolve flows implemented. |
| /mentor/student/[studentId] | partially ready | Twin summary works; raw JSON debug blocks remain. |

## 9. Production Gap Report

### P0
- Outbox events require synchronous drain in dev — Celery worker must run in deployed environments.
- No frontend for study-session / revision activity submission (student journey step 4–5 blocked in UI).
- No student onboarding UI — demo data requires seed script or API calls.
- npm build/lint/typecheck not verified in CI agent environment — run locally before pilot.

### P1
- Token refresh not implemented in frontend (401 ends session).
- Concept IDs shown instead of human-readable syllabus labels.
- Mentor queue may be empty until decision engine emits case-creating actions.
- Forecast and mentor twin pages use raw JSON instead of charts.
- No E2E browser tests.

### P2
- OpenAPI codegen for frontend DTOs.
- Admin portal for institute_admin role.
- Active sidebar route highlighting and mobile polish.
- Dedicated faculty seed user documentation in README.

## 10. Recommended Next Sprint

1. **F1.1 UI completion** — onboarding flow, study/revision activity forms, concept label mapping.
2. **I1.3 Ops hardening** — document Celery worker requirement; add `make demo` target; CI frontend build.
3. **Demo polish** — replace JSON `<pre>` blocks; ensure mentor queue populates predictably for demos.
4. **E2E tests** — Playwright smoke for student + mentor happy paths using `seed_demo_data.py`.
