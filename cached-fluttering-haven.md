# EduGuide 教师端开发计划（符合DEVELOPER_GUIDE）

## 一、项目背景与目标

### 1.1 当前状态
- **核心框架**：LangGraph + 共享记忆架构已完成（Phase 1）
- **Agent系统**：Architect/Companion/Catalyst 节点已实现（Phase 2-4）
- **教师端PRD**：`EduGuide_教师端PRD.md` 已定义4个模块

### 1.2 本计划目标
完成教师端全功能实现，包括：
- 模块1-4的完整后端实现
- 模块5（AI教案+PPT）新增实现
- 所有功能通过 **Skills** 暴露给Agent使用
- 确保与核心框架、共享记忆系统完全连通

---

## 二、架构设计（Skills驱动）

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           教师端 Skills 架构                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │                        Skill Registry                               │ │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ │ │
│  │  │ Skill:       │ │ Skill:       │ │ Skill:       │ │ Skill:       │ │ │
│  │  │ Material     │ │ Monitor      │ │ Intervene    │ │ LessonPlan   │ │ │
│  │  │ Manager      │ │ Dashboard    │ │ Console      │ │ Generator    │ │ │
│  │  │ (教材管理)    │ │ (学生监控)    │ │ (干预控制台)  │ │ (教案/PPT)   │ │ │
│  │  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘ │ │
│  │  ┌──────────────┐                                                   │ │
│  │  │ Skill:       │                                                   │ │
│  │  │ Config       │                                                   │ │
│  │  │ Manager      │                                                   │ │
│  │  │ (班级配置)    │                                                   │ │
│  │  └──────────────┘                                                   │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                    │                                     │
│                                    ▼                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │                        Tools Layer                                  │ │
│  │  (每个Skill对应1-N个Tools，通过 @tool 装饰器注册)                      │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                    │                                     │
│                                    ▼                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │                     Shared Memory (通用层)                           │ │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ │ │
│  │  │ teacher_     │ │ teacher_     │ │ pending_     │ │ teacher_     │ │ │
│  │  │ uploads      │ │ authority_   │ │ escalations  │ │ lesson_plans │ │ │
│  │  │              │ │ graph        │ │              │ │              │ │ │
│  │  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘ │ │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ │ │
│  │  │ teacher_     │ │ teacher_     │ │ generated_   │ │ interaction_ │ │ │
│  │  │ escalation_  │ │ student_     │ │ ppts         │ │ episodes     │ │ │
│  │  │ responses    │ │ messages     │ │              │ │ (读)         │ │ │
│  │  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 三、共享记忆层设计（符合DEVELOPER_GUIDE）

### 3.1 架构约束

根据DEVELOPER_GUIDE.md：
- `memory/*` 属于 **Phase 1 框架负责人** 管理范围
- 所有人**只读**，修改需框架负责人统一执行
- 新增namespace需添加到 `memory/shared.py` 的 `NAMESPACES` 字典
- 三层架构：working.py (Redis) → external.py (ChromaDB+PostgreSQL) → archive.py (文件系统)

### 3.2 现有Namespace（memory/shared.py已有）

| Namespace | 写入方 | 读取方 | 存储位置 |
|-----------|--------|--------|----------|
| `teacher_uploads` | 教师端 | Architect | external |
| `teacher_authority_graph` | Architect | Companion, 教师端 | external |
| `teacher_boundary_adjustments` | 教师端 | Architect | external |
| `teacher_escalation_responses` | 教师端 | Companion | external |
| `teacher_student_messages` | 教师端 | Companion, 学生端 | external |
| `student_cognitive_models` | Companion | Architect, Catalyst, 教师端 | external |
| `interaction_episodes` | 所有Agent | 所有Agent, 教师端 | external |
| `pending_escalations` | Companion | 教师端 | **working** |
| `pending_validations` | Catalyst | Architect | external |
| `interest_signals` | Companion | Catalyst | external |
| `companion_control` | 教师端 | Companion | **working** |

### 3.3 需新增的Namespace（需框架负责人修改）

```python
# 需添加到 memory/shared.py 的 NAMESPACES 字典

NAMESPACES.update({
    # 教师端配置（External Memory）
    "teacher_configurations": "教师班级配置、Agent行为参数",
    "teacher_importance_marks": "教师标记的概念重要性、教学建议",

    # AI教案与PPT（External Memory）
    "teacher_lesson_plans": "AI生成教案、教师编辑内容（学生端可读）",
    "generated_ppts": "PPT文件元数据、预览图路径",

    # 审计日志（Archive Memory - 文件系统）
    "teacher_audit_logs": "教师操作审计日志",
})
```

### 3.4 存储层分配

| 存储层 | 对应文件 | 存储内容 | 适用Namespace |
|--------|---------|---------|--------------|
| **Working** | `memory/working.py` | Redis高速缓存 | `pending_escalations`, `companion_control` |
| **External** | `memory/external.py` | ChromaDB+PostgreSQL | 大部分namespace（持久化数据） |
| **Archive** | `memory/archive.py` | 文件系统 | `teacher_audit_logs`, PPT实际文件 |

---

## 四、Skills 详细设计

### Skill 1: Material Manager（教材管理）

**文件**: `skills/material_manager/skill.yaml`

```yaml
name: material-manager
description: 教师上传教材、管理知识边界、查看知识图谱
entry:
  command: python
  args:
    - "{skill_path}/entry.py"
    - "{args}"

tools:
  - teacher_upload_material
  - teacher_get_material_status
  - teacher_adjust_boundary
  - teacher_mark_importance
  - teacher_get_knowledge_graph
  - teacher_delete_material
```

**API端点**:

```python
POST   /api/v1/teacher/materials/upload
GET    /api/v1/teacher/materials/{material_id}/status
PUT    /api/v1/teacher/materials/{material_id}/boundary
PUT    /api/v1/teacher/materials/{material_id}/importance
GET    /api/v1/teacher/materials/{material_id}/knowledge-graph
DELETE /api/v1/teacher/materials/{material_id}
```

---

### Skill 2: Monitor Dashboard（学生监控）

```yaml
name: monitor-dashboard
description: 教师查看班级总览、学生详情、Agent决策日志
tools:
  - teacher_get_class_overview
  - teacher_get_student_detail
  - teacher_get_student_cognition
  - teacher_view_agent_logs
  - teacher_query_interaction_history
```

**API端点**:

```python
GET /api/v1/teacher/classes/{class_id}/overview
GET /api/v1/teacher/classes/{class_id}/students
GET /api/v1/teacher/students/{student_id}
GET /api/v1/teacher/students/{student_id}/cognition
GET /api/v1/teacher/students/{student_id}/agent-logs
GET /api/v1/teacher/students/{student_id}/interactions
```

---

### Skill 3: Intervene Console（干预控制台）

```yaml
name: intervene-console
description: 教师响应escalation、发送消息、调整Agent策略
tools:
  - teacher_get_escalations
  - teacher_get_escalation_detail
  - teacher_respond_to_escalation
  - teacher_send_message
  - teacher_pause_companion
  - teacher_get_conversations
```

**API端点**:

```python
GET  /api/v1/teacher/escalations
GET  /api/v1/teacher/escalations/{escalation_id}
POST /api/v1/teacher/escalations/{escalation_id}/respond
POST /api/v1/teacher/messages/send
GET  /api/v1/teacher/messages/conversations/{student_id}
PUT  /api/v1/teacher/companion/pause
```

---

### Skill 4: Config Manager（班级配置）

```yaml
name: config-manager
description: 教师配置班级参数、Agent行为偏好、通知设置
tools:
  - teacher_get_config
  - teacher_update_config
  - teacher_get_class_config
  - teacher_update_class_config
  - teacher_configure_notifications
```

---

### Skill 5: LessonPlan Generator（AI教案与PPT）

```yaml
name: lesson-plan-generator
description: AI辅助教案生成、PPT导出、预览管理
tools:
  - generate_lesson_plan
  - get_lesson_plan
  - update_lesson_plan
  - delete_lesson_plan
  - generate_lesson_ppt
  - get_ppt_status
  - get_ppt_download
  - get_ppt_preview
  - list_lesson_plan_templates
```

**数据流**:

```
教师: 选择教材 + 输入目标
    │
    ▼
POST /lesson-plans/generate
    │
    ▼
[Tool: generate_lesson_plan]
    1. 读取 teacher_authority_graph
    2. LLM生成教案结构
    3. 写入 teacher_lesson_plans
    │
    ▼
返回: {plan_id, preview_data}
    │
    ▼
教师: 预览/编辑
    │
    ▼
POST /lesson-plans/{plan_id}/ppt
    │
    ▼
[Tool: generate_lesson_ppt]
    1. 读取 teacher_lesson_plans
    2. 填充PPT模板
    3. 生成PPT → output/ppts/
    4. 生成预览图 → output/previews/
    5. 写入 generated_ppts
    │
    ▼
轮询: GET /ppt/{ppt_id}/status
    │
    ▼ (completed)
提供: 预览图 + 下载链接
```

---

## 五、文件结构

```
EduGuide/
├── skills/                              # 新增Skills目录
│   ├── material_manager/
│   │   ├── skill.yaml
│   │   └── entry.py
│   ├── monitor_dashboard/
│   │   ├── skill.yaml
│   │   └── entry.py
│   ├── intervene_console/
│   │   ├── skill.yaml
│   │   └── entry.py
│   ├── config_manager/
│   │   ├── skill.yaml
│   │   └── entry.py
│   └── lesson_plan_generator/
│       ├── skill.yaml
│       └── entry.py
│
├── tools/                               # 扩展
│   ├── material_manager.py
│   ├── monitor_dashboard.py
│   ├── intervene_console.py
│   ├── config_manager.py
│   └── lesson_plan_generator.py
│
├── app/api/v1/endpoints/
│   ├── materials.py
│   ├── monitor.py
│   ├── intervene.py
│   ├── config.py
│   └── lesson_plans.py
│
├── templates/                           # PPT模板
│   ├── lesson_default.pptx
│   ├── lesson_minimal.pptx
│   └── lesson_colorful.pptx
│
└── output/                              # PPT输出（.gitignore）
    ├── ppts/
    └── previews/
```

---

## 六、文件归属与协作规范

### 6.1 教师端专属文件（新增）

| 归属 | 路径 | 说明 |
|------|------|------|
| **教师端开发** | `skills/*` | 5个Skill目录及实现 |
| **教师端开发** | `tools/*_manager.py` | 各模块Tools |
| **教师端开发** | `app/api/v1/endpoints/*.py` | API端点实现 |
| **教师端开发** | `templates/*.pptx` | PPT模板文件 |
| **教师端开发** | `output/` | PPT输出目录 |

### 6.2 需协调的文件（框架负责人管理）

| 路径 | 修改内容 | 协调方式 |
|------|---------|---------|
| `memory/shared.py` | 新增4个namespace | 提交namespace列表给框架负责人 |
| `requirements.txt` | 添加python-pptx | 告知框架负责人 |
| `.gitignore` | 添加output/目录 | 告知框架负责人 |

### 6.3 Namespace修改申请

提交给框架负责人：

```python
# memory/shared.py 新增：
"teacher_configurations": "教师班级配置、Agent行为参数（External Memory）",
"teacher_importance_marks": "教师标记的概念重要性、教学建议（External Memory）",
"teacher_lesson_plans": "AI生成教案、教师编辑内容（External Memory）",
"generated_ppts": "PPT文件元数据、预览图路径（External Memory）",
```

---

## 七、开发阶段

### Phase 1: 基础设施（Day 1）
- [ ] 创建Skills目录结构
- [ ] 与框架负责人协调，新增namespace到memory/shared.py
- [ ] 添加python-pptx依赖
- [ ] 创建output/目录并配置.gitignore

### Phase 2: Material Manager（Day 1-2）
- [ ] 实现上传Tool → teacher_uploads
- [ ] 实现状态查询Tool
- [ ] 实现边界调整Tool → teacher_boundary_adjustments
- [ ] 实现重要性标记Tool → teacher_importance_marks
- [ ] API端点

### Phase 3: Monitor Dashboard（Day 2-3）
- [ ] 实现班级总览Tool
- [ ] 实现学生详情Tool
- [ ] 实现Agent日志Tool
- [ ] API端点

### Phase 4: Intervene Console（Day 3-4）
- [ ] 实现escalation查询Tool（读取pending_escalations）
- [ ] 实现响应Tool → teacher_escalation_responses
- [ ] 实现消息发送Tool → teacher_student_messages
- [ ] API端点

### Phase 5: Config Manager（Day 4）
- [ ] 实现配置读写Tool → teacher_configurations
- [ ] API端点

### Phase 6: LessonPlan Generator（Day 5-6）
- [ ] 实现AI教案生成Tool → teacher_lesson_plans
- [ ] 实现PPT生成Tool → generated_ppts + output/文件
- [ ] 实现状态查询Tool
- [ ] API端点

### Phase 7: 集成测试（Day 7）
- [ ] 端到端测试
- [ ] 与Agent协作测试
- [ ] 权限测试

---

## 八、关键决策确认

| # | 决策项 | 选择 |
|---|--------|------|
| 1 | 教案存储 | A. 新namespace `teacher_lesson_plans` |
| 2 | PPT文件存储 | B. 项目目录 `output/` |
| 3 | 预览图片 | B. 预生成缓存 |
| 4 | 学生端可见性 | C. 学生可见完整教案 |
| 5 | 实时通知 | A. MVP用轮询 |

---

*计划制定时间: 2024*
*版本: 教师端 MVP*
*分支: teacher*
