# EduGuide 教师端开发计划

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

## 三、Skills 详细设计

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
  - teacher_upload_material      # 上传教材
  - teacher_get_material_status  # 查询处理状态
  - teacher_adjust_boundary      # 调整知识边界
  - teacher_mark_importance      # 标记概念重要性
  - teacher_get_knowledge_graph  # 获取知识图谱
  - teacher_delete_material      # 删除教材
```

**对应 Tools** (`tools/material_manager.py`):

| Tool | 功能 | 写入Shared Memory | 权限 |
|------|------|------------------|------|
| `teacher_upload_material` | 上传PDF/DOCX/PPT | `teacher_uploads` | material_manage: create |
| `teacher_get_material_status` | 查询解析进度 | 读取 `teacher_uploads` | material_manage: read |
| `teacher_adjust_boundary` | 调整知识边界严格度 | `teacher_boundary_adjustments` | material_manage: update |
| `teacher_mark_importance` | 标记考点/难点 | `teacher_importance_marks` | material_manage: update |
| `teacher_get_knowledge_graph` | 获取可视化数据 | 读取 `teacher_authority_graph` | material_manage: read |
| `teacher_delete_material` | 删除教材及关联数据 | 清理多个namespace | material_manage: delete |

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

**文件**: `skills/monitor_dashboard/skill.yaml`

```yaml
name: monitor-dashboard
description: 教师查看班级总览、学生详情、Agent决策日志
entry:
  command: python
  args:
    - "{skill_path}/entry.py"
    - "{args}"

tools:
  - teacher_get_class_overview      # 班级总览
  - teacher_get_student_detail      # 学生详情
  - teacher_get_student_cognition   # 学生认知模型
  - teacher_view_agent_logs         # Agent决策日志
  - teacher_query_interaction_history # 查询交互历史
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

**文件**: `skills/intervene_console/skill.yaml`

```yaml
name: intervene-console
description: 教师响应escalation、发送消息、调整Agent策略
entry:
  command: python
  args:
    - "{skill_path}/entry.py"
    - "{args}"

tools:
  - teacher_get_escalations         # 获取待处理escalation列表
  - teacher_get_escalation_detail   # 获取单个escalation详情
  - teacher_respond_to_escalation   # 响应escalation
  - teacher_send_message            # 发送消息给学生
  - teacher_pause_companion         # 暂停/恢复Companion
  - teacher_get_conversations       # 获取对话列表
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

**文件**: `skills/config_manager/skill.yaml`

```yaml
name: config-manager
description: 教师配置班级参数、Agent行为偏好、通知设置
entry:
  command: python
  args:
    - "{skill_path}/entry.py"
    - "{args}"

tools:
  - teacher_get_config              # 获取当前配置
  - teacher_update_config           # 更新配置
  - teacher_get_class_config        # 获取班级特定配置
  - teacher_update_class_config     # 更新班级配置
  - teacher_configure_notifications # 配置通知
```

**配置数据结构**:

```python
class TeacherConfig(BaseModel):
    # Socratic Companion
    companion_strictness: Literal["gentle", "moderate", "strict"]
    companion_max_attempts: int  # 默认5次后escalate
    companion_emotion_detection: bool

    # Curiosity Catalyst
    catalyst_enabled: bool
    catalyst_push_frequency: Literal["daily", "weekly"]
    catalyst_max_daily_push: int
    catalyst_content_review: bool

    # Pedagogical Architect
    architect_default_boundary: Literal["strict", "moderate", "permissive"]
    architect_auto_expand: bool

    # Notifications
    notification_escalation_threshold: Literal["high", "medium", "any"]
    notification_delivery: List[Literal["in_app", "email", "push"]]
```

---

### Skill 5: LessonPlan Generator（AI教案与PPT）

**文件**: `skills/lesson_plan_generator/skill.yaml`

```yaml
name: lesson-plan-generator
description: AI辅助教案生成、PPT导出、预览管理
entry:
  command: python
  args:
    - "{skill_path}/entry.py"
    - "{args}"

tools:
  - generate_lesson_plan            # AI生成教案
  - get_lesson_plan                 # 获取教案详情
  - update_lesson_plan              # 更新教案
  - delete_lesson_plan              # 删除教案
  - generate_lesson_ppt             # 生成PPT
  - get_ppt_status                  # 查询PPT生成状态
  - get_ppt_download                # 获取下载链接
  - get_ppt_preview                 # 获取预览图片
  - list_lesson_plan_templates      # 获取教案模板列表
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

## 四、文件结构

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
├── templates/
│   ├── lesson_default.pptx
│   ├── lesson_minimal.pptx
│   └── lesson_colorful.pptx
│
└── output/
    ├── ppts/
    └── previews/
```

---

## 五、开发阶段

### Phase 1: 基础设施（Day 1）
- 创建Skills目录结构
- 扩展共享记忆命名空间
- 添加python-pptx依赖
- 创建输出目录

### Phase 2: Material Manager（Day 1-2）
- 实现上传Tool
- 实现状态查询Tool
- 实现边界调整Tool
- 实现重要性标记Tool
- API端点

### Phase 3: Monitor Dashboard（Day 2-3）
- 实现班级总览Tool
- 实现学生详情Tool
- 实现Agent日志Tool
- API端点

### Phase 4: Intervene Console（Day 3-4）
- 实现escalation查询Tool
- 实现响应Tool
- 实现消息发送Tool
- API端点

### Phase 5: Config Manager（Day 4）
- 实现配置读写Tool
- API端点

### Phase 6: LessonPlan Generator（Day 5-6）
- 实现AI教案生成Tool
- 实现PPT生成Tool
- 实现状态查询Tool
- API端点

### Phase 7: 集成测试（Day 7）
- 端到端测试
- 与Agent协作测试
- 权限测试

---

## 六、共享记忆层设计（符合DEVELOPER_GUIDE）

### 6.1 架构约束

根据DEVELOPER_GUIDE.md：
- `memory/*` 属于 **Phase 1 框架负责人** 管理范围
- 所有人**只读**，修改需框架负责人统一执行
- 新增namespace需添加到 `memory/shared.py` 的 `NAMESPACES` 字典
- 三层架构：working.py (Redis) → external.py (ChromaDB+PostgreSQL) → archive.py (文件系统)

### 6.2 现有Namespace（memory/shared.py已有）

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

### 6.3 需新增的Namespace（需框架负责人修改）

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

### 6.4 存储层分配

| 存储层 | 对应文件 | 存储内容 | 适用Namespace |
|--------|---------|---------|--------------|
| **Working** | `memory/working.py` | Redis高速缓存 | `pending_escalations`, `companion_control` |
| **External** | `memory/external.py` | ChromaDB+PostgreSQL | 大部分namespace（持久化数据） |
| **Archive** | `memory/archive.py` | 文件系统 | `teacher_audit_logs`, PPT实际文件 |

### 6.5 文件存储路径（Archive层）

| 资源类型 | 存储路径 | 生命周期 |
|---------|---------|---------|
| PPT文件 | `output/ppts/{ppt_id}.pptx` | 24小时后清理 |
| 预览图片 | `output/previews/{ppt_id}_{n}.png` | 随PPT一起清理 |
| 上传教材 | `uploads/materials/{material_id}/` | 永久保存 |
| 审计日志 | `logs/audit/{date}/teacher_{id}.log` | 永久归档 |

### 6.6 数据模型

#### teacher_lesson_plans（External Memory存储）

```python
{
    "plan_id": "plan_abc123",
    "teacher_id": "tch_001",
    "material_id": "mat_456",
    "class_id": "cls_301",

    "title": "十字相乘法因式分解",
    "grade": "中三",
    "subject": "数学",
    "duration": 45,

    "objectives": {
        "knowledge": "理解十字相乘法的原理...",
        "skills": "能够熟练运用十字相乘法...",
        "attitudes": "培养数学逻辑思维..."
    },

    "timeline": [
        {
            "phase": "导入",
            "duration": 5,
            "teacher_activities": ["复习已学知识...", "提出问题..."],
            "student_activities": ["回忆公式...", "思考回答..."],
            "design_intention": "建立新旧知识联系"
        }
    ],

    "ai_generated": True,
    "ai_model": "gpt-4o",
    "generated_at": "2024-01-15T10:30:00Z",
    "edited_by_teacher": False,
    "status": "active"
}
```

#### generated_ppts（External Memory存储，文件在Archive）

```python
{
    "ppt_id": "ppt_def456",
    "plan_id": "plan_abc123",
    "teacher_id": "tch_001",

    "file_name": "十字相乘法_教案.pptx",
    "file_path": "output/ppts/ppt_def456.pptx",  # Archive层实际文件
    "file_size_bytes": 1024000,

    "slide_count": 8,
    "preview_images": [
        "output/previews/ppt_def456_1.png"  # Archive层预览图
    ],

    "template_used": "default",
    "generated_at": "2024-01-15T10:35:00Z",
    "expires_at": "2024-01-16T10:35:00Z",
    "status": "completed",  # generating/completed/failed/expired
    "download_count": 0
}
```

### 6.7 与现有记忆系统的接口

所有Tools通过 `memory/shared.py` 提供的接口读写：

```python
from memory.shared import shared_memory

# 写入（External Memory）
shared_memory.write(
    namespace="teacher_lesson_plans",
    key=plan_id,
    value={...}
)

# 读取
entry = shared_memory.read(
    namespace="teacher_authority_graph",
    key=material_id
)

# 查询列表
entries = shared_memory.read_all(
    namespace="teacher_uploads",
    filter_dict={"teacher_id": "tch_001"},
    limit=10
)
```

---

## 七、关键决策确认

| # | 决策项 | 选择 |
|---|--------|------|
| 1 | 教案存储 | A. 新namespace `teacher_lesson_plans` |
| 2 | PPT文件存储 | B. 项目目录 `output/` |
| 3 | 预览图片 | B. 预生成缓存 |
| 4 | 学生端可见性 | C. 学生可见完整教案 |
| 5 | 实时通知 | A. MVP用轮询 |

---

## 八、文件归属与协作规范

根据DEVELOPER_GUIDE.md的归属表，教师端开发涉及：

### 8.1 教师端专属文件（新增）

| 归属 | 路径 | 说明 |
|------|------|------|
| **教师端开发** | `skills/*` | 5个Skill目录及实现 |
| **教师端开发** | `tools/material_manager.py` | 教材管理Tools |
| **教师端开发** | `tools/monitor_dashboard.py` | 监控Tools |
| **教师端开发** | `tools/intervene_console.py` | 干预Tools |
| **教师端开发** | `tools/config_manager.py` | 配置Tools |
| **教师端开发** | `tools/lesson_plan_generator.py` | 教案/PPT Tools |
| **教师端开发** | `app/api/v1/endpoints/*.py` | API端点实现 |
| **教师端开发** | `templates/*.pptx` | PPT模板文件 |
| **教师端开发** | `output/` | PPT输出目录 |

### 8.2 需协调的文件（框架负责人管理）

| 路径 | 修改内容 | 协调方式 |
|------|---------|---------|
| `memory/shared.py` | 新增4个namespace | 提交namespace列表给框架负责人统一修改 |
| `requirements.txt` | 添加python-pptx | 告知框架负责人依赖变更 |
| `.gitignore` | 添加output/目录 | 告知框架负责人 |

### 8.3 Namespace修改申请

提交给框架负责人的具体修改：

```python
# memory/shared.py 的 NAMESPACES 字典新增：

"teacher_configurations": "教师班级配置、Agent行为参数（External Memory）",
"teacher_importance_marks": "教师标记的概念重要性、教学建议（External Memory）",
"teacher_lesson_plans": "AI生成教案、教师编辑内容（External Memory）",
"generated_ppts": "PPT文件元数据、预览图路径（External Memory）",
```

---

## 九、验收标准

### 功能验收

| 功能 | 验收方式 |
|------|---------|
| 教材上传 | 上传PDF，返回material_id，3分钟后状态为completed |
| 知识图谱 | 上传后GET /knowledge-graph返回节点关系 |
| 班级总览 | GET /overview返回35个学生，7个需要关注 |
| Escalation | 模拟学生连续错误，教师端收到通知 |
| 消息发送 | 教师发送消息，学生端可见 |
| AI教案 | POST /generate返回完整教案结构 |
| PPT生成 | POST /ppt后，2分钟内可下载.pptx |

### 性能验收

| 指标 | 目标 |
|------|------|
| API响应时间 | < 200ms (不调用LLM的接口) |
| AI教案生成 | < 30秒 |
| PPT生成 | < 10秒 (含预览图) |
| 并发 | 支持10个教师同时操作 |

---

*计划制定时间: 2024*
*版本: 教师端 MVP*
*分支: teacher*
