# EduGuide 教师端详细实施文档 (PRD)
## 版本：Hack the East MVP - Teacher Interface
## 日期：2024

---

## 一、文档说明

### 1.1 定位
本文档定义**教师端**的功能、接口和交互设计，与《EduGuide 详细实施文档 (PRD)》中的Agent系统完全对接。

### 1.2 接口一致性声明
- 所有与Agent系统的交互通过**共享记忆空间**完成
- 教师端工具与Agent工具在同一Tool Ecosystem中注册
- 教师操作触发Agent观察-决策循环

---

## 二、教师端架构

### 2.1 系统定位

```
┌─────────────────────────────────────────────────────────────────┐
│                        教师端 (Teacher Interface)                │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐             │
│  │ 教材上传     │ │ 学生监控     │ │ 干预控制台   │             │
│  │ 与管理       │ │ 仪表板       │ │              │             │
│  └──────────────┘ └──────────────┘ └──────────────┘             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼ 读写共享记忆
┌─────────────────────────────────────────────────────────────────┐
│                      Shared Memory Space                        │
│  ┌──────────────────┐  ┌──────────────────┐                     │
│  │ Teacher Actions  │  │ Agent Observations│                    │
│  │ (教师操作日志)    │  │ (Agent读取触发决策)│                   │
│  └──────────────────┘  └──────────────────┘                     │
├─────────────────────────────────────────────────────────────────┤
│  Teacher's Authority Graph  │  Pending Escalations              │
│  (知识权威图谱)              │  (待处理的学生求助)                │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │
    ┌─────────────────────────┼─────────────────────────┐
    │                         │                         │
    ▼                         ▼                         ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Pedagogical     │    │ Socratic        │    │ Curiosity       │
│ Architect       │◄──►│ Companion       │◄──►│ Catalyst        │
│                 │      │                 │      │                 │
│ 接收教师上传    │      │ 请求教师干预    │      │ 查询教师授权    │
│ 维护知识边界    │      │ 报告学生状态    │      │ 确认内容安全    │
└─────────────────┘      └─────────────────┘      └─────────────────┘
```

### 2.2 核心设计原则

1. **观察而非控制**: 教师观察Agent决策，而非直接控制流程
2. **干预而非替代**: 教师在必要时干预，而非替代Agent工作
3. **透明可见**: Agent的所有决策对教师可见、可审计
4. **异步协作**: 教师不必实时在线，Agent会累积待处理事项

---

## 三、功能模块

### 模块1: 教材上传与管理

#### 3.1.1 功能描述
教师上传教学材料，Pedagogical Architect自动解析并建立知识权威图谱。

#### 3.1.2 用户界面

**上传界面**:
```
┌─────────────────────────────────────────────────────┐
│  📚 教材上传                                         │
├─────────────────────────────────────────────────────┤
│                                                     │
│  [拖放文件到这里] 或 [点击选择]                      │
│                                                     │
│  支持的格式: PDF, DOCX, PPT, TXT, Markdown          │
│                                                     │
├─────────────────────────────────────────────────────┤
│  教材信息:                                           │
│  ┌───────────────────────────────────────────────┐  │
│  │ 教材名称: [中三數學_因式分解.pdf    ]         │  │
│  │                                               │  │
│  │ 适用年级: [中三 ▼]  科目: [数学 ▼]           │  │
│  │                                               │  │
│  │ 章节标签: [因式分解] [十字相乘法] [公式法]   │  │
│  │                                               │  │
│  │ 难度级别: [基础 ●────○○○○ 进阶]              │  │
│  │                                               │  │
│  │ 知识边界严格度: [严格 ▼]                      │  │
│  │    严格: 只允许教材内内容                      │
│  │    适中: 教材为主，适度扩展                    │
│  │    宽松: 鼓励探索性学习                        │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│              [取消]        [开始处理 ▶]             │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**处理进度界面**:
```
┌─────────────────────────────────────────────────────┐
│  正在处理: 中三數學_因式分解.pdf                     │
│  [████████████████████░░░░░░░░░░] 65%               │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Pedagogical Architect 处理日志:                    │
│  ┌───────────────────────────────────────────────┐  │
│  │ ✅ 01:23:45 - 文件解析完成                      │  │
│  │ ✅ 01:23:52 - 识别章节结构: 提取公因式,        │  │
│  │               十字相乘法, 公式法               │  │
│  │ 🔄 01:24:10 - 建立知识节点关系...              │  │
│  │ ⏳ 01:24:15 - 生成评估策略...                  │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  预计完成: 2分钟                                    │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**完成后的知识图谱可视化**:
```
┌─────────────────────────────────────────────────────┐
│  📊 知识图谱: 中三數學_因式分解                      │
├─────────────────────────────────────────────────────┤
│                                                     │
│                    [因式分解]                        │
│                   (核心概念)                         │
│                        │                            │
│        ┌───────────────┼───────────────┐           │
│        ▼               ▼               ▼           │
│  [提取公因式]    [十字相乘法]    [公式法]          │
│  (基础)          (进阶)          (高级)            │
│        │               │               │           │
│        ▼               ▼               ▼           │
│   [例题3道]      [例题5道]      [例题2道]          │
│   [练习2道]      [常见错误]     [综合应用]         │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │ 📋 已识别常见错误模式:                        │   │
│  │    • 符号错误 (错误率预估: 35%)               │   │
│  │    • 数字选择错误 (错误率预估: 25%)           │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  [编辑图谱]  [添加例题]  [设置边界]  [完成]         │
│                                                     │
└─────────────────────────────────────────────────────┘
```

#### 3.1.3 后端接口

**工具: `teacher_upload_material`**

```python
@tool
def teacher_upload_material(
    file_path: str,
    metadata: TeacherUploadMetadata
) -> Dict:
    """
    教师上传教材，触发Pedagogical Architect处理。

    此工具由教师端调用，写入共享记忆，
    Architect观察后启动ingest_material流程。

    Args:
        file_path: 上传文件的路径
        metadata: {
            "material_name": str,
            "grade_level": str,  # "中三", "高一"等
            "subject": str,
            "chapter_tags": List[str],
            "difficulty_level": float,  # 0.0 - 1.0
            "boundary_strictness": "strict" | "moderate" | "permissive",
            "expected_duration_minutes": int,  # 预计学完时间
            "prerequisite_materials": List[str],  # 前置教材ID
            "teacher_notes": str  # 教师备注
        }

    Returns:
        {
            "upload_id": str,
            "processing_status": "queued" | "processing" | "completed" | "failed",
            "architect_task_id": str,  # Architect处理任务ID
            "estimated_processing_time": int,  # 秒
            "material_id": str  # 完成后分配的ID
        }
    """
    # 1. 验证文件格式和大小
    # 2. 保存到存储
    # 3. 写入共享记忆: namespace="teacher_uploads"
    # 4. Pedagogical Architect观察到新上传，启动处理
    pass
```

**共享记忆写入**:

```python
shared_memory.write(
    namespace="teacher_uploads",
    key=f"upload_{upload_id}",
    value={
        "teacher_id": teacher_id,
        "file_path": file_path,
        "metadata": metadata,
        "status": "pending_architect",
        "uploaded_at": datetime.now().isoformat(),
        "observed_by_architect": False  # Architect处理后置为True
    }
)
```

**Architect观察触发**:

```python
# Pedagogical Architect定期观察namespace
def architect_observe_uploads():
    pending_uploads = shared_memory.read_all(
        namespace="teacher_uploads",
        filter={"status": "pending_architect", "observed_by_architect": False}
    )

    for upload in pending_uploads:
        # Agent决策: 是否立即处理？优先级如何？
        decision = architect.decide_process_priority(upload)

        if decision.should_process_now:
            architect.call_tool("ingest_material", {
                "file_path": upload["file_path"],
                "source_type": "teacher_upload",
                "auto_chunk": True
            })

            # 标记为已观察
            shared_memory.update(
                namespace="teacher_uploads",
                key=upload["key"],
                value={"observed_by_architect": True, "processing_started": True}
            )
```

#### 3.1.4 教师可以进行的干预

**1. 调整知识边界**

```python
@tool
def teacher_adjust_knowledge_boundary(
    material_id: str,
    concept_id: str,
    boundary_adjustment: BoundaryAdjustment
) -> Dict:
    """
    教师手动调整某个知识点的边界严格度。

    场景: Architect自动判断某概念属于"严格"范围，
    但教师希望允许学生适度探索相关内容。

    Args:
        material_id: 教材ID
        concept_id: 概念ID
        boundary_adjustment: {
            "strictness": "strict" | "moderate" | "permissive",
            "reason": str,  # 教师调整原因
            "allowed_extensions": List[str],  # 允许的相关主题
            "forbidden_topics": List[str]  # 明确禁止的主题
        }

    Returns:
        {
            "adjustment_id": str,
            "applied": bool,
            "affected_queries": int  # 有多少历史查询会受影响
        }
    """
    # 写入共享记忆，Architect读取后更新知识边界
    shared_memory.write(
        namespace="teacher_boundary_adjustments",
        key=f"adjustment_{adjustment_id}",
        value={
            "material_id": material_id,
            "concept_id": concept_id,
            "adjustment": boundary_adjustment,
            "applied_by_architect": False,
            "timestamp": now()
        }
    )
```

**2. 标记重点/难点**

```python
@tool
def teacher_mark_concept_importance(
    material_id: str,
    concept_id: str,
    importance_mark: ImportanceMark
) -> Dict:
    """
    教师标记某个概念的重要性，影响Agent的教学策略。

    Args:
        importance_mark: {
            "level": "critical" | "important" | "optional",
            "exam_weight": float,  # 考试分值预估
            "common_misconceptions": List[str],  # 教师预知的常见错误
            "teaching_tips": str  # 教学建议
        }

    Returns:
        {
            "mark_id": str,
            "companion_notified": bool  # Socratic Companion是否已读取
        }
    """
    # Companion会读取此标记，调整提示策略
    pass
```

---

### 模块2: 学生监控仪表板

#### 3.2.1 功能描述
教师实时查看全班学生的学习状态、Agent决策日志、需要关注的学生。

#### 3.2.2 用户界面

**班级总览**:
```
┌─────────────────────────────────────────────────────────────────────┐
│  📊 班级总览 - 中三(2)班 - 数学: 因式分解                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │
│  │   👥 总人数     │  │   🟢 学习顺利   │  │   🔴 需要关注   │     │
│  │      35         │  │      28 (80%)   │  │      7 (20%)    │     │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘     │
│                                                                     │
│  实时活动 (过去30分钟):                                              │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ 小明 - 03:45 正在练习十字相乘法 [Companion引导中] 🟢          │ │
│  │ 小红 - 03:42 连续出错3次 [已调整策略] 🟡                       │ │
│  │ 小华 - 03:38 完成练习 [正确率85%] 🟢                          │ │
│  │ 小李 - 03:35 请求帮助 [等待教师] 🔴                           │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  需要教师介入的学生:                                                 │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ 🔴 小李 - 连续5次错误，情绪低落 [点击介入]                     │ │
│  │ 🟡 小王 - 对概念理解有偏差 [查看详情]                         │ │
│  │ 🟡 小张 - 长时间无进展 [发送提醒]                             │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**单个学生详情**:
```
┌─────────────────────────────────────────────────────────────────────┐
│  👤 学生详情: 小明                                                   │
│  [返回班级总览]  [上一人] [下一人]                                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 📈 学习进度                                                  │   │
│  │                                                              │   │
│  │ 提取公因式    [████████████████░░░░] 80% ✅ 已掌握          │   │
│  │ 十字相乘法    [████████████░░░░░░░░] 60% 🔄 学习中          │   │
│  │ 公式法        [████░░░░░░░░░░░░░░░░] 20% ⏳ 未开始          │   │
│  │                                                              │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 🧠 认知模型 (由Socratic Companion维护)                       │   │
│  │                                                              │   │
│  │ 理解深度: 中等 (置信度: 0.65)                                │   │
│  │ 学习风格: 偏好通过验证自我发现                                │   │
│  │                                                              │   │
│  │ 常见错误模式:                                                │   │
│  │  • 符号错误 (发生2次，已纠正) ⚠️                             │   │
│  │  • 数字选择 (发生1次)                                        │   │
│  │                                                              │   │
│  │ 学习偏好: 喜欢具体例子 → 抽象概念                            │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 💬 最近对话 (可查看完整历史)                                  │   │
│  │                                                              │   │
│  │ Companion: "如果展开(x-2)(x-3)，中间项是多少？"              │   │
│  │ 小明: "是-5x... 啊我知道了！应该是(x-2)(x-3)"               │   │
│  │ Companion: "很好！自己发现错误了。现在验证一下。"            │   │
│  │                                                              │   │
│  │ [查看完整对话] [Companion策略说明]                           │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  教师操作: [发送消息] [调整难度] [标记关注] [请求面谈]              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

#### 3.2.3 后端接口

**查询学生状态**:

```python
@tool
def teacher_query_student_status(
    teacher_id: str,
    student_id: Optional[str] = None,
    class_id: Optional[str] = None,
    query_type: Literal["overview", "detailed", "alert_only"] = "overview"
) -> Dict:
    """
    教师查询学生状态，系统从共享记忆中聚合数据。

    数据来源:
    - Student Cognitive Model (Socratic Companion维护)
    - Interaction History (所有Agent写入)
    - Pending Escalations (需要教师关注)

    Args:
        student_id: 查询单个学生，为None则查全班
        class_id: 班级ID
        query_type: 查询详细程度

    Returns:
        {
            "students": [
                {
                    "student_id": str,
                    "name": str,
                    "overall_progress": float,
                    "current_topic": str,
                    "companion_assessment": {
                        "understanding_depth": float,
                        "confidence_level": float,
                        "error_patterns": List[ErrorPattern],
                        "learning_style": str
                    },
                    "recent_activity": List[ActivityLog],
                    "needs_attention": bool,
                    "attention_reason": Optional[str],
                    "last_companion_interaction": datetime
                }
            ],
            "class_statistics": {
                "total_students": int,
                "avg_progress": float,
                "students_needing_attention": int,
                "common_difficulties": List[str]
            }
        }
    """
    # 从共享记忆中读取聚合数据
    pass
```

**读取Agent决策日志**:

```python
@tool
def teacher_view_agent_reasoning(
    student_id: str,
    interaction_id: Optional[str] = None,
    time_range: Optional[TimeRange] = None
) -> List[AgentDecisionLog]:
    """
    查看Agent的完整决策过程（可解释性）。

    返回数据包括:
    - Agent的Observation（观察到了什么）
    - Agent的Reasoning（如何推理）
    - Agent的Decision（决定调用什么工具）
    - Tool Execution（工具执行结果）

    这展示了"Agent为什么这样做"。
    """
    # 从Interaction History中读取
    logs = shared_memory.read_all(
        namespace="interaction_episodes",
        filter={"student_id": student_id},
        time_range=time_range
    )

    return [
        {
            "timestamp": log["timestamp"],
            "agent_id": log["agent_id"],
            "observation": log["reasoning_chain"]["observation"],
            "analysis": log["reasoning_chain"]["analysis"],
            "decision": log["reasoning_chain"]["decision"],
            "tools_called": log["tools_called"],
            "output": log["output"]
        }
        for log in logs
    ]
```

---

### 模块3: 干预控制台

#### 3.3.1 功能描述
教师在必要时介入，包括：回应escalation、调整Agent策略、发送直接消息。

#### 3.3.2 Escalation处理流程

**Escalation产生** (Socratic Companion触发):
```python
# Socratic Companion决定escalate
escalate_to_human(
    student_id="xiaoming_123",
    reason="repeated_failure",
    context_summary="连续5次十字相乘错误，检测到挫败情绪",
    urgency="high"
)

# 写入共享记忆
shared_memory.write(
    namespace="pending_escalations",
    key=f"escalation_{escalation_id}",
    value={
        "student_id": "xiaoming_123",
        "escalated_by": "socratic_companion",
        "reason": "repeated_failure",
        "context": context_summary,
        "urgency": "high",
        "status": "pending_teacher",  # pending_teacher | teacher_viewed | resolved
        "created_at": now(),
        "student_context": {  # Companion提供的完整上下文
            "current_topic": "十字相乘法",
            "error_count": 5,
            "error_history": [...],
            "cognitive_state": {...},
            "conversation_history": [...]
        }
    }
)
```

**教师接收通知**:
```
┌─────────────────────────────────────────────────────────────────┐
│  🔔 紧急: 学生小李需要您的帮助                                      │
│     (来自 Socratic Companion)                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  学生: 小李 (中三2班)                                             │
│  问题: 连续5次在十字相乘练习中出错，检测到挫败情绪                  │
│  时间: 3分钟前                                                    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Companion提供的上下文:                                       ││
│  │ • 当前练习: x²+7x+12 的因式分解                              ││
│  │ • 学生尝试: (x+3)(x+4), (x+2)(x+6), (x+1)(x+12)...          ││
│  │ • 错误模式: 能正确找数字，但和验证步骤出错                    ││
│  │ • 情绪指标: 输入速度变慢，出现"又错了..."等表达               ││
│  │ • Companion已尝试策略: 直接纠正 → 引导验证 → 分解步骤        ││
│  │ • 建议: 可能需要基础概念复习或换教学方式                      ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  [立即介入]  [查看完整对话]  [发送鼓励消息]  [暂时忽略]            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**教师介入选项**:

```python
@tool
def teacher_respond_to_escalation(
    escalation_id: str,
    response_type: Literal["take_over", "guide_companion", "message_student", "ignore"],
    response_content: TeacherResponse
) -> Dict:
    """
    教师回应escalation请求。

    Args:
        response_type:
            - "take_over": 教师接管，暂停Companion
            - "guide_companion": 教师指导Companion调整策略
            - "message_student": 教师发送消息，Companion继续
            - "ignore": 忽略，Companion自行继续

        response_content: {
            "message": str,  # 给学生的消息（如果是take_over或message）
            "strategy_adjustment": {  # 指导Companion（如果是guide_companion）
                "new_approach": str,
                "focus_concept": str,
                "suggested_activity": str
            },
            "estimated_duration": int,  # 预计干预时间（分钟）
            "follow_up_required": bool  # 是否需要后续跟进
        }

    Returns:
        {
            "status": "resolved" | "transferred_to_teacher" | "companion_adjusted",
            "student_notified": bool,
            "companion_notified": bool
        }
    """
    # 写入共享记忆
    shared_memory.write(
        namespace="teacher_escalation_responses",
        key=f"response_{escalation_id}",
        value={
            "escalation_id": escalation_id,
            "response_type": response_type,
            "response_content": response_content,
            "responded_at": now()
        }
    )

    # 触发相应Agent观察
    if response_type == "take_over":
        # 通知Companion暂停
        shared_memory.write(
            namespace="companion_control",
            key=f"pause_{student_id}",
            value={"paused_by_teacher": True, "until": None}
        )
    elif response_type == "guide_companion":
        # Companion读取strategy_adjustment后调整
        pass

    return {"status": "resolved", "student_notified": True}
```

#### 3.3.3 实时消息沟通

**教师发送消息**:
```python
@tool
def teacher_send_message(
    teacher_id: str,
    student_id: str,
    message: str,
    message_type: Literal["direct", "hint", "encouragement", "alert"] = "direct",
    companion_visibility: Literal["hidden", "visible", "collaborative"] = "collaborative"
) -> Dict:
    """
    教师直接向学生发送消息。

    companion_visibility:
        - "hidden": Companion看不到此消息，独立并行
        - "visible": Companion可见，但不参与
        - "collaborative": Companion可见，可协助后续对话

    消息写入共享记忆，学生端显示。
    """
    message_entry = {
        "message_id": generate_id(),
        "from": "teacher",
        "from_id": teacher_id,
        "to": student_id,
        "content": message,
        "message_type": message_type,
        "companion_visibility": companion_visibility,
        "timestamp": now(),
        "read": False
    }

    shared_memory.write(
        namespace="teacher_student_messages",
        key=message_entry["message_id"],
        value=message_entry
    )
```

**界面示例**:
```
┌─────────────────────────────────────────────────────────────────┐
│  💬 与小李的对话                                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 🤖 Companion (14:30): 试试展开(x-3)(x-4)验证一下?            ││
│  └─────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 👤 小李 (14:32): 我展开是x²-7x+12，但是原题是+7x...        ││
│  └─────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 🤖 Companion (14:33): 观察得很仔细!那应该换成什么符号呢...  ││
│  └─────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 🔴 System (14:35): Companion请求教师介入                      ││
│  └─────────────────────────────────────────────────────────────┘│
│  ┌──────────────────────────────────────────┐                   │
│  │ 👨‍🏫 我 (14:38): 小李，我看到你发现了符号 │                   │
│  │ 问题的关键。试着想想：如果两个负数相乘   │                   │
│  │ 得正数，但它们相加呢？                   │                   │
│  └──────────────────────────────────────────┘                   │
│                                                                  │
│  [输入消息...] [Companion协作模式 ▼] [发送]                       │
│                                                                  │
│  当前模式: 协作 - Companion会看到我发的消息并协助后续引导          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

### 模块4: 班级管理与配置

#### 3.4.1 功能描述
教师配置班级参数、Agent行为偏好、通知设置。

#### 3.4.2 配置界面

**Agent行为配置**:
```
┌─────────────────────────────────────────────────────────────────┐
│  ⚙️ Agent 行为配置 - 中三(2)班                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Socratic Companion 配置:                                         │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 引导严格度: [温和 ●───○○○] [中等 ○───○○○] [严格 ○───○○○]  ││
│  │                                                              ││
│  │    温和: 更多鼓励，更快给提示                                ││
│  │    中等: 平衡引导和挑战                                      ││
│  │    严格: 坚持让学生自己发现，延迟提示                        ││
│  │                                                              ││
│  │ 最大尝试次数: [5] 次后escalate给教师                        ││
│  │                                                              ││
│  │ 情绪检测: [✓] 启用 (检测到挫败时自动调整策略)                ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  Curiosity Catalyst 配置:                                         │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 主动推送: [✓] 启用                                          ││
│  │                                                              ││
│  │ 推送频率: [每天 ▼]                                          ││
│  │ 最大每日推送数: [3] 条                                       ││
│  │                                                              ││
│  │ 推送时机: [✓] 学生在线时  [✓] 课余时间                      ││
│  │                                                              ││
│  │ 内容审核: [✓] 需要Architect审核后才推送                     ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  Pedagogical Architect 配置:                                      │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 知识边界默认严格度: [严格 ▼]                                ││
│  │                                                              ││
│  │ 自动扩展知识: [ ] 允许 (当学生问超纲问题时)                  ││
│  │                                                              ││
│  │ 新教材处理: [自动处理 ▼]                                    ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│              [恢复默认]           [保存配置]                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**通知设置**:
```python
@tool
def teacher_configure_notifications(
    teacher_id: str,
    notification_settings: NotificationSettings
) -> Dict:
    """
    教师配置接收何种通知。

    Args:
        notification_settings: {
            "escalation_urgency_threshold": "high" | "medium" | "any",
            "class_overview_frequency": "daily" | "weekly" | "never",
            "student_milestones": bool,  # 学生达成里程碑时通知
            "agent_unusual_behavior": bool,  # Agent异常行为时通知
            "delivery_methods": ["in_app", "email", "push"],
            "quiet_hours": {  # 免打扰时段
                "start": "22:00",
                "end": "08:00"
            }
        }
    """
    pass
```

---

## 四、数据模型

### 4.1 教师相关实体

```python
class Teacher(BaseModel):
    teacher_id: str
    name: str
    email: str
    subjects: List[str]  # 教授的科目
    created_at: datetime

    # 配置
    default_companion_strictness: Literal["gentle", "moderate", "strict"]
    notification_settings: NotificationSettings

class Class(BaseModel):
    class_id: str
    teacher_id: str
    name: str  # "中三2班"
    grade: str  # "中三"
    subject: str
    students: List[str]  # student_ids

    # Agent配置（班级级别可覆盖教师默认）
    companion_config: CompanionConfig
    catalyst_config: CatalystConfig
    architect_config: ArchitectConfig

class MaterialUpload(BaseModel):
    upload_id: str
    teacher_id: str
    class_id: str
    material_id: str

    # 文件信息
    file_path: str
    file_name: str
    file_size: int

    # 元数据
    metadata: TeacherUploadMetadata

    # 处理状态
    status: "uploaded" | "processing" | "indexed" | "failed"
    processing_log: List[ProcessingLogEntry]

    # 知识图谱（Architect处理后生成）
    knowledge_graph: Optional[KnowledgeGraph]

class Escalation(BaseModel):
    escalation_id: str
    student_id: str
    class_id: str

    # Escalation信息
    escalated_by: str  # Agent ID
    reason: Literal["frustration", "repeated_failure", "out_of_scope", "emotional_distress"]
    urgency: Literal["low", "medium", "high"]
    context_summary: str

    # 完整上下文（用于教师了解详情）
    student_context: Dict  # Companion提供的认知状态、对话历史等

    # 状态
    status: "pending" | "viewed" | "responded" | "resolved"
    created_at: datetime
    resolved_at: Optional[datetime]

    # 教师响应
    teacher_response: Optional[TeacherResponse]
```

### 4.2 共享记忆命名空间

```python
# 教师操作相关
SHARED_MEMORY_NAMESPACES = {
    # 教师上传
    "teacher_uploads": "教师上传的教材，Architect观察",
    "teacher_boundary_adjustments": "教师手动调整的知识边界",
    "teacher_importance_marks": "教师标记的概念重要性",

    # 监控与查询
    "teacher_queries": "教师的查询请求日志",
    "teacher_viewed_students": "教师查看学生的记录",

    # Escalation
    "pending_escalations": "待教师处理的escalation",
    "teacher_escalation_responses": "教师对escalation的响应",

    # 消息
    "teacher_student_messages": "教师与学生的直接消息",
    "companion_control": "教师控制Companion的指令",

    # 配置
    "teacher_configurations": "教师的配置设置"
}
```

---

## 五、API端点设计

### 5.1 RESTful API

```python
# 教材管理
POST   /api/v1/teacher/materials/upload
GET    /api/v1/teacher/materials
GET    /api/v1/teacher/materials/{material_id}
PUT    /api/v1/teacher/materials/{material_id}/boundary
DELETE /api/v1/teacher/materials/{material_id}

# 学生监控
GET    /api/v1/teacher/classes/{class_id}/students
GET    /api/v1/teacher/students/{student_id}
GET    /api/v1/teacher/students/{student_id}/agent-logs
GET    /api/v1/teacher/students/{student_id}/cognition-model

# Escalation处理
GET    /api/v1/teacher/escalations
GET    /api/v1/teacher/escalations/{escalation_id}
POST   /api/v1/teacher/escalations/{escalation_id}/respond

# 消息
GET    /api/v1/teacher/messages
POST   /api/v1/teacher/messages/send
GET    /api/v1/teacher/messages/conversations/{student_id}

# 配置
GET    /api/v1/teacher/config
PUT    /api/v1/teacher/config
PUT    /api/v1/teacher/classes/{class_id}/config
```

### 5.2 WebSocket实时通知

```python
# WebSocket连接
ws://api/v1/teacher/realtime?teacher_id={teacher_id}

# 推送事件类型
EVENT_TYPES = {
    "escalation_new": "新的escalation需要处理",
    "escalation_resolved": "escalation已解决",
    "student_milestone": "学生达成学习里程碑",
    "material_processed": "教材处理完成",
    "companion_alert": "Companion检测到异常情况",
    "student_online": "学生上线",
    "new_message": "收到学生新消息"
}
```

---

## 六、与Agent系统的接口一致性验证

### 6.1 接口对照表

| 教师端操作 | 共享记忆写入 | Agent观察触发 | Agent工具 |
|-----------|-------------|--------------|-----------|
| 上传教材 | `teacher_uploads` | Architect观察 | `ingest_material` |
| 调整知识边界 | `teacher_boundary_adjustments` | Architect观察 | `establish_knowledge_boundary` |
| 标记重要性 | `teacher_importance_marks` | Companion读取 | 影响`construct_hint`策略 |
| 响应escalation | `teacher_escalation_responses` | Companion观察 | 影响后续交互 |
| 发送消息 | `teacher_student_messages` | Companion观察 | `companion_visibility`控制 |
| 暂停Companion | `companion_control` | Companion观察 | Companion暂停/恢复 |

### 6.2 数据流验证

**场景: 教师上传教材 → Architect处理 → 影响Companion行为**

```
1. 教师调用 teacher_upload_material()
   ↓
2. 写入 shared_memory["teacher_uploads"]
   ↓
3. Pedagogical Architect 观察到新上传
   ↓
4. Architect调用 ingest_material() 解析
   ↓
5. 更新 shared_memory["teacher_authority_graph"]
   ↓
6. Socratic Companion 后续查询时读取新知识边界
   ↓
7. Companion的回答现在基于新教材
```

**场景: Companion escalate → 教师响应 → Companion调整**

```
1. Companion调用 escalate_to_human()
   ↓
2. 写入 shared_memory["pending_escalations"]
   ↓
3. 教师通过WebSocket收到通知
   ↓
4. 教师调用 teacher_respond_to_escalation()
   ↓
5. 写入 shared_memory["teacher_escalation_responses"]
   ↓
6. Companion观察到教师响应
   ↓
7. Companion根据strategy_adjustment调整后续行为
```

---

## 七、安全与权限

### 7.1 教师权限模型

```python
TEACHER_PERMISSIONS = {
    "material_manage": ["create", "read", "update", "delete"],
    "student_view": ["read"],  # 只能看自己班级的学生
    "student_intervene": ["create", "update"],  # 介入和消息
    "class_config": ["read", "update"],
    "escalation_handle": ["read", "update"],
    "agent_logs_view": ["read"]  # 查看Agent决策日志
}
```

### 7.2 数据隔离

- 教师只能查看自己班级学生的数据
- 教师上传的教材默认仅自己班级可用
- Agent日志按班级隔离

---

## 八、实施优先级

### MVP (Hackathon)
- [ ] 教材上传界面 + 进度显示
- [ ] 班级总览仪表板
- [ ] Escalation通知 + 基础响应
- [ ] 学生详情查看

### Phase 2
- [ ] 完整的消息系统
- [ ] Agent决策日志可视化
- [ ] 知识图谱编辑
- [ ] 配置面板

### Phase 3
- [ ] 移动端适配
- [ ] 批量操作
- [ ] 数据分析报表
- [ ] 多班级管理

---

## 九、附录: Mock数据

### 9.1 示例教师

```json
{
  "teacher_id": "tch_001",
  "name": "李老师",
  "email": "li@school.edu.hk",
  "subjects": ["数学"],
  "classes": ["cls_301"]
}
```

### 9.2 示例班级

```json
{
  "class_id": "cls_301",
  "teacher_id": "tch_001",
  "name": "中三2班",
  "grade": "中三",
  "subject": "数学",
  "students": ["stu_001", "stu_002", "stu_003"],
  "companion_config": {
    "strictness": "moderate",
    "max_attempts": 5,
    "emotion_detection": true
  }
}
```

### 9.3 示例Escalation

```json
{
  "escalation_id": "esc_001",
  "student_id": "stu_001",
  "student_name": "小李",
  "escalated_by": "socratic_companion",
  "reason": "repeated_failure",
  "urgency": "high",
  "context_summary": "连续5次十字相乘错误，检测到挫败情绪",
  "created_at": "2024-01-15T14:35:00Z",
  "status": "pending"
}
```

---

**文档结束**

本文档完整定义了教师端的功能、接口和与Agent系统的集成方式，确保与《EduGuide 详细实施文档 (PRD)》中的Agent系统完全连通。
