# Catalyst 工程师工作清单

**职责范围**（仅修改以下归属）：  
`agents/catalyst/*`、`prompts/catalyst.py`、`tools/arxiv_monitor.py`、`tools/github_monitor.py`、`tools/briefing.py`  
不修改 `graph.py`、`memory/*`、其他 agent 或框架文件。

**协作契约**：  
- **写入** 共享记忆 `interest_signals`：根据学生上传的 PDF/Word 分析兴趣并写入。  
- **读取** 共享记忆 `interest_signals`：用于扩展监控域与个性化简报。  
- **写入** 共享记忆 `pending_validations`（待审核内容，由 Architect 审核后写回，Catalyst 再决定是否推送）。

---

## 一、按先后顺序的工作项

| 序号 | 工作项 | 重要程度 | 说明 |
|------|--------|----------|------|
| **1** | 完善并定稿 **`prompts/catalyst.py`** | 高 | 已有 PRD 文案；根据最终工具名与调用方式做一次对齐（如与 `arxiv_monitor` / `github_monitor` / `briefing` 命名一致），确保 TOOLS AVAILABLE 与 Reasoning 格式可直接指导节点实现。 |
| **2** | 实现 **`tools/arxiv_monitor.py`** | 高（P0） | 对接 arXiv API；按兴趣关键词/向量搜索近期论文；实现相关性计算（embedding 或关键词）；返回 monitor_id、论文列表、高相关数量等；接口需可被节点与定时任务调用。 |
| **3** | 实现 **`tools/briefing.py`** | 高（P0） | 实现 `synthesize_briefing`：根据事件（新论文/新仓库等）与 curriculum_context 生成个性化简报；返回是否应通知、个性化摘要、与课程的桥梁说明、建议动作等；与 PRD §2.3.2 一致。 |
| **4** | 实现 **`agents/catalyst/node.py`** 节点逻辑 | 高（P0） | 从 `prompts.catalyst` 加载 System Prompt；绑定并调用 `arxiv_monitor`、`github_monitor`、`briefing`；对学生上传的 PDF/Word 分析兴趣并写入 `interest_signals`；读 `interest_signals` 扩展监控与个性化简报；对 `new_content_detected` 做相关性判断；写 `pending_validations`（需审核时）；需要通知时写入 `state["notifications"]`。 |
| **5** | 实现 **主动推送/定时入口** | 高（P0） | 在节点或图外提供定时/事件驱动入口：轮询或接收“新内容”事件 → 调用监控工具 → 高相关内容经 `synthesize_briefing` 与（可选）Architect 审核流程后，将通知加入 `notifications` 或等价出口。 |
| **6** | 实现 **`tools/github_monitor.py`** | 中（P1） | 对接 GitHub API；按兴趣关键词搜索仓库；实现相关性评分；返回 monitor_id、仓库列表、高相关数量、推荐项目等；与 PRD §5.2 及 Phase 4 验收一致。 |
| **7** | 与共享记忆的集成与联调 | 中 | 在节点中正确使用 `memory.shared`：对学生上传文件做兴趣分析并写 `interest_signals`；读 `interest_signals` 扩展监控域与个性化；写 `pending_validations` 的 key/value 结构需与 Architect 约定一致；确认 Architect 审核写回后，Catalyst 能读取并决定是否推送。 |
| **8** | （可选）PRD 中的 **discover_connection** / **suggest_exploration_path** | 低 | PRD §2.3.2 有定义；DEVELOPER_GUIDE 未单独列文件。若做，可在 `briefing` 或节点内实现简化版，或后续单独小工具。 |

---

## 二、重要程度说明

- **高（P0）**：Phase 4 与 MVP 必须达成——arXiv 监控与相关性、个性化简报、高相关内容通知、节点可被图调用并写 pending_validations。
- **中（P1）**：Phase 4 期望——GitHub 监控、与共享记忆的完整读/写与联调。
- **低**：PRD 加分能力，时间允许再做。

---

## 三、验收标准（Phase 4）

- [ ] arXiv 可搜索并按兴趣计算相关性。  
- [ ] GitHub 可搜索相关仓库（P1）。  
- [ ] `synthesize_briefing` 能生成个性化简报。  
- [ ] 检测到高相关内容后能通知学生（主动推送/定时）。  
- [ ] 节点根据学生上传分析并写 `interest_signals`、读 `interest_signals`、写 `pending_validations`，与 Architect 审核流程衔接。

---

*仅工作清单，不包含具体实现；实现时请严格只改 Catalyst 归属文件并与框架/Architect/Companion 约定保持一致。*
