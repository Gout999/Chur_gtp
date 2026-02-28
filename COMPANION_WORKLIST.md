# Companion 工程师工作清单

**职责范围**（仅修改以下归属）：  
`agents/companion/*`、`prompts/companion.py`、`tools/hints.py`、`tools/cognition.py`  
不修改 `graph.py`、`memory/*`、其他 agent 或框架文件。

**协作契约**：  
- **读取** 共享记忆 `teacher_authority_graph`：获取 Architect 写入的知识节点与知识边界，确保引导不超出课程范围。  
- **读/写** `student_cognitive_models`（External Memory）：每次交互前读取学生认知快照，交互后更新。  
- **写入** `interaction_episodes`（External Memory）：将有意义的交互持久化，供后续检索。

---

## 一、按先后顺序的工作项

| 序号 | 工作项 | 重要程度 | 说明 |
|------|--------|----------|------|
| **1** | 完善并定稿 **`prompts/companion.py`** | 高 | 已有 PRD §2.2.1 文案为基础；对齐实际工具名（`construct_hint`、`escalate_to_human`、`update_student_cognition_map`）；明确 TOOLS AVAILABLE 列表与 Reasoning 格式；确保"不给直接答案"和"不问兴趣"两条铁律写入 prompt。 |
| **2** | 实现 **`tools/cognition.py`** — `update_student_cognition_map` | 高（P0） | 从 External Memory 读取学生认知快照；根据 `is_correct`、`time_spent`、`help_requests` 计算信念更新（D-S 启发式）；识别新误解模式；写回 `student_cognitive_models` 与 Archive `cognition_snapshots`；返回变化摘要（updated_concepts、new_misconceptions、confidence_changes、recommended_focus_areas）。 |
| **3** | 实现 **`tools/hints.py`** — `construct_hint` | 高（P0） | 读取学生历史错误模式（依赖 cognition 数据）；将 `current_input`、`target_concept`、`error_analysis` 交 LLM 推理最佳 hint 策略（socratic / analogy / decompose / confront）；同概念连续 ≥3 次错误需自动切换策略；返回结构化 hint（hint_content、follow_up_questions、difficulty_level 等）。 |
| **4** | 实现 **`tools/hints.py`** — `escalate_to_human`（最小 stub） | 高（P0） | System Prompt 铁律要求"frustrated → escalate_to_human"，节点逻辑中 LLM 可能随时决定调用此工具，因此必须存在可调用的实现。MVP 阶段实现为最小 stub：日志记录 + 返回 student_message（安慰/等待消息）；将 escalation 事件写入 `interaction_episodes`；无需真实推送通道，后续可扩展。 |
| **5** | 实现 **`agents/companion/node.py`** 节点逻辑 | 高（P0） | 从 `prompts.companion` 加载 System Prompt；加载学生认知模型（memory/external）；从 `teacher_authority_graph`（memory/shared）读取知识边界；检索历史交互（memory/external `interaction_episodes`）；组装 Working Memory 传入 LLM ReAct 循环；根据推理结果调用 `construct_hint` 或 `escalate_to_human`；每次交互结束调用 `update_student_cognition_map`；将回复写入 `state["response_to_student"]`；将交互持久化到 `interaction_episodes`。 |
| **6** | 多轮对话策略调整逻辑 | 高（P0） | 在节点中实现策略切换规则：同概念连续 ≥3 次错误 → 切换 hint 策略；≥5 次 → 触发 `escalate_to_human(reason="repeated_failure")`；跟踪会话级别的连续错误计数（可放在 Working Memory 或 state 中）。 |
| **7** | ~~知识边界遵守逻辑~~ ✅ | 中（P0） | 每次交互前从 `teacher_authority_graph` 拉取最新知识边界；若学生提问超出 scope，根据 `scope_level`（strict / moderate / permissive）返回不同引导回复（bridge / decline）；确保不因边界未同步而引导超出课程范围。 |
| **8** | 与共享记忆的集成与联调 | 中 | 确认 `memory/shared.py` 的读写 API 用法正确；验证从 `teacher_authority_graph` 读取的 key/value 结构与 Architect 写入的一致；验证 `student_cognitive_models` 的读写与 Archive `cognition_snapshots` 的同步；首次交互时初始化默认认知模型（所有概念 uncertainty=1.0）。 |
| **9** | 多轮对话测试脚本 | 中 | 编写测试脚本模拟：单概念正确回答 → 确认 hint 消失；同概念多次错误 → 确认策略切换；≥5 次错误 → 确认 escalation 触发；超范围提问 → 确认边界拦截；验证认知模型在多轮后被正确更新。 |
| **10** | （可选）LLM 输出过滤层 | 低 | 在节点回复前增加后处理检查：检测回复中是否包含直接答案（关键词/模式匹配），若检测到则重新生成或截断，作为 System Prompt 的安全网。 |
| **11** | （可选）`generate_multimodal_explanation` | 低（P2） | PRD §2.2.1 提及的多模态解释（图示/语音），MVP 不要求。若时间允许可实现简化版文本 + Markdown 图示。 |

---

## 二、重要程度说明

- **高（P0）**：Phase 3 与 MVP 必须达成 —— 苏格拉底式引导（不给答案）、hint 按错误类型生成不同策略、同概念多次错误后策略调整、认知模型每次交互后更新、读取知识边界、`escalate_to_human` 最小 stub（prompt 铁律要求，节点必须能调用）。
- **中（P1）**：Phase 3 期望 —— 与共享记忆完整联调、测试脚本。
- **低（P2）**：PRD 加分能力，时间允许再做。

---

## 三、验收标准（Phase 3）

- [ ] 学生提问后 Companion 以苏格拉底式提问回复，**不给直接答案**。
- [ ] `construct_hint` 能根据错误类型生成不同策略的 hint（至少支持 socratic 和 decompose 两种）。
- [ ] 同一概念连续错误 ≥3 次后，Companion 自动切换 hint 策略。
- [ ] 每次交互后 `update_student_cognition_map` 更新认知模型并可被下一次交互读取。
- [ ] 从 `teacher_authority_graph` 读取知识边界，对超范围问题做 bridge 或 decline 处理。
- [ ] `escalate_to_human` 最小 stub 可在反复失败/挫败时被调用并返回安慰消息（P0）。
- [ ] 多轮对话测试脚本可跑通上述场景。

---

## 四、依赖与前置条件

| 依赖项 | 提供方 | 状态 |
|--------|--------|------|
| `EduGuideState` 定义与图构建 | Phase 1 / 框架负责人 | 须先完成 |
| `memory/*` 三层读写 API | Phase 1 / 框架负责人 | 须先完成 |
| `tools/base.py` 工具注册框架 | Phase 1 / 框架负责人 | 须先完成 |
| `teacher_authority_graph` 有数据 | 工程师 A（Architect） | 联调时需要 |
| `config.py` + LLM API key | Phase 1 / 框架负责人 | 须先完成 |

---

*仅工作清单，不包含具体实现；实现时请严格只改 Companion 归属文件并与框架/Architect/Catalyst 约定保持一致。*
