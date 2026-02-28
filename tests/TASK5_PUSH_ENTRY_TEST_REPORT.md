# 工作项 5「主动推送/定时入口」测试报告

**测试工程师视角**：从需求逻辑与代码文件细节验证是否完成工作项 5。  
**注意**：若测试触发图内自循环，立即停止并重新评估。

---

## 一、需求复述（CATALYST_WORKLIST 第 5 项）

在**节点或图外**提供**定时/事件驱动入口**：

1. **轮询或接收「新内容」事件**
2. → **调用监控工具**（arxiv_monitor / github_monitor）
3. → **高相关内容**经 `synthesize_briefing` 与（可选）Architect 审核
4. → 将**通知加入 `notifications` 或等价出口**

---

## 二、需求符合性检查

| 检查项 | 要求 | 实现情况 | 结论 |
|--------|------|----------|------|
| 定时/事件驱动入口 | 图外或独立入口：轮询或接收新内容事件 | **已实现**：`agents/catalyst/entry.run_new_content_check()` 单次执行；`POST /api/v1/push/trigger-new-content` 供定时/Webhook 调用 | ✅ 已实现 |
| 调用监控工具 | 由入口触发后调用 arxiv_monitor / github_monitor | 图外入口调用 `run_new_content_check` → 内部单次执行节点 → 调用 monitor 与 briefing | ✅ 已实现 |
| synthesize_briefing | 高相关内容经简报生成 | 节点内已调用 `synthesize_briefing`，且结果参与 `should_notify` 与 `notifications` | ✅ 已实现 |
| Architect 审核（可选） | 可选审核流程 | 节点写 `pending_validations`，由 Architect 审核写回；未在本次测试中验证跨 Agent 联调 | ✅ 已写 pending_validations |
| 通知出口 | 加入 `notifications` 或等价出口 | 节点内 `state["notifications"]` 追加 `curiosity_briefing`；`run_new_content_check` 返回的 `notifications` 即该出口 | ✅ 已实现 |

**小结**：**节点内链路**与**图外定时/事件驱动入口**均已实现；定时任务可调用 `run_new_content_check` 或 POST `/api/v1/push/trigger-new-content`。

---

## 三、代码路径与调用链（已实现部分）

- **事件路由**：`graph.py` 中 `event_type="new_content_detected"` → `route_by_event_type` → 进入 `curiosity_catalyst` 节点。
- **节点**：`agents/catalyst/node.py`  
  - 读 `interest_signals` → 调用 `monitor_arxiv_domain`、`monitor_github_domain` → 合并 `content_items` → `synthesize_briefing` → 写 `pending_validations` → 若 `should_notify` 则追加 `state["notifications"]`。
- **工具**：`tools/arxiv_monitor.py`、`tools/github_monitor.py`、`tools/briefing.py` 均被节点直接调用，接口可被「节点与定时任务」复用（当前仅节点在用）。

**图外入口**：`agents/catalyst/entry.run_new_content_check()` 构造 state 并单次调用节点；`app/api/v1/push.py` 提供 `POST /api/v1/push/trigger-new-content` 路由调用该函数。

---

## 四、死循环与自循环风险

- **图内 Catalyst 自循环**：`graph.py` 中从 `curiosity_catalyst` 出发的边由 `should_continue_monitoring(state)` 决定：  
  - `loop_count > 100` → `END`  
  - 否则 → 再次进入 `curiosity_catalyst`。  
  且节点内每次执行 `state["loop_count"] = state.get("loop_count", 0) + 1`，因此**最多执行 101 次**后到 END，**不会无限循环**。
- **单次新内容事件的语义**：对于一次「新内容」事件，期望应为「执行一次监控+简报+通知」。当前设计下，若通过图入口以 `new_content_detected` 触发，会重复进入 Catalyst 共 101 次（仅靠 `loop_count` 截断），属于**资源浪费**，建议后续改为：例如在单次事件场景下设置 `agent_decision` 或单独分支使一次执行后即到 END。
- **测试策略**：验证「监控 → 简报 → notifications」时，**仅单次调用节点**（不通过图多步执行），避免 101 次自循环；不编写会触发图内多轮 Catalyst 的自动化测试，防止长时间运行。

---

## 五、结论与建议

| 维度 | 结论 |
|------|------|
| **工作项 5 是否完整完成** | **是**。节点内「监控 → 简报 → 通知」与写 `pending_validations` 已实现；图外入口已实现：`run_new_content_check` + `POST /api/v1/push/trigger-new-content`。 |
| **死循环** | 图内 Catalyst 有 `loop_count > 100` 保护，不会无限循环；图外入口单次调用节点，不经过图，无自循环。 |
| **建议** | 可选：对单次新内容事件在图中增加「一次执行后即 END」的路径，避免经图触发时跑 101 次。 |

---

## 六、本次执行的验证测试

- 见 `tests/e2e/test_task5_push_entry.py`：  
  - 单次调用 `curiosity_catalyst_node`，断言 `current_agent`、`notifications`、`tools_to_call`、`loop_count`。  
  - 单次调用 `run_new_content_check`，断言返回含 `notifications`、`current_agent`、`tools_to_call`（含 monitor 与 briefing）。  
  - 不触发图的多次迭代，运行时间可控。
