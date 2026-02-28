# 项目接口总览（All Endpoints）

更新时间：2026-02-28  
后端入口：`app/main.py`，统一前缀：`/api/v1`

## 1. 全局约定

### 1.1 Base URL

- 本地默认：`http://localhost:8000`

### 1.2 鉴权

- 仅 `teacher` 路由要求鉴权：
  - `Authorization: Bearer <token>`
- 其它基础路由（`/api/v1/materials`、`/api/v1/students`、`/api/v1/escalations`、`/api/v1/messages`）当前不要求鉴权。

### 1.3 响应包裹规则（仅 teacher）

`/api/v1/teacher/*` 经过中间件统一包裹：

成功：

```json
{
  "success": true,
  "data": {}
}
```

失败：

```json
{
  "success": false,
  "error": {
    "detail": "..."
  }
}
```

## 2. 系统接口

| Method | Path | 鉴权 | 说明 | 返回关键字段 |
|---|---|---|---|---|
| GET | `/health` | 否 | 服务健康检查 | `status` (`ok`) |

## 3. Teacher 接口（共 33 个操作）

### 3.1 教材管理（Materials）

| Method | Path | 说明 | 请求关键字段 | 返回关键字段 |
|---|---|---|---|---|
| POST | `/api/v1/teacher/materials/upload` | 上传教材元信息，进入 queued | `teacher_id`, `file_name`, `file_path`, `source_type`, `tags?` | `material_id`, `status`, `stored_at` |
| GET | `/api/v1/teacher/materials/{material_id}/status` | 查询教材状态 | `material_id` (path) | `material_id`, `status`, `stored_at`, `updated_at` |
| PUT | `/api/v1/teacher/materials/{material_id}/boundary` | 更新教材边界严格度 | `strictness`, `reason?` | `material_id`, `strictness`, `updated_at` |
| PUT | `/api/v1/teacher/materials/{material_id}/importance` | 标注知识点重要度 | `marks[]` (`concept`, `level`, `note?`) | `material_id`, `marks_saved`, `updated_at` |
| GET | `/api/v1/teacher/materials/{material_id}/knowledge-graph` | 获取教材知识图谱 | `material_id` (path) | `material_id`, `nodes[]`, `edges[]` |
| DELETE | `/api/v1/teacher/materials/{material_id}` | 删除教材（幂等） | `material_id` (path) | `material_id`, `deleted`, `deleted_at` |

### 3.2 监控面板（Monitor）

| Method | Path | 说明 | 请求关键字段 | 返回关键字段 |
|---|---|---|---|---|
| GET | `/api/v1/teacher/classes/{class_id}/overview` | 班级聚合看板 | `class_id` (path) | `total_students`, `total_interactions`, `pending_escalations`, `at_risk_students` |
| GET | `/api/v1/teacher/classes/{class_id}/students` | 班级学生列表 | `class_id` (path) | `students[]` (`student_id`, `mastery_score`, `latest_topic`) |
| GET | `/api/v1/teacher/students/{student_id}` | 学生详情 | `student_id` (path) | `profile`, `mastery_score`, `latest_topic` |
| GET | `/api/v1/teacher/students/{student_id}/cognition` | 学生认知模型 | `student_id` (path) | `mastery_score`, `misconceptions`, `confidence` |
| GET | `/api/v1/teacher/students/{student_id}/agent-logs` | Agent 决策日志 | `student_id` (path) | `logs[]` (`timestamp`, `agent`, `decision`, `tool`) |
| GET | `/api/v1/teacher/students/{student_id}/interactions` | 学生交互记录（可过滤） | `student_id` (path), `topic?`, `start_date?`, `end_date?`, `limit?` | `total`, `items[]` |

### 3.3 干预控制台（Intervene）

| Method | Path | 说明 | 请求关键字段 | 返回关键字段 |
|---|---|---|---|---|
| GET | `/api/v1/teacher/escalations` | 待处理升级列表 | - | `escalations[]` |
| GET | `/api/v1/teacher/escalations/{escalation_id}` | 升级详情 | `escalation_id` (path) | `escalation_id`, `detail` |
| POST | `/api/v1/teacher/escalations/{escalation_id}/respond` | 教师响应升级并 resolved | `teacher_id`, `action`, `message?` | `escalation_id`, `resolved`, `responded_at` |
| POST | `/api/v1/teacher/messages/send` | 教师发消息给学生 | `teacher_id`, `student_id`, `content`, `channel` | `message_id`, `delivery_state`, `created_at` |
| GET | `/api/v1/teacher/messages/conversations/{student_id}` | 查询与某学生会话 | `student_id` (path) | `student_id`, `total`, `items[]` |
| PUT | `/api/v1/teacher/companion/pause` | 暂停/恢复 companion | `paused`, `scope`, `reason?`, `class_id?` | `paused`, `scope`, `updated_at` |

### 3.4 配置中心（Config）

| Method | Path | 说明 | 请求关键字段 | 返回关键字段 |
|---|---|---|---|---|
| GET | `/api/v1/teacher/config` | 读取教师全局配置 | `teacher_id?` (query) | `teacher_id`, `config` |
| PUT | `/api/v1/teacher/config` | 更新教师全局配置 | `teacher_id`, `config` | `teacher_id`, `config` |
| GET | `/api/v1/teacher/classes/{class_id}/config` | 读取班级配置（含覆盖） | `class_id` (path), `teacher_id?` (query) | `teacher_id`, `config` |
| PUT | `/api/v1/teacher/classes/{class_id}/config` | 更新班级覆盖配置 | `class_id` (path), `teacher_id`, `config` | `teacher_id`, `config` |
| PUT | `/api/v1/teacher/config/notifications` | 更新通知策略字段 | `teacher_id`, `notification_escalation_threshold`, `notification_delivery[]` | `teacher_id`, `config` |

### 3.5 教案与课件（Lesson Plan / PPT）

| Method | Path | 说明 | 请求关键字段 | 返回关键字段 |
|---|---|---|---|---|
| POST | `/api/v1/teacher/lesson-plans/generate` | 生成教案 | `teacher_id`, `class_id`, `title`, `objective`, `topics?`, `material_ids?` | `plan_id`, `sections[]`, `version`, `updated_at` |
| GET | `/api/v1/teacher/lesson-plans/{plan_id}` | 获取教案详情 | `plan_id` (path) | `plan_id`, `title`, `objective`, `sections[]`, `version` |
| PUT | `/api/v1/teacher/lesson-plans/{plan_id}` | 更新教案并递增版本 | `plan_id` (path), `teacher_id`, `title?/objective?/topics?/sections?` | `plan_id`, `version`, `updated_at` |
| DELETE | `/api/v1/teacher/lesson-plans/{plan_id}` | 删除教案（幂等） | `plan_id` (path) | `plan_id`, `deleted`, `deleted_at` |
| POST | `/api/v1/teacher/lesson-plans/{plan_id}/ppt` | 基于教案生成 PPT | `plan_id` (path), `teacher_id`, `template` | `ppt_id`, `status`, `poll_url` |
| GET | `/api/v1/teacher/ppt/{ppt_id}/status` | 查询 PPT 状态 | `ppt_id` (path) | `ppt_id`, `status`, `progress` |
| GET | `/api/v1/teacher/ppt/{ppt_id}/download` | 获取下载地址 | `ppt_id` (path) | `ppt_id`, `download_url` |
| GET | `/api/v1/teacher/ppt/{ppt_id}/preview` | 获取预览图列表 | `ppt_id` (path) | `ppt_id`, `preview_images[]` |
| GET | `/api/v1/teacher/lesson-templates` | 模板列表 | - | `templates[]` |

### 3.6 鉴权验证（Auth）

| Method | Path | 说明 | 请求关键字段 | 返回关键字段 |
|---|---|---|---|---|
| GET | `/api/v1/teacher/profile` | 鉴权与包裹格式验证 | `Authorization` Header | `id`, `role` |

## 4. 非 Teacher 基础接口（共 4 个操作）

| Method | Path | 鉴权 | 说明 | 请求关键字段 | 返回关键字段 |
|---|---|---|---|---|---|
| POST | `/api/v1/materials/ingest` | 否 | 基础材料摄取占位接口 | 任意 `payload` | `status`, `payload` |
| GET | `/api/v1/students/{student_id}` | 否 | 基础学生查询占位接口 | `student_id` (path) | `student_id` |
| POST | `/api/v1/escalations/` | 否 | 基础升级占位接口 | 任意 `payload` | `status`, `payload` |
| POST | `/api/v1/messages/` | 否 | 基础消息占位接口 | 任意 `payload` | `status`, `payload` |

## 5. 常见状态码

- `200`: 请求成功。
- `401`: teacher 路由缺少或错误 Bearer Token。
- `404`: 资源不存在（如 `material_not_found`、`lesson_plan_not_found`、`ppt_not_found`）。
- `409`: 下载尚未就绪（`ppt_not_ready`）。
- `422`: 请求体字段缺失或类型不匹配。

## 6. E2E 推荐调用顺序

1. 教材链路：`upload -> status -> boundary -> importance -> knowledge-graph -> delete`
2. 干预链路：`escalations(list/detail) -> respond -> messages/send -> conversations -> companion/pause`
3. 教案链路：`lesson-plans/generate -> get -> update -> ppt -> status/preview/download -> delete`

对应可视化联测前端：`frontend/Superpower E2E Console`（见 `frontend/README.md`）。
