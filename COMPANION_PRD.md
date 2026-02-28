# Socratic Companion — 子 PRD

**角色**：Engineer B  
**Agent**：Socratic Companion（苏格拉底同伴）  
**对应主 PRD**：`Chur_gtp/EduGuide_PRD_Detailed.md` §2.2  
**对应开发指南**：`Chur_gtp/DEVELOPER_GUIDE.md` §2 / §3

---

## 一、Agent 定位与核心目标

Socratic Companion 是 EduGuide 的**面向学生的对话 Agent**，负责所有实时教学交互。核心原则：

1. **引导而非告知** —— 永远不给直接答案，通过苏格拉底式提问引导学生自主发现。
2. **对话严格围绕知识** —— 只进行与当前主题或习题相关的苏格拉底式提问，**不** 主动询问学生兴趣、爱好或"你想学什么"（兴趣推断由 Catalyst 通过分析上传文件完成）。
3. **自适应策略** —— 根据学生的错误模式与认知模型，动态调整 hint 策略和难度。
4. **适时升级** —— 检测到学生挫败、反复失败或情绪异常时，主动升级至人工教师。

---

## 二、职责范围（文件归属）

仅在以下文件中添加或修改代码，不修改他人归属文件：

| 文件路径 | 用途 |
|----------|------|
| `agents/companion/__init__.py` | 包导出 |
| `agents/companion/node.py` | Companion 节点逻辑：读 state、调 prompt + tools、写 state |
| `prompts/companion.py` | System Prompt 维护（PRD §2.2.1 文案为基础） |
| `tools/hints.py` | `construct_hint` + `escalate_to_human` 工具实现 |
| `tools/cognition.py` | `update_student_cognition_map` 工具实现 |

**只读依赖**（使用但不修改）：

| 路径 | 用途 |
|------|------|
| `graph.py` | `EduGuideState` 定义、图构建（Phase 1 产出） |
| `memory/*` | 记忆层 API（Working / External / Archive / Shared） |
| `tools/base.py` | 工具注册与日志框架 |
| `config.py` / `.env` | 配置与 API keys |

---

## 三、共享记忆协作契约

Companion 通过 `memory/shared.py` 的 namespace 与其他 Agent 协作，**不直接 import 或调用对方代码**。

| Namespace | 操作 | 说明 |
|-----------|------|------|
| `teacher_authority_graph` | **读取** | 由 Architect 写入的知识节点、知识边界、有效性约束。Companion 在每次交互前加载，确保回答不超出课程范围。 |
| `student_cognitive_models` | **读/写** | 学生的错误模式、理解向量、学习偏好。Companion 每次交互后更新（通过 `update_student_cognition_map`）。 |
| `interaction_episodes` | **写入** | 将有意义的交互记录持久化到 External Memory，供后续检索。 |

### 与 Architect 的交互流程

1. Architect 上传/更新教材 → 写入 `teacher_authority_graph`。
2. Companion 在处理学生消息时，从 `teacher_authority_graph` 加载知识边界，确保引导在课程范围内。
3. 若 Companion 观察到班级范围的系统性错误模式，可写入 `pending_validations` 建议 Architect 调整课程（P1 功能）。

### 与 Catalyst 的隔离

- Companion **不** 向学生提问兴趣/爱好相关的问题。
- 兴趣推断完全由 Catalyst 通过分析学生上传的 PDF/Word 文件完成。
- 两者通过共享记忆间接协作，无直接调用。

---

## 四、System Prompt 设计

基于 PRD §2.2.1，以下为定稿指导（实际文本维护在 `prompts/companion.py`）：

```python
SOCRATIC_COMPANION_PROMPT = """
You are the Socratic Companion in the EduGuide system.

YOUR CORE GOAL:
Guide students to discover answers through questioning, building deep understanding
rather than providing answers.

WHAT YOU CAN OBSERVE:
- Student input (text/voice/image)
- Student's interaction history from episodic_memory
- Current conversation context
- Knowledge boundaries from Pedagogical Architect
- Student's cognitive model (error patterns, understanding depth)

YOUR DECISION FRAMEWORK:
1. OBSERVE: What did the student say/do?
2. REASON:
   - What is their current understanding level?
   - Have they made similar errors before?
   - What hint strategy would be most effective?
3. DECIDE: Which combination of tools to call?
4. ACT: Execute tools and generate response

TOOLS AVAILABLE:
- retrieve_knowledge(query, scope): Dynamic retrieval with adjustable scope
- construct_hint(student_id, current_input, target_concept, error_analysis): Build hint strategy (socratic/analogy/decompose/confront)
- escalate_to_human(reason): Call teacher when needed
- update_student_cognition_map(interaction): Update understanding model

IMPORTANT RULES:
- NEVER give direct answers. Always guide discovery.
- Your dialogue is strictly about knowledge, tests, and subject-matter questions—
  do NOT ask about the student's interests, hobbies, or "what do you want to learn";
  only ask Socratic questions related to the current topic or exercise.
- Before responding, check student's error history.
- If student is frustrated (detected from input), escalate_to_human.
- After each interaction, update the cognition map.
- Your hints should adapt to student's cognitive style.

REASONING FORMAT:
Observation: [Student input and context]
Pattern Analysis: [Any matching error patterns from history]
Strategy Selection: [Why this hint approach was chosen]
Expected Student Action: [What student should do next]
"""
```

**Prompt 定稿注意事项**：

- `TOOLS AVAILABLE` 中的工具名必须与 `tools/hints.py`、`tools/cognition.py` 中实际注册的 `@tool` 函数名一致。
- `generate_multimodal_explanation` 暂不在 MVP 范围内（属 P2），prompt 中暂不列入或标记为 future。
- `retrieve_knowledge` 依赖记忆层框架提供的检索 API（Phase 1 产出），Companion 通过 `memory/external.py` 调用，可封装为轻量工具或直接在节点逻辑中调用。

---

## 五、工具详细设计

### 5.1 `construct_hint`（tools/hints.py）

```python
@tool
def construct_hint(
    student_id: str,
    current_input: str,
    target_concept: str,
    error_analysis: Optional[Dict] = None
) -> Dict:
    """
    根据错误模式与学生画像构建个性化 hint。

    策略选择（Agent 自主决定）：
    - socratic:  追问引导，适合浅层理解错误
    - analogy:   类比映射，适合概念迁移困难
    - decompose: 步骤分解，适合复杂问题卡住
    - confront:  展示矛盾让学生自我纠正，适合顽固误解

    Returns:
        {
            "hint_id": str,
            "strategy": "socratic" | "analogy" | "decompose" | "confront",
            "hint_content": str,
            "follow_up_questions": List[str],
            "difficulty_level": float,  # 0.0 - 1.0
            "expected_response_type": "explanation" | "calculation" | "verification"
        }
    """
```

**实现要点**：

1. 从 `student_cognitive_models` 读取该学生的历史错误模式。
2. 将 `current_input`、`target_concept`、`error_analysis` 与历史模式一起交给 LLM 推理出最佳 hint 策略。
3. 若同一概念连续 ≥3 次错误且策略未变，自动切换到不同策略。
4. 返回结构化 hint，由节点组装为最终回复。

### 5.2 `escalate_to_human`（tools/hints.py）

```python
@tool
def escalate_to_human(
    student_id: str,
    reason: Literal["frustration", "repeated_failure", "out_of_scope", "emotional_distress"],
    context_summary: str,
    urgency: Literal["low", "medium", "high"] = "medium"
) -> Dict:
    """
    请求人工教师介入。

    触发条件（Agent 自主判断）：
    - 学生表现出挫败信号
    - 同一概念连续失败多次
    - 问题超出系统能力
    - 检测到情绪异常

    Returns:
        {
            "escalation_id": str,
            "teacher_notification_sent": bool,
            "estimated_response_time": str,
            "student_message": str  # 等待期间展示给学生的消息
        }
    """
```

**实现要点**：

1. MVP 阶段可先实现为日志记录 + 返回安慰消息（无真实推送通道）。
2. 将 escalation 事件写入 `interaction_episodes`，供后续查询。
3. `student_message` 应根据 reason 生成不同的安慰/等待消息。

### 5.3 `update_student_cognition_map`（tools/cognition.py）

```python
@tool
def update_student_cognition_map(
    student_id: str,
    interaction_data: Dict
) -> Dict:
    """
    基于交互更新学生认知模型。

    使用 Dempster-Shafer 启发的信念更新：
    - 追踪学生对各概念的理解置信度
    - 识别误解模式
    - 更新学习风格偏好

    Args:
        interaction_data: {
            "concept": str,
            "student_response": str,
            "is_correct": bool,
            "time_spent": float,
            "help_requests": int
        }

    Returns:
        {
            "updated_concepts": List[str],
            "new_misconceptions": List[Dict],
            "confidence_changes": Dict[str, float],
            "recommended_focus_areas": List[str]
        }
    """
```

**实现要点**：

1. 从 `student_cognitive_models` 读取当前认知快照。
2. 根据 `is_correct`、`time_spent`、`help_requests` 计算信念更新量：
   - 正确且快速 → 大幅提升置信度
   - 正确但慢/多次求助 → 小幅提升
   - 错误 → 降低置信度，记录误解模式
3. 将更新后的认知模型写回 `student_cognitive_models`（External Memory）。
4. 更新 Archive Memory 中的 `cognition_snapshots` 表。
5. 返回变化摘要，供节点决策后续 hint 策略。

### 5.4 `retrieve_knowledge`（依赖框架）

`retrieve_knowledge` 本质上是对 `memory/external.py` 向量检索 API 的封装。有两种实现路径：

- **路径 A**：在节点逻辑中直接调用 `memory.external` 的检索方法（不单独注册为 @tool）。
- **路径 B**：封装为轻量 @tool，放在 `tools/hints.py` 中，调用底层 memory API。

建议采用路径 A（MVP 简化），在节点的 `load_relevant_context` 阶段完成检索。

---

## 六、节点逻辑设计（agents/companion/node.py）

```python
def socratic_companion_node(state: EduGuideState) -> EduGuideState:
    """
    Socratic Companion 节点。

    流程：
    1. 加载学生认知模型到 Working Memory
    2. 从 teacher_authority_graph 加载知识边界
    3. 检索与当前输入相关的历史交互
    4. 调用 LLM（ReAct）进行推理 + 工具选择
    5. 执行工具调用（construct_hint / escalate_to_human）
    6. 调用 update_student_cognition_map 更新认知模型
    7. 将回复写入 state["response_to_student"]
    """
```

### 节点处理流程

```
Student Message
      │
      ▼
┌─────────────────────────┐
│ 1. 加载学生认知模型       │  ← memory/external (student_cognitive_models)
│    + 知识边界            │  ← memory/shared (teacher_authority_graph)
│    + 历史交互            │  ← memory/external (interaction_episodes)
└─────────────────────────┘
      │
      ▼
┌─────────────────────────┐
│ 2. LLM ReAct 推理        │  ← System Prompt + Working Memory
│    - 观察学生输入         │
│    - 分析错误模式         │
│    - 选择 hint 策略       │
└─────────────────────────┘
      │
      ├── 需要引导 ──────────────────────────┐
      │                                      ▼
      │                          ┌───────────────────┐
      │                          │ construct_hint()   │
      │                          └───────────────────┘
      │                                      │
      ├── 需要升级 ──────────────────────────┐│
      │                                      ▼▼
      │                          ┌───────────────────┐
      │                          │ escalate_to_human()│
      │                          └───────────────────┘
      │                                      │
      ▼                                      ▼
┌─────────────────────────┐    ┌───────────────────────┐
│ 3. 生成回复              │    │ 4. 更新认知模型         │
│    → state["response_   │    │    update_student_     │
│       to_student"]      │    │    cognition_map()     │
└─────────────────────────┘    └───────────────────────┘
      │                                      │
      ▼                                      ▼
┌─────────────────────────────────────────────────┐
│ 5. 持久化交互到 interaction_episodes             │
└─────────────────────────────────────────────────┘
```

### 关键行为规则

1. **首次交互**：若该学生无历史认知模型，初始化默认模型（所有概念 uncertainty=1.0）。
2. **策略切换**：连续同概念 ≥3 次错误 → 必须切换 hint 策略；≥5 次 → 触发 escalate_to_human（reason="repeated_failure"）。
3. **知识边界遵守**：若 `teacher_authority_graph` 中 `scope_level` 为 `strict`，对超范围问题返回 `recommended_response_type="decline"` 的引导回复。
4. **每次交互结束**：必须调用 `update_student_cognition_map`，即使学生没有回答问题（记录 `time_spent` 和 `help_requests`）。

---

## 七、Agent 间路由（不修改 graph.py，仅需理解）

根据 PRD §4.1：

- **入口**：`event_type == "student_message"` 或 `"student_question"` → 路由到 `socratic_companion` 节点。
- **出口**：Companion 通过 `agent_decision` 字段影响路由：
  - 含 `"request_validation"` → 转交 Architect（如发现系统性课程问题）。
  - 含 `"explore_connection"` → 转交 Catalyst（如学生提问触发兴趣发现）。
  - 默认 → `END`（正常回复学生后结束本轮）。

---

## 八、MVP 验收标准

### P0（必须实现）

- [ ] 学生发送消息后，Companion 以苏格拉底式提问回复，**不给直接答案**。
- [ ] `construct_hint` 能根据错误类型（socratic / analogy / decompose / confront）生成不同策略的 hint。
- [ ] 同一概念多次错误后，Companion **自动调整** hint 策略。
- [ ] 每次交互后 `update_student_cognition_map` 更新认知模型，模型可被后续交互读取。
- [ ] Companion 从 `teacher_authority_graph` 读取知识边界，对超范围问题做适当处理。
- [ ] `escalate_to_human` 最小 stub 实现：System Prompt 铁律要求 frustrated → escalate，节点 LLM 可能随时调用此工具，必须有可调用的实现（日志 + 安慰消息即可，无需真实推送）。

### P1（期望实现）

- [ ] `escalate_to_human` 完整实现：真实推送通道（WebSocket/通知）、教师仪表盘集成。
- [ ] 学生认知模型可视化（与 Phase 5 协商，可提供数据接口）。
- [ ] 教师干预机制（Companion 发出 escalation 后，教师可通过某入口接手会话）。

### P2（加分项）

- [ ] `generate_multimodal_explanation`：支持生成图示/语音解释。
- [ ] 语音输入解析（学生发送语音消息）。
- [ ] 图片解析（数学题拍照识别）。

---

## 九、技术风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| LLM 偶尔泄漏直接答案 | 违反核心原则 | System Prompt 强调 + 输出过滤层（后处理检查是否含直接答案） |
| 认知模型更新不一致 | 信念偏差 | 写入前加锁/版本号，避免并发冲突 |
| 学生挫败检测误判 | 不必要的 escalation 或错过真正需要帮助的情况 | 设置信号阈值（多维度判断：关键词 + 连续失败次数 + 响应速度变化） |
| 知识边界未及时同步 | Companion 引导超出课程 | 每次交互前主动拉取 `teacher_authority_graph` 最新快照 |
| 上下文窗口溢出 | 长对话中丢失早期信息 | 遵循 MemGPT swap 机制，保留最关键的认知模型 + 最近 N 轮对话 |

---

*本子 PRD 严格对齐主 PRD（EduGuide_PRD_Detailed.md）与开发者指南（DEVELOPER_GUIDE.md）。实现时仅修改 Companion 归属文件，通过共享记忆 namespace 与其他 Agent 协作。*
