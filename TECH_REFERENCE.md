# EduGuide 技术参考（真实路径与版本）

> 本文档为 Catalyst 工作项（含主动推送/定时入口）及全项目开发提供**可核查**的技术基线。  
> 所有路径与配置均真实存在，无占位符。

---

## 一、技术栈版本

### 1.1 运行时

| 组件 | 版本约束 | 说明 |
|------|----------|------|
| Python | 3.11+ | PRD 约定；项目主语言 |
| 后端框架 | FastAPI ≥ 0.115.0 | `requirements.txt` |
|  ASGI 服务器 | Uvicorn[standard] ≥ 0.30.0 | `requirements.txt` |
| 图执行引擎 | LangGraph ≥ 0.2.0 | `requirements.txt` |
| LLM 客户端 | langchain-openai ≥ 0.1.0 | `requirements.txt` |

### 1.2 后端依赖（`requirements.txt`）

| 包名 | 版本约束 | 用途 |
|------|----------|------|
| arxiv | ≥ 2.0.0 | arXiv API 监控（Catalyst） |
| requests | ≥ 2.31.0 | HTTP 请求（含 MINIMAX 调用） |
| fastapi | ≥ 0.115.0 | Web API |
| uvicorn[standard] | ≥ 0.30.0 | 应用服务器 |
| langgraph | ≥ 0.2.0 | 状态图与节点编排 |
| langchain-openai | ≥ 0.1.0 | OpenAI 模型调用 |
| redis | ≥ 5.0.0 | 缓存/会话（可选） |
| sqlalchemy | ≥ 2.0.0 | ORM（可选） |
| python-dotenv | ≥ 1.0.0 | 环境变量加载 |
| pytest | ≥ 8.0.0 | 单元/集成测试 |

### 1.3 前端依赖（`frontend/package.json`）

| 包名 | 版本 | 用途 |
|------|------|------|
| axios | ^1.8.0 | HTTP 客户端 |
| socket.io-client | ^4.8.0 | WebSocket 客户端 |

---

## 二、关键文档路径

| 文档 | 绝对路径 | 说明 |
|------|----------|------|
| Catalyst 工作清单 | `c:\Chur_gtp\CATALYST_WORKLIST.md` | Catalyst 工程师任务与验收标准 |
| 开发者指南 | `c:\Chur_gtp\DEVELOPER_GUIDE.md` | 框架、目录约定、归属、共享记忆契约 |
| 产品与架构 PRD | `c:\Chur_gtp\EduGuide_PRD_Detailed.md` | 产品需求与 LangGraph 图结构 |
| 本技术参考 | `c:\Chur_gtp\TECH_REFERENCE.md` | 技术栈、路径、环境变量、依赖图 |
| Prompt 说明 | `c:\Chur_gtp\Prompt_Instructions.md` | 提示词设计说明 |
| 任务计划 | `c:\Chur_gtp\task_plan.md` | 任务规划 |
| E2E 测试说明 | `c:\Chur_gtp\tests\e2e\README.md` | 端到端测试说明 |
| Demo 说明 | `c:\Chur_gtp\demo\README.md` | 演示脚本说明 |

---

## 三、环境变量位置

### 3.1 文件路径

| 类型 | 路径 | 说明 |
|------|------|------|
| 模板 | `c:\Chur_gtp\.env.example` | 环境变量模板，可提交 |
| 运行时 | `c:\Chur_gtp\.env` | 实际配置，不提交（含敏感信息） |
| 加载逻辑 | `c:\Chur_gtp\config.py` | 通过 `load_dotenv()` 加载 `.env`，并导出 `SETTINGS` |

### 3.2 环境变量与 `config.py` 映射

| 变量名 | 用途 | 默认值（config.py） |
|--------|------|---------------------|
| OPENAI_API_KEY | OpenAI API 密钥 | `""` |
| ANTHROPIC_API_KEY | Anthropic API 密钥 | `""` |
| MINIMAX_API_KEY | MINIMAX API 密钥（Catalyst LLM） | `""` |
| MINIMAX_GROUP_ID | MINIMAX Group ID | `""` |
| DATABASE_URL | PostgreSQL 连接 | `postgresql://user:password@localhost:5432/eduguide` |
| REDIS_URL | Redis 连接 | `redis://localhost:6379/0` |
| CHROMA_HOST | Chroma 向量库主机 | `localhost` |
| CHROMA_PORT | Chroma 端口 | `8001` |
| APP_ENV | 运行环境 | `development` |
| LOG_LEVEL | 日志级别 | `INFO` |
| SECRET_KEY | 应用密钥 | `change-me` |
| GITHUB_TOKEN | GitHub API 令牌（GitHub 监控） | `""` |

---

## 四、项目依赖关系图

### 4.1 LangGraph 图结构（`graph.py`）

```
                    route_by_event_type (入口)
                                  │
          ┌───────────────────────┼───────────────────────┐
          ▼                       ▼                       ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│ Architect       │   │ Companion       │   │ Catalyst        │
│ pedagogical_    │   │ socratic_       │   │ curiosity_      │
│ architect_node  │   │ companion_node  │   │ catalyst_node   │
└────────┬────────┘   └────────┬────────┘   └────────┬────────┘
         │                      │                      │
         │    route_by_agent_decision / should_continue_monitoring
         └──────────────────────┼──────────────────────┘
                                ▼
                            END 或 下一节点
```

**事件路由**：`file_upload` → Architect；`student_message` / `student_question` / `escalation` → Companion；`new_content_detected` / `validation_request` → Architect。

### 4.2 Catalyst 归属模块与工具调用链

```
图外定时/事件驱动入口 (工作项 5)
  - agents/catalyst/entry.py → run_new_content_check()  单次执行，不经过图
  - POST /api/v1/push/trigger-new-content (app/api/v1/push.py)
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ agents/catalyst/node.py                                      │
│  - 读 prompts/catalyst.py (System Prompt)                    │
│  - 读 memory/shared.py → interest_signals                   │
│  - 写 memory/shared.py → pending_validations                │
│  - 写 state["notifications"]                                │
└─────────────────────────────────────────────────────────────┘
        │
        ├── tools/arxiv_monitor.py   → monitor_arxiv_domain
        ├── tools/github_monitor.py  → monitor_github_domain
        ├── tools/briefing.py       → synthesize_briefing
        └── agents/catalyst/llm.py  → MINIMAX LLM（兴趣提取、相关性、简报）
```

### 4.3 共享记忆 Namespace 与读写方（`memory/shared.py`）

| Namespace | 写入方 | 读取方 | 用途 |
|-----------|--------|--------|------|
| teacher_authority_graph | Architect | Companion | 知识边界、知识节点 |
| interest_signals | Catalyst | Catalyst | 学生兴趣（PDF/Word 分析）→ 监控与简报 |
| pending_validations | Catalyst | Architect | 待审核内容；Architect 审核后写回，Catalyst 再决定是否推送 |

### 4.4 Catalyst 文件归属（DEVELOPER_GUIDE 约定）

| 路径 | 归属 |
|------|------|
| `agents/catalyst/*` | Catalyst |
| `prompts/catalyst.py` | Catalyst |
| `tools/arxiv_monitor.py` | Catalyst |
| `tools/github_monitor.py` | Catalyst |
| `tools/briefing.py` | Catalyst |

**不修改**：`graph.py`、`memory/*`、其他 agent 或框架文件。

---

## 五、主动推送/定时入口（工作项 5）技术要点

- **图外入口（已实现）**：
  - **可调用函数**：`agents/catalyst/entry.run_new_content_check(student_id, interest_keywords=..., curriculum_context=...)`，单次执行节点，返回 `notifications`、`tools_to_call` 等；定时任务可直接 import 调用。
  - **HTTP 入口**：`POST /api/v1/push/trigger-new-content`，请求体 `{"student_id": "...", "interest_keywords": [...], "curriculum_context": {...}}`；定时任务或 Webhook 可周期 POST 此接口。
- **流程**：轮询或接收「新内容」事件 → 调用 `run_new_content_check` 或上述 API → 内部调用 `monitor_arxiv_domain` / `monitor_github_domain` → 高相关内容经 `synthesize_briefing` → 通知写入返回的 `notifications`（等价于 `state["notifications"]`）。
- **依赖**：`config.py`（API 密钥）、`memory/shared`（interest_signals、pending_validations）、`tools/arxiv_monitor.py`、`tools/briefing.py`、`tools/github_monitor.py`。
- **环境变量**：`OPENAI_API_KEY` / `MINIMAX_API_KEY` / `MINIMAX_GROUP_ID`、`GITHUB_TOKEN`（GitHub 监控）。

---

*文档生成时间：以仓库实际内容为准。*
