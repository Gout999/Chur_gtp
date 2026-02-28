# EduGuide Developer Guide

本文档说明 EduGuide 项目整体框架、目录约定、三人分工与提交规范，确保开发符合 PRD 逻辑且提交不产生混乱与冲突。

---

## 1. 总框架（符合 PRD）

EduGuide 采用 **Agent-Native** 架构：一个 LangGraph 图 + 共享记忆 + 工具生态，三个 Agent 作为图节点，通过 `EduGuideState` 与 Shared Memory 协作。

### 1.1 架构概览

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Shared Memory (memory/)                       │
├─────────────────────────────────────────────────────────────────────┤
│  teacher_authority_graph  │  student cognitive / interaction history │
│  interest_signals         │  pending_validations                     │
└─────────────────────────────────────────────────────────────────────┘
                              ▲ ▲ ▲
                              │ │ │
         ┌────────────────────┘ │ └────────────────────┐
         ▼                      ▼                      ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│ Architect       │   │ Companion       │   │ Catalyst        │
│ (agents/        │   │ (agents/         │   │ (agents/         │
│  architect/)    │   │  companion/)     │   │  catalyst/)     │
└─────────────────┘   └─────────────────┘   └─────────────────┘
         │                      │                      │
         └──────────────────────┼──────────────────────┘
                                ▼
                    ┌─────────────────────┐
                    │   tools/            │
                    │   base, ingest,     │
                    │   boundary, hints,  │
                    │   cognition,        │
                    │   arxiv_monitor,    │
                    │   github_monitor,   │
                    │   briefing          │
                    └─────────────────────┘
```

### 1.2 项目目录结构（PRD 命名约定）

```
EduGuide/
├── config.py                 # 配置加载（API keys、参数）
├── .env                      # 环境变量（不提交敏感信息，用 .env.example 模板）
├── .env.example              # 环境变量模板
├── graph.py                  # LangGraph 图：EduGuideState、建图、路由、仅 import 各 agent 节点
│
├── memory/                   # 记忆层：Working / External / Archive + 共享读写
│   ├── __init__.py
│   ├── working.py            # Working Memory
│   ├── external.py           # External Memory（向量检索）
│   ├── archive.py            # Archive（持久化）
│   └── shared.py             # 共享记忆读写与 namespace 约定
│
├── tools/                    # 工具生态
│   ├── __init__.py
│   ├── base.py               # 工具注册、调用、日志（Phase 1 基础框架）
│   ├── ingest.py             # Architect: ingest_material
│   ├── boundary.py           # Architect: establish_knowledge_boundary
│   ├── hints.py              # Companion: construct_hint
│   ├── cognition.py          # Companion: update_student_cognition_map
│   ├── arxiv_monitor.py      # Catalyst: arXiv 监控
│   ├── github_monitor.py     # Catalyst: GitHub 监控
│   └── briefing.py           # Catalyst: synthesize_briefing
│
├── prompts/                  # 各 Agent 的 System Prompt（PRD 约定）
│   ├── __init__.py
│   ├── architect.py          # Pedagogical Architect prompt
│   ├── companion.py          # Socratic Companion prompt
│   └── catalyst.py           # Curiosity Catalyst prompt
│
├── agents/                   # 各 Agent 节点实现（供 graph.py import）
│   ├── __init__.py
│   ├── architect/
│   │   ├── __init__.py
│   │   └── node.py           # pedagogical_architect_node(state) -> state
│   ├── companion/
│   │   ├── __init__.py
│   │   └── node.py           # socratic_companion_node(state) -> state
│   └── catalyst/
│       ├── __init__.py
│       └── node.py           # curiosity_catalyst_node(state) -> state
│
├── tests/
│   └── e2e/                  # 端到端测试
│
├── demo/                     # Hackathon 演示脚本
│
├── EduGuide_PRD_Detailed.md  # 产品与架构 PRD
└── DEVELOPER_GUIDE.md        # 本开发者说明
```

---

## 2. 三人小框架与文件归属

每位工程师**只在自己负责的目录/文件中添加或修改代码**，不修改他人负责的文件，从源头避免冲突。

### 2.1 归属表

| 归属 | 路径 | 说明 |
|------|------|------|
| **Phase 1 / 框架负责人** | `config.py`, `.env.example`, `graph.py`, `memory/*`, `tools/base.py` | 所有人只读；仅框架负责人在必要时修改 |
| **工程师 A（Architect）** | `agents/architect/*`, `prompts/architect.py`, `tools/ingest.py`, `tools/boundary.py` | Pedagogical Architect 全部逻辑 |
| **工程师 B（Companion）** | `agents/companion/*`, `prompts/companion.py`, `tools/hints.py`, `tools/cognition.py` | Socratic Companion 全部逻辑 |
| **工程师 C（Catalyst）** | `agents/catalyst/*`, `prompts/catalyst.py`, `tools/arxiv_monitor.py`, `tools/github_monitor.py`, `tools/briefing.py` | Curiosity Catalyst 全部逻辑 |
| **Phase 5 / 协商** | `tests/e2e/`, `demo/`, `README.md` | 集成阶段由一人整理或按场景拆分 |

### 2.2 各工程师工作区

- **工程师 A**  
  - 在 `agents/architect/node.py` 实现节点逻辑（读 state、调 prompt + tools、写 state、写共享记忆）。  
  - 在 `prompts/architect.py` 维护 System Prompt。  
  - 在 `tools/ingest.py`、`tools/boundary.py` 实现工具，并在节点中调用。

- **工程师 B**  
  - 在 `agents/companion/node.py` 实现节点逻辑。  
  - 在 `prompts/companion.py` 维护 System Prompt。  
  - 在 `tools/hints.py`、`tools/cognition.py` 实现工具。

- **工程师 C**  
  - 在 `agents/catalyst/node.py` 实现节点逻辑（含定时/推送入口）。  
  - 在 `prompts/catalyst.py` 维护 System Prompt。  
  - 在 `tools/arxiv_monitor.py`、`tools/github_monitor.py`、`tools/briefing.py` 实现工具。

---

## 3. 共享记忆 Namespace 约定（协作契约）

Agent 间仅通过 **memory/shared** 的 namespace 读写协作，不直接依赖对方代码。约定如下，实现与使用需遵守。

| Namespace | 写入方 | 读取方 | 用途 |
|-----------|--------|--------|------|
| `teacher_authority_graph` | Architect（tools/boundary.py、ingest 结果） | Companion | 知识边界、知识节点、约束 |
| `interest_signals` | Catalyst（学生上传 PDF/Word 分析得出兴趣） | Catalyst | 扩展监控域、个性化简报 |
| `pending_validations` | Catalyst（待审核内容） | Architect | 审核后写回，Catalyst 再决定是否推送 |

具体 key / value 结构见 `memory/shared.py` 的 docstring 或项目内 `docs/contracts.md`（若创建）。

---

## 4. graph.py 约定（避免冲突）

- `graph.py` 在 **Phase 1 定稿**：只包含 `EduGuideState` 定义、建图、路由逻辑，**不包含**任何 Agent 内部业务逻辑。
- 三个节点通过 **import** 引入：
  - `from agents.architect import pedagogical_architect_node`
  - `from agents.companion import socratic_companion_node`
  - `from agents.catalyst import curiosity_catalyst_node`
- 之后 A/B/C **不修改 graph.py**，只在自己目录下实现/修改 `agents/*/node.py` 及各自 tools、prompts。

---

## 5. 提交与分支建议

- **分支**：每人使用独立功能分支（如 `feature/architect`、`feature/companion`、`feature/catalyst`）。
- **提交范围**：只提交上表属于自己归属的文件；若需改 `graph.py` 或 `memory/`，提交前与框架负责人同步，由负责人统一改一次再合并。
- **合并顺序**：先合并 Phase 1 到 `main`，再按 A → B → C 合并各自分支；Phase 5 再合并 e2e/demo/README。

---

## 6. MVP 阶段与验收（与 PRD 对应）

| Phase | 负责 | 产出 | 验收标准 |
|-------|------|------|----------|
| Phase 1 | 框架负责人 | graph.py, memory/, tools/base.py, config, .env.example | 三节点可独立运行，记忆三层可读写，工具可注册与日志 |
| Phase 2 | 工程师 A | prompts/architect.py, tools/ingest.py, tools/boundary.py, agents/architect/ | 可生成推理链，PDF 解析为知识节点，知识边界可写且 Companion 可读 |
| Phase 3 | 工程师 B | prompts/companion.py, tools/hints.py, tools/cognition.py, agents/companion/ | 只引导不给答案，hint 按错误类型变化，cognition_map 更新，多轮策略调整 |
| Phase 4 | 工程师 C | prompts/catalyst.py, tools/arxiv_monitor.py, github_monitor.py, briefing.py, agents/catalyst/ | arXiv/GitHub 监控与相关性，个性化简报，高相关内容通知 |
| Phase 5 | 协商 | tests/e2e/, demo/, README.md | 端到端场景可跑通，Demo 可演示，文档可让他人部署 |

---

## 7. 参考

- 产品与架构细节：`EduGuide_PRD_Detailed.md`  
- 状态与图结构：PRD 第四章 LangGraph 图结构  
- 记忆与协作：PRD 第三章 MemGPT 风格记忆与 3.3 Agent 间协作机制  

开发者只需在**总框架下的各自小框架**内增加代码，并遵守上述归属与契约，即可保证提交清晰、无冲突。
