# EduGuide 开发实施文档
## Agent-Native Teaching System - 详细开发指南

**版本**: MVP 1.0
**日期**: 2024
**状态**: 实施阶段

---

## 文档结构

本文档为开发团队提供从环境搭建到代码实现的完整指导，包含：
1. 环境配置与依赖安装
2. 核心模块实现细节
3. Agent节点开发规范
4. 工具实现模板
5. 测试与部署流程

---

## 第一部分：环境配置

### 1.1 系统要求

| 组件 | 最低配置 | 推荐配置 |
|------|---------|---------|
| Python | 3.11+ | 3.12 |
| PostgreSQL | 15+ | 16 |
| Redis | 7.0+ | 7.2 |
| Node.js | 18+ | 20 |
| 内存 | 8GB | 16GB |
| 磁盘 | 20GB SSD | 50GB SSD |

### 1.2 环境变量配置

创建 `.env` 文件：

```bash
# === API Keys ===
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# === Database ===
DATABASE_URL=postgresql://user:password@localhost:5432/eduguide
REDIS_URL=redis://localhost:6379/0

# === Vector Store ===
CHROMA_HOST=localhost
CHROMA_PORT=8001

# === Application ===
APP_ENV=development
LOG_LEVEL=DEBUG
SECRET_KEY=your-secret-key-here

# === External APIs ===
GITHUB_TOKEN=ghp_...  # 可选，用于提高GitHub API限流
```

### 1.3 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/Gout999/Chur_gtp.git
cd Chur_gtp

# 2. 创建Python虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 数据库初始化
alembic upgrade head

# 5. 启动服务（开发模式）
# Terminal 1: Redis
redis-server

# Terminal 2: ChromaDB
chroma run --host localhost --port 8001

# Terminal 3: FastAPI
uvicorn app.main:app --reload --port 8000

# Terminal 4: Frontend (optional)
cd frontend && npm install && npm run dev
```

---

## 第二部分：项目结构详解

### 2.1 目录组织

```
Chur_gtp/
├── app/                          # FastAPI后端
│   ├── __init__.py
│   ├── main.py                   # 应用入口
│   ├── config.py                 # 配置加载
│   ├── dependencies.py           # 依赖注入
│   ├── core/
│   │   ├── auth.py              # JWT认证
│   │   ├── exceptions.py        # 全局异常处理
│   │   └── websocket.py         # WebSocket管理
│   ├── api/
│   │   └── v1/                  # API路由
│   │       ├── teacher.py
│   │       ├── materials.py
│   │       ├── students.py
│   │       ├── escalations.py
│   │       └── messages.py
│   ├── models/                   # SQLAlchemy模型
│   ├── schemas/                  # Pydantic模式
│   └── services/                 # 业务逻辑层
├── agents/                       # Agent节点（核心）
│   ├── __init__.py
│   ├── architect/
│   │   ├── __init__.py
│   │   ├── node.py              # 节点实现
│   │   └── tools.py             # Architect专用工具
│   ├── companion/
│   │   ├── __init__.py
│   │   ├── node.py
│   │   └── tools.py
│   └── catalyst/
│       ├── __init__.py
│       ├── node.py
│       └── tools.py
├── memory/                       # 记忆系统
│   ├── __init__.py
│   ├── working.py               # 工作记忆
│   ├── external.py              # 外部向量记忆
│   ├── archive.py               # 归档存储
│   └── shared.py                # 共享记忆接口
├── prompts/                      # Agent Prompts
│   ├── architect.py
│   ├── companion.py
│   └── catalyst.py
├── tools/                        # 工具生态
│   ├── __init__.py
│   ├── base.py                  # 工具基类
│   ├── ingest.py                # 教材摄取
│   ├── boundary.py              # 知识边界
│   ├── hints.py                 # 提示生成
│   ├── cognition.py             # 认知更新
│   ├── arxiv_monitor.py         # arXiv监控
│   ├── github_monitor.py        # GitHub监控
│   └── briefing.py              # 简报生成
├── graph.py                      # LangGraph图定义
├── frontend/                     # React前端
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── store/
│   │   └── types/
│   └── package.json
├── tests/                        # 测试套件
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── alembic/                      # 数据库迁移
├── docs/                         # 文档
└── requirements.txt
```

### 2.2 文件归属约定

遵循"谁负责，谁修改"原则：

| 路径 | 负责 | 说明 |
|------|------|------|
| `graph.py`, `memory/*` | 框架负责人 | 所有人只读，修改需协商 |
| `agents/architect/*` | 工程师A | Pedagogical Architect |
| `agents/companion/*` | 工程师B | Socratic Companion |
| `agents/catalyst/*` | 工程师C | Curiosity Catalyst |
| `frontend/*` | 前端工程师 | 教师端界面 |

---

## 第三部分：核心模块实现

### 3.1 LangGraph图定义 (graph.py)

```python
# graph.py
from typing import TypedDict, Annotated, List, Optional
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import operator

# 导入Agent节点
from agents.architect import pedagogical_architect_node
from agents.companion import socratic_companion_node
from agents.catalyst import curiosity_catalyst_node

class EduGuideState(TypedDict):
    """全局状态 - Agent共享"""
    # 事件信息
    event_type: str
    event_payload: dict

    # Agent决策
    current_agent: Optional[str]
    agent_decision: Optional[str]
    tools_to_call: List[dict]

    # 记忆
    working_memory: dict

    # 输出
    response_to_student: Optional[str]
    response_to_teacher: Optional[str]
    notifications: List[dict]

    # 控制
    session_id: str
    timestamp: str
    loop_count: int

def route_by_event_type(state: EduGuideState) -> str:
    """根据事件类型选择入口Agent"""
    routing_map = {
        "file_upload": "pedagogical_architect",
        "student_message": "socratic_companion",
        "new_content_detected": "curiosity_catalyst",
        "validation_request": "pedagogical_architect",
        "escalation": "socratic_companion"
    }
    return routing_map.get(state.get("event_type"), "socratic_companion")

def route_by_agent_decision(state: EduGuideState) -> str:
    """Agent自主决定下一步"""
    decision = state.get("agent_decision", "")

    if "request_validation" in decision:
        return "pedagogical_architect"
    if "need_student_guidance" in decision:
        return "socratic_companion"
    if "explore_connection" in decision:
        return "curiosity_catalyst"
    if "monitor_continue" in decision:
        return "curiosity_catalyst"

    return END

def should_continue_monitoring(state: EduGuideState) -> str:
    """Catalyst持续监控循环"""
    if state.get("loop_count", 0) > 100:
        return END
    return "curiosity_catalyst"

def build_eduguide_graph():
    """构建LangGraph图"""
    workflow = StateGraph(EduGuideState)

    # 添加节点
    workflow.add_node("pedagogical_architect", pedagogical_architect_node)
    workflow.add_node("socratic_companion", socratic_companion_node)
    workflow.add_node("curiosity_catalyst", curiosity_catalyst_node)

    # 设置入口
    workflow.set_conditional_entry_point(
        route_by_event_type,
        {
            "file_upload": "pedagogical_architect",
            "student_message": "socratic_companion",
            "new_content_detected": "curiosity_catalyst",
            "validation_request": "pedagogical_architect",
            "escalation": "socratic_companion"
        }
    )

    # 添加条件边
    workflow.add_conditional_edges(
        "pedagogical_architect",
        route_by_agent_decision,
        ["socratic_companion", "curiosity_catalyst", END]
    )
    workflow.add_conditional_edges(
        "socratic_companion",
        route_by_agent_decision,
        ["pedagogical_architect", "curiosity_catalyst", END]
    )
    workflow.add_conditional_edges(
        "curiosity_catalyst",
        should_continue_monitoring,
        ["curiosity_catalyst", END]
    )

    # 添加记忆检查点
    memory = MemorySaver()

    return workflow.compile(checkpointer=memory)

# 全局图实例
eduguide_graph = build_eduguide_graph()
```

### 3.2 记忆系统实现

#### 3.2.1 共享记忆客户端 (memory/shared.py)

```python
# memory/shared.py
import json
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import redis
from sqlalchemy.orm import Session

class SharedMemoryClient:
    """共享记忆客户端 - Agent和教师端共用"""

    def __init__(self, redis_client: redis.Redis, db: Session):
        self.redis = redis_client
        self.db = db

    def write(
        self,
        namespace: str,
        key: str,
        value: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> str:
        """写入共享记忆"""
        entry_id = f"{namespace}:{key}"
        timestamp = datetime.utcnow().isoformat()

        data = {
            "entry_id": entry_id,
            "namespace": namespace,
            "key": key,
            "value": value,
            "timestamp": timestamp,
            "created_at": timestamp
        }

        # Redis写入
        redis_key = f"eduguide:memory:{entry_id}"
        self.redis.set(
            redis_key,
            json.dumps(data, ensure_ascii=False, default=str),
            ex=ttl
        )

        # PostgreSQL持久化
        # ... (数据库写入逻辑)

        # 发布通知
        self.redis.publish(
            f"channel:{namespace}",
            json.dumps({"action": "write", "key": key, "namespace": namespace})
        )

        return entry_id

    def read(self, namespace: str, key: str) -> Optional[Dict]:
        """读取记忆条目"""
        entry_id = f"{namespace}:{key}"
        redis_key = f"eduguide:memory:{entry_id}"

        # 先查Redis
        cached = self.redis.get(redis_key)
        if cached:
            return json.loads(cached)

        # 再查数据库
        # ... (数据库查询逻辑)

        return None

    def read_all(
        self,
        namespace: str,
        filter_dict: Optional[Dict] = None,
        limit: int = 100
    ) -> List[Dict]:
        """读取命名空间下所有条目"""
        pattern = f"eduguide:memory:{namespace}:*"
        keys = self.redis.keys(pattern)

        results = []
        for redis_key in keys[:limit]:
            data = self.redis.get(redis_key)
            if data:
                entry = json.loads(data)
                if filter_dict:
                    match = all(
                        entry["value"].get(k) == v
                        for k, v in filter_dict.items()
                    )
                    if match:
                        results.append(entry)
                else:
                    results.append(entry)

        return results

    def update(
        self,
        namespace: str,
        key: str,
        updates: Dict[str, Any]
    ) -> bool:
        """更新记忆条目"""
        entry = self.read(namespace, key)
        if not entry:
            return False

        entry["value"].update(updates)
        entry["updated_at"] = datetime.utcnow().isoformat()

        # 写回Redis
        entry_id = f"{namespace}:{key}"
        redis_key = f"eduguide:memory:{entry_id}"
        self.redis.set(
            redis_key,
            json.dumps(entry, ensure_ascii=False, default=str)
        )

        return True

    def subscribe(self, namespace: str, callback: Callable):
        """订阅命名空间变化"""
        pubsub = self.redis.pubsub()
        pubsub.subscribe(f"channel:{namespace}")

        for message in pubsub.listen():
            if message["type"] == "message":
                data = json.loads(message["data"])
                callback(data)

# 命名空间常量
NAMESPACES = {
    "teacher_uploads": "教师上传的教材",
    "teacher_authority_graph": "Architect维护的知识权威图谱",
    "teacher_boundary_adjustments": "教师手动调整的知识边界",
    "teacher_escalation_responses": "教师对escalation的响应",
    "teacher_student_messages": "教师与学生的消息",
    "student_cognitive_models": "Companion维护的学生认知模型",
    "interaction_episodes": "Agent交互历史",
    "pending_escalations": "待处理的escalations",
    "pending_validations": "Catalyst待Architect审核的内容",
    "interest_signals": "学生兴趣信号",
    "companion_control": "Companion控制指令"
}
```

### 3.3 Agent节点模板

#### 3.3.1 Architect节点 (agents/architect/node.py)

```python
# agents/architect/node.py
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from graph import EduGuideState
from memory.shared import SharedMemoryClient
from prompts.architect import ARCHITECT_PROMPT
from tools.ingest import ingest_material
from tools.boundary import establish_knowledge_boundary

def pedagogical_architect_node(state: EduGuideState) -> EduGuideState:
    """
    Pedagogical Architect节点实现。

    职责：
    - 处理教师上传的教材
    - 维护知识边界
    - 生成评估策略
    """

    # 初始化
    llm = ChatOpenAI(model="gpt-4", temperature=0.3)
    tools = [ingest_material, establish_knowledge_boundary]

    # 绑定工具
    llm_with_tools = llm.bind_tools(tools)

    # 构建提示
    prompt = ChatPromptTemplate.from_messages([
        ("system", ARCHITECT_PROMPT),
        ("human", "Current state: {state}\n\nObservation: {observation}")
    ])

    # 准备观察信息
    observation = state["event_payload"]

    # 调用LLM
    chain = prompt | llm_with_tools
    result = chain.invoke({
        "state": json.dumps(state["working_memory"], indent=2),
        "observation": json.dumps(observation, indent=2)
    })

    # 处理工具调用
    if result.tool_calls:
        for tool_call in result.tool_calls:
            # 执行工具
            tool_result = execute_tool(tool_call, tools)

            # 记录到共享记忆
            # ...

    # 更新状态
    state["current_agent"] = "pedagogical_architect"
    state["agent_decision"] = result.content
    state["loop_count"] = state.get("loop_count", 0) + 1

    return state

def execute_tool(tool_call: dict, tools: list) -> dict:
    """执行工具调用"""
    tool_name = tool_call["name"]
    tool_args = tool_call["args"]

    for tool in tools:
        if tool.name == tool_name:
            return tool.invoke(tool_args)

    return {"error": f"Tool {tool_name} not found"}
```

#### 3.3.2 Companion节点 (agents/companion/node.py)

```python
# agents/companion/node.py
from graph import EduGuideState
from prompts.companion import COMPANION_PROMPT
from tools.hints import construct_hint
from tools.cognition import update_student_cognition_map

def socratic_companion_node(state: EduGuideState) -> EduGuideState:
    """
    Socratic Companion节点实现。

    职责：
    - 引导学生自主发现答案
    - 维护学生认知模型
    - 必要时escalate给教师
    """

    llm = ChatOpenAI(model="gpt-4", temperature=0.4)
    tools = [construct_hint, update_student_cognition_map, escalate_to_human]

    # 加载学生记忆
    student_id = state["event_payload"].get("student_id")
    cognitive_model = load_cognitive_model(student_id)
    state["working_memory"]["cognitive_model"] = cognitive_model

    # 构建提示
    prompt = ChatPromptTemplate.from_messages([
        ("system", COMPANION_PROMPT),
        ("human", "Student input: {input}\nCognitive model: {cognition}")
    ])

    # 调用LLM
    chain = prompt | llm.bind_tools(tools)
    result = chain.invoke({
        "input": state["event_payload"].get("content"),
        "cognition": json.dumps(cognitive_model, indent=2)
    })

    # 更新状态
    state["current_agent"] = "socratic_companion"
    state["response_to_student"] = result.content
    state["loop_count"] = state.get("loop_count", 0) + 1

    return state
```

#### 3.3.3 Catalyst节点 (agents/catalyst/node.py)

```python
# agents/catalyst/node.py
from graph import EduGuideState
from prompts.catalyst import CATALYST_PROMPT
from tools.arxiv_monitor import search_arxiv
from tools.github_monitor import search_github
from tools.briefing import synthesize_briefing

def curiosity_catalyst_node(state: EduGuideState) -> EduGuideState:
    """
    Curiosity Catalyst节点实现。

    职责：
    - 监控外部信息源
    - 发现学生兴趣与课程连接
    - 主动推送个性化内容
    """

    llm = ChatOpenAI(model="gpt-4", temperature=0.5)
    tools = [search_arxiv, search_github, synthesize_briefing]

    # 判断事件类型
    event_type = state["event_type"]

    if event_type == "new_content_detected":
        # 评估是否通知学生
        return evaluate_and_notify(state, llm, tools)

    elif event_type == "monitor_tick":
        # 执行监控
        return perform_monitoring(state, llm, tools)

    else:
        # 处理学生上传的兴趣资料
        return process_student_curiosity(state, llm, tools)

    return state
```

---

## 第四部分：工具实现

### 4.1 工具基类 (tools/base.py)

```python
# tools/base.py
from typing import Dict, Any, Callable
from functools import wraps
import json
from datetime import datetime

class ToolRegistry:
    """工具注册中心"""

    def __init__(self):
        self._tools: Dict[str, Callable] = {}

    def register(self, name: str, func: Callable):
        """注册工具"""
        self._tools[name] = func
        return func

    def get(self, name: str) -> Callable:
        """获取工具"""
        return self._tools.get(name)

    def list_tools(self) -> Dict[str, str]:
        """列出所有工具"""
        return {
            name: func.__doc__
            for name, func in self._tools.items()
        }

# 全局注册表
tool_registry = ToolRegistry()

def tool(name: str):
    """工具装饰器"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 记录工具调用
            log_tool_call(name, args, kwargs)

            # 执行工具
            result = func(*args, **kwargs)

            # 记录结果
            log_tool_result(name, result)

            return result

        tool_registry.register(name, wrapper)
        return wrapper
    return decorator

def log_tool_call(tool_name: str, args: tuple, kwargs: dict):
    """记录工具调用"""
    call_record = {
        "timestamp": datetime.utcnow().isoformat(),
        "tool": tool_name,
        "args": str(args),
        "kwargs": str(kwargs)
    }
    # 写入日志或共享记忆

def log_tool_result(tool_name: str, result: Any):
    """记录工具结果"""
    result_record = {
        "timestamp": datetime.utcnow().isoformat(),
        "tool": tool_name,
        "result": str(result)[:500]  # 截断
    }
```

### 4.2 具体工具实现示例

```python
# tools/ingest.py
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from typing import List, Dict

from tools.base import tool
from memory.shared import SharedMemoryClient

@tool("ingest_material")
def ingest_material(
    file_path: str,
    source_type: str = "teacher_upload",
    auto_chunk: bool = True,
    custom_chunk_size: int = None
) -> Dict:
    """
    解析教材并建立知识图谱。

    Args:
        file_path: 文件路径
        source_type: 来源类型
        auto_chunk: 是否自动分块
        custom_chunk_size: 自定义分块大小

    Returns:
        解析结果包含知识节点、分块数量等
    """

    # 1. 加载文档
    if file_path.endswith('.pdf'):
        loader = PyPDFLoader(file_path)
        documents = loader.load()
    else:
        # 其他格式处理
        pass

    # 2. 分块
    if auto_chunk:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        chunks = text_splitter.split_documents(documents)

    # 3. 生成嵌入
    embeddings = OpenAIEmbeddings()

    # 4. 提取知识节点（使用LLM）
    knowledge_nodes = extract_knowledge_nodes(chunks)

    # 5. 存储到向量数据库
    # ...

    return {
        "material_id": generate_id(),
        "knowledge_nodes": knowledge_nodes,
        "chunk_count": len(chunks),
        "indexing_status": "success",
        "warnings": []
    }

def extract_knowledge_nodes(chunks: List) -> List[Dict]:
    """使用LLM从文本块提取知识节点"""
    # 实现知识提取逻辑
    pass
```

---

## 第五部分：前端实现

### 5.1 核心服务层

```typescript
// frontend/src/services/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  timeout: 10000
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
```

### 5.2 WebSocket连接

```typescript
// frontend/src/services/websocket.ts
import { io, Socket } from 'socket.io-client';

class WebSocketService {
  private socket: Socket | null = null;

  connect(teacherId: string, token: string) {
    this.socket = io('ws://localhost:8000', {
      query: { teacher_id: teacherId },
      auth: { token }
    });

    this.socket.on('connect', () => {
      console.log('WebSocket connected');
    });

    return this.socket;
  }

  onEscalation(callback: (data: any) => void) {
    this.socket?.on('new_escalation', callback);
  }

  disconnect() {
    this.socket?.disconnect();
  }
}

export const wsService = new WebSocketService();
```

---

## 第六部分：测试策略

### 6.1 单元测试

```python
# tests/unit/test_architect.py
import pytest
from agents.architect.node import pedagogical_architect_node
from graph import EduGuideState

def test_architect_processes_upload():
    """测试Architect处理教材上传"""
    state: EduGuideState = {
        "event_type": "file_upload",
        "event_payload": {
            "file_path": "test.pdf",
            "material_name": "Test Material"
        },
        "working_memory": {},
        "session_id": "test-session",
        "timestamp": "2024-01-01T00:00:00",
        "loop_count": 0
    }

    result = pedagogical_architect_node(state)

    assert result["current_agent"] == "pedagogical_architect"
    assert result["loop_count"] == 1
```

### 6.2 集成测试

```python
# tests/integration/test_memory.py
import pytest
from memory.shared import SharedMemoryClient

def test_memory_write_and_read(redis_client, db_session):
    """测试共享记忆读写"""
    memory = SharedMemoryClient(redis_client, db_session)

    # 写入
    memory.write(
        namespace="test",
        key="test-key",
        value={"data": "test"}
    )

    # 读取
    result = memory.read("test", "test-key")

    assert result["value"]["data"] == "test"
```

### 6.3 E2E测试

```python
# tests/e2e/test_teaching_flow.py
import pytest

@pytest.mark.asyncio
async def test_complete_teaching_flow():
    """测试完整教学流程"""
    # 1. 教师上传教材
    # 2. 学生提问
    # 3. Agent响应
    # 4. 验证结果
    pass
```

---

## 第七部分：部署指南

### 7.1 Docker部署

```dockerfile
# Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/eduguide
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
      - chroma

  db:
    image: postgres:16
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=eduguide
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine

  chroma:
    image: chromadb/chroma:latest
    ports:
      - "8001:8000"

volumes:
  postgres_data:
```

---

## 附录

### A. 环境变量完整列表

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| OPENAI_API_KEY | 是 | - | OpenAI API密钥 |
| ANTHROPIC_API_KEY | 否 | - | Anthropic API密钥（可选） |
| DATABASE_URL | 是 | - | PostgreSQL连接串 |
| REDIS_URL | 是 | - | Redis连接串 |
| CHROMA_HOST | 否 | localhost | ChromaDB主机 |
| CHROMA_PORT | 否 | 8001 | ChromaDB端口 |
| LOG_LEVEL | 否 | INFO | 日志级别 |
| APP_ENV | 否 | development | 运行环境 |

### B. 常见错误与解决

| 错误 | 原因 | 解决 |
|------|------|------|
| ModuleNotFoundError | 依赖未安装 | `pip install -r requirements.txt` |
| Connection refused | Redis/Chroma未启动 | 检查服务状态 |
| API rate limit | 调用频率过高 | 实现重试机制或使用缓存 |

### C. 相关文档链接

- [PRD详细文档](./EduGuide_PRD_Detailed.md)
- [教师端PRD](./EduGuide_教师端PRD.md)
- [评审员文档](./EduGuide_评审员文档.md)
- [API实现](./教师端-API实现.md)
- [前端组件](./教师端-前端组件.md)

---

**文档结束**

本文档与项目代码同步维护，如有疑问请参考PRD或联系团队。
