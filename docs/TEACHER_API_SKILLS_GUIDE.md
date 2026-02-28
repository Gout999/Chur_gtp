# Teacher API and Skills Guide

This guide documents the teacher-side API, skill manifests, and local runbook for the current MVP implementation.

## 1. Authentication

Teacher endpoints require:

```
Authorization: Bearer <token>
```

## 2. Response Envelope

All `/api/v1/teacher/*` endpoints return a consistent envelope:

```json
{
  "success": true,
  "data": {}
}
```

Error case:

```json
{
  "success": false,
  "error": {
    "detail": "..."
  }
}
```

## 3. Endpoint Summary

### 3.1 Material Manager

- `POST /api/v1/teacher/materials/upload`
- `GET /api/v1/teacher/materials/{material_id}/status`
- `PUT /api/v1/teacher/materials/{material_id}/boundary`
- `PUT /api/v1/teacher/materials/{material_id}/importance`
- `GET /api/v1/teacher/materials/{material_id}/knowledge-graph`
- `DELETE /api/v1/teacher/materials/{material_id}`

### 3.2 Monitor Dashboard

- `GET /api/v1/teacher/classes/{class_id}/overview`
- `GET /api/v1/teacher/classes/{class_id}/students`
- `GET /api/v1/teacher/students/{student_id}`
- `GET /api/v1/teacher/students/{student_id}/cognition`
- `GET /api/v1/teacher/students/{student_id}/agent-logs`
- `GET /api/v1/teacher/students/{student_id}/interactions`

### 3.3 Intervene Console

- `GET /api/v1/teacher/escalations`
- `GET /api/v1/teacher/escalations/{escalation_id}`
- `POST /api/v1/teacher/escalations/{escalation_id}/respond`
- `POST /api/v1/teacher/messages/send`
- `GET /api/v1/teacher/messages/conversations/{student_id}`
- `PUT /api/v1/teacher/companion/pause`

### 3.4 Config Manager

- `GET /api/v1/teacher/config`
- `PUT /api/v1/teacher/config`
- `GET /api/v1/teacher/classes/{class_id}/config`
- `PUT /api/v1/teacher/classes/{class_id}/config`
- `PUT /api/v1/teacher/config/notifications`

### 3.5 Lesson Plan Generator

- `POST /api/v1/teacher/lesson-plans/generate`
- `GET /api/v1/teacher/lesson-plans/{plan_id}`
- `PUT /api/v1/teacher/lesson-plans/{plan_id}`
- `DELETE /api/v1/teacher/lesson-plans/{plan_id}`
- `POST /api/v1/teacher/lesson-plans/{plan_id}/ppt`
- `GET /api/v1/teacher/ppt/{ppt_id}/status`
- `GET /api/v1/teacher/ppt/{ppt_id}/download`
- `GET /api/v1/teacher/ppt/{ppt_id}/preview`
- `GET /api/v1/teacher/lesson-templates`

## 4. Skills

Skills are located under `skills/`:

- `skills/material_manager`
- `skills/monitor_dashboard`
- `skills/intervene_console`
- `skills/config_manager`
- `skills/lesson_plan_generator`

Each skill includes:

- `skill.yaml`: metadata and tool list
- `entry.py`: runnable entrypoint

Example:

```bash
python skills/material_manager/entry.py '{"action":"ping"}'
```

Expected output shape:

```json
{
  "status": "not_implemented",
  "skill": "material-manager",
  "received_args": {
    "action": "ping"
  }
}
```

## 5. Local Runbook

### 5.1 Bootstrap

```bash
./init.sh
```

### 5.2 Run API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5.3 Run Teacher Integration and E2E Tests

```bash
pytest -q \
  tests/integration/test_teacher_auth_envelope.py \
  tests/integration/test_teacher_material_upload.py \
  tests/integration/test_teacher_monitor_endpoints.py \
  tests/integration/test_teacher_intervene_endpoints.py \
  tests/integration/test_teacher_config_endpoints.py \
  tests/integration/test_teacher_lesson_plan_endpoints.py \
  tests/integration/test_teacher_skills_scaffold.py \
  tests/e2e/test_teacher_workflows.py
```
