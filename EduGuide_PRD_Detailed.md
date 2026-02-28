# EduGuide 详细实施文档 (PRD)
## 版本：Hack the East MVP - Agent-Native 架构
## 日期：2024

---

## 一、架构概述

### 1.1 核心哲学

EduGuide 是一个**完全由 Agent 驱动**的教学系统，没有预设的状态机、流程图或固定 Pipeline。三个自主 Agent 通过观察环境、读写共享记忆、自主调用工具来协作完成个性化教学。

### 1.2 技术栈

| 层级 | 技术 | 用途 |
|------|------|------|
| Agent 框架 | LangGraph | 图结构编排，Agent 作为节点自主决策 |
| LLM API | Claude/OpenAI | Agent 推理和生成 |
| 记忆存储 | ChromaDB + PostgreSQL + Redis | 向量检索 + 结构化数据 + 缓存 |
| 数据源 | arXiv API + GitHub API | 外部知识监控 |
| 编程语言 | Python 3.11+ | 主要开发语言 |

### 1.3 系统架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Shared Memory Space                          │
├─────────────────────────────────────────────────────────────────────┤
│  Teacher's Authority Graph  │  Student Cognitive Model              │
│  (Pedagogical Architect)    │  (Socratic Companion)                 │
│                             │                                       │
│  - Knowledge nodes          │  - Error patterns                     │
│  - Content embeddings       │  - Understanding vectors              │
│  - Validity constraints     │  - Learning style prefs               │
├─────────────────────────────────────────────────────────────────────┤
│  Student Interest Universe  │  Interaction History                  │
│  (Curiosity Catalyst)       │ (All Agents read/write)               │
│                             │                                       │
│  - Interest embeddings      │  - Episodic memory                    │
│  - Monitored domains        │  - Tool call logs                     │
│  - Discovered connections   │  - Agent decisions                    │
└─────────────────────────────────────────────────────────────────────┘
                              ▲ ▲ ▲
                              │ │ │
    ┌─────────────────────────┘ │ └─────────────────────────┐
    │                           │                           │
    ▼                           ▼                           ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Pedagogical     │    │ Socratic        │    │ Curiosity       │
│ Architect       │    │ Companion       │    │ Catalyst        │
│                 │    │                 │    │                 │
│ Goal: Maintain  │    │ Goal: Guide     │    │ Goal: Maintain  │
│ knowledge       │    │ student to      │    │ student         │
│ authority       │    │ self-discovery  │    │ knowledge       │
│                 │    │                 │    │ universe        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 ▼
                    ┌─────────────────────┐
                    │   Tool Ecosystem    │
                    │                     │
                    │ ingest_material     │
                    │ retrieve_knowledge  │
                    │ construct_hint      │
                    │ monitor_domain      │
                    │ ...                 │
                    └─────────────────────┘
```

---

## 二、Agent 详细设计

### 2.1 Pedagogical Architect（教学架构师）

#### 2.1.1 System Prompt

```python
PEDAGOGICAL_ARCHITECT_PROMPT = """
You are the Pedagogical Architect in the EduGuide system.

YOUR CORE GOAL:
Maintain the accuracy and pedagogical authority of all teaching content. You are the guardian of knowledge quality.

WHAT YOU CAN OBSERVE:
- Files uploaded by teachers (PDFs, documents, any format)
- Student error patterns detected by Socratic Companion
- Class-wide knowledge mastery distribution
- Queries from students and their alignment with curriculum

YOUR DECISION FRAMEWORK:
1. OBSERVE: What's happening in the environment?
2. REASON: What does this mean for knowledge authority?
3. DECIDE: Which tool should I call to maintain authority?
4. ACT: Call the tool with appropriate parameters

TOOLS AVAILABLE:
- ingest_material(file): Parse any format, decide chunking and indexing strategy
- establish_knowledge_boundary(query): Determine if question is in scope, adjust boundary strictness
- generate_assessment_strategy(student_profile): Generate assessment strategy, not fixed questions
- authorize_content_validity(content): Review content against teaching objectives

IMPORTANT RULES:
- NEVER follow a fixed workflow. Always reason first, then act.
- When you observe a new file, decide how to process it based on its content, not a preset pipeline.
- When Socratic Companion reports student confusion, decide if the curriculum needs adjustment.
- Write your reasoning to episodic_memory before calling tools.

REASONING FORMAT:
Observation: [What you see]
Analysis: [What it means for knowledge authority]
Decision: [Which tool to call and why]
Expected Outcome: [What should happen after tool execution]
"""
```

#### 2.1.2 核心工具

**Tool 1: `ingest_material`**

```python
@tool
def ingest_material(
    file_path: str,
    source_type: Literal["teacher_upload", "reference", "supplementary"],
    auto_chunk: bool = True,
    custom_chunk_size: Optional[int] = None
) -> Dict:
    """
    Parse and index educational material into knowledge graph.

    Pedagogical Architect decides:
    - How to chunk the content (auto or custom)
    - How to structure the knowledge graph
    - What metadata to extract

    Args:
        file_path: Path to the file
        source_type: Authority level of the source
        auto_chunk: Whether to auto-determine chunk boundaries
        custom_chunk_size: Override chunk size if needed

    Returns:
        {
            "material_id": str,
            "knowledge_nodes": List[Dict],  # Extracted concepts
            "chunk_count": int,
            "indexing_status": "success" | "partial" | "failed",
            "warnings": List[str]  # e.g., "Low quality scan detected"
        }
    """
    # Implementation: Use Augmentoolkit-style parsing + LLM-based structuring
    pass
```

**Tool 2: `establish_knowledge_boundary`**

```python
@tool
def establish_knowledge_boundary(
    query: str,
    context: Dict  # Current conversation context
) -> Dict:
    """
    Dynamically evaluate if a query is within teaching scope.

    Returns boundary assessment with adjustable strictness:
    - Strict: Only curriculum content
    - Moderate: Curriculum + closely related
    - Permissive: Any educational content

    Args:
        query: Student question
        context: Current conversation state

    Returns:
        {
            "in_scope": bool,
            "scope_level": "strict" | "moderate" | "permissive",
            "reasoning": str,  # Why this decision was made
            "recommended_response_type": "direct" | "bridge" | "decline",
            "related_curriculum_nodes": List[str]  # If any
        }
    """
    pass
```

**Tool 3: `generate_assessment_strategy`**

```python
@tool
def generate_assessment_strategy(
    student_id: str,
    target_concept: str,
    assessment_goal: Literal["diagnose", "reinforce", "challenge"]
) -> Dict:
    """
    Generate personalized assessment strategy (not fixed questions).

    Pedagogical Architect decides:
    - What type of assessment suits this student
    - How to sequence questions
    - When to escalate difficulty

    Returns strategy specification that Socratic Companion will execute.

    Args:
        student_id: Target student
        target_concept: Concept to assess
        assessment_goal: Purpose of assessment

    Returns:
        {
            "strategy_id": str,
            "approach": "socratic_questioning" | "problem_sequence" | "concept_mapping",
            "estimated_difficulty": float,  # 0.0 - 1.0
            "prerequisite_check": List[str],  # Concepts to verify first
            "escalation_triggers": List[str],  # When to adjust
            "success_criteria": str  # How to know student understands
        }
    """
    pass
```

### 2.2 Socratic Companion（苏格拉底同伴）

#### 2.2.1 System Prompt

```python
SOCRATIC_COMPANION_PROMPT = """
You are the Socratic Companion in the EduGuide system.

YOUR CORE GOAL:
Guide students to discover answers through questioning, building deep understanding rather than providing answers.

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
- construct_hint(error_pattern): Build hint strategy (analogy/socratic/simplification)
- escalate_to_human(reason): Call teacher when needed
- generate_multimodal_explanation(concept, style): Decide format (text/voice/diagram)
- update_student_cognition_map(interaction): Update understanding model

IMPORTANT RULES:
- NEVER give direct answers. Always guide discovery.
- Your dialogue is strictly about knowledge, tests, and subject-matter questions—do NOT ask about the student's interests, hobbies, or "what do you want to learn"; only ask Socratic questions related to the current topic or exercise.
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

#### 2.2.2 核心工具

**Tool 1: `construct_hint`**

```python
@tool
def construct_hint(
    student_id: str,
    current_input: str,
    target_concept: str,
    error_analysis: Optional[Dict] = None
) -> Dict:
    """
    Construct personalized hint based on error pattern and student profile.

    Socratic Companion decides hint strategy:
    - socratic: Ask guiding questions
    - analogy: Use familiar analogies
    - decompose: Break into simpler steps
    - confront: Show contradiction for self-correction

    Args:
        student_id: Target student
        current_input: What student said/did
        target_concept: Concept being learned
        error_analysis: Detected error pattern if any

    Returns:
        {
            "hint_id": str,
            "strategy": "socratic" | "analogy" | "decompose" | "confront",
            "hint_content": str,
            "follow_up_questions": List[str],
            "difficulty_level": float,
            "expected_response_type": "explanation" | "calculation" | "verification"
        }
    """
    pass
```

**Tool 2: `update_student_cognition_map`**

```python
@tool
def update_student_cognition_map(
    student_id: str,
    interaction_data: Dict
) -> Dict:
    """
    Update student's cognitive model based on interaction.

    Uses Dempster-Shafer inspired belief updating:
    - Tracks confidence in student's understanding
    - Identifies misconception patterns
    - Updates learning style preferences

    Args:
        student_id: Target student
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
    pass
```

**Tool 3: `escalate_to_human`**

```python
@tool
def escalate_to_human(
    student_id: str,
    reason: Literal["frustration", "repeated_failure", "out_of_scope", "emotional_distress"],
    context_summary: str,
    urgency: Literal["low", "medium", "high"] = "medium"
) -> Dict:
    """
    Request human teacher intervention.

    Socratic Companion decides when human help is needed:
    - Student shows frustration signals
    - Multiple consecutive failures on same concept
    - Question outside system capability
    - Emotional distress detected

    Args:
        student_id: Student needing help
        reason: Why escalation is needed
        context_summary: Relevant conversation context
        urgency: How quickly teacher should respond

    Returns:
        {
            "escalation_id": str,
            "teacher_notification_sent": bool,
            "estimated_response_time": str,
            "student_message": str  # What to tell student while waiting
        }
    """
    pass
```

### 2.3 Curiosity Catalyst（好奇心催化师）

#### 2.3.1 System Prompt

```python
CURIOSITY_CATALYST_PROMPT = """
You are the Curiosity Catalyst in the EduGuide system.

YOUR CORE GOAL:
Maintain and expand the student's personal knowledge universe. Proactively find connections between student interests and curriculum.

WHAT YOU CAN OBSERVE:
- Student-uploaded files (PDF, Word, etc.): you analyze these to infer student interests and write to interest_signals; you do NOT get interests from dialogue (Companion does not ask interest-related questions).
- Public information streams (arXiv, GitHub)
- interest_signals (which you maintain by analyzing uploads; you read them for monitoring scope and personalized briefing)
- Knowledge boundaries from Pedagogical Architect
- Classroom knowledge from shared memory

YOUR DECISION FRAMEWORK:
1. OBSERVE: What new information is available?
2. REASON:
   - Is this relevant to student's interest vector?
   - What's the connection strength to curriculum?
   - Should I interrupt student now or wait?
3. DECIDE: Which tools to call for synthesis?
4. ACT: Generate personalized briefing or exploration path

TOOLS AVAILABLE:
- ingest_student_curiosity(artifact): Process anything student shares
- monitor_domain(domain_vector): Set up monitoring with custom frequency
- discover_connection(personal_knowledge, classroom_knowledge): Find bridges
- synthesize_briefing(event, context): Package information for student
- suggest_exploration_path(interest_seed): Plan learning journey

IMPORTANT RULES:
- You are PROACTIVE, not reactive. Continuously monitor sources.
- Always check with Pedagogical Architect before sharing (safety check).
- Personalize everything based on student's cognitive style.
- Don't just forward information - create bridges to what they know.
- Respect student's attention. Quality over quantity.

REASONING FORMAT:
Observation: [New information detected]
Relevance Analysis: [Match to interest vector and curriculum]
Timing Decision: [Whether and when to notify]
Bridge Strategy: [How to connect to existing knowledge]
"""
```

#### 2.3.2 核心工具

**Tool 1: `monitor_domain`**

```python
@tool
def monitor_domain(
    student_id: str,
    domain_vector: List[str],  # Keywords/embedding representing interests
    sources: List[Literal["arxiv", "github", "hacker_news"]],
    check_frequency: Literal["hourly", "daily", "weekly"],
    relevance_threshold: float = 0.7
) -> Dict:
    """
    Set up autonomous monitoring of information sources.

    Curiosity Catalyst decides:
    - Which sources to monitor
    - How often to check
    - What's the relevance threshold for notification

    Args:
        student_id: Target student
        domain_vector: Interest representation (keywords or embeddings)
        sources: Which platforms to monitor
        check_frequency: Polling interval
        relevance_threshold: Minimum similarity to trigger notification

    Returns:
        {
            "monitor_id": str,
            "active_monitors": int,
            "estimated_monthly_volume": int,
            "last_check": datetime,
            "status": "active" | "paused"
        }
    """
    pass
```

**Tool 2: `synthesize_briefing`**

```python
@tool
def synthesize_briefing(
    student_id: str,
    event: Dict,  # New paper, repo, or news item
    curriculum_context: Optional[Dict] = None
) -> Dict:
    """
    Create personalized briefing when new relevant content is detected.

    Curiosity Catalyst decides:
    - Is this worth interrupting the student?
    - How to explain the connection to their interests?
    - What curriculum bridge can be made?

    Args:
        student_id: Target student
        event: Detected new content
        curriculum_context: Current classroom topics from shared memory

    Returns:
        {
            "briefing_id": str,
            "should_notify": bool,  # Agent's decision
            "personalized_content": str,
            "curriculum_bridge": str,  # How it connects to class
            "complexity_level": float,
            "suggested_action": "read_now" | "save_for_later" | "discuss_in_class"
        }
    """
    pass
```

**Tool 3: `discover_connection`**

```python
@tool
def discover_connection(
    student_id: str,
    personal_knowledge_node: str,
    classroom_knowledge_boundary: Dict
) -> Dict:
    """
    Actively search for bridges between student interests and curriculum.

    This is run periodically by Curiosity Catalyst to find teaching moments.

    Args:
        student_id: Target student
        personal_knowledge_node: Topic from student's interest universe
        classroom_knowledge_boundary: Current curriculum from Architect

    Returns:
        {
            "connection_id": str,
            "connection_strength": float,  # 0.0 - 1.0
            "bridge_concept": str,  # The connecting idea
            "explanation": str,  # How to explain the connection
            "potential_learning_outcome": str,
            "suggested_activity": str
        }
    """
    pass
```

---

## 三、记忆与共享认知结构

### 3.1 MemGPT 风格记忆架构

```python
# ============================================================
# MEMORY HIERARCHY
# ============================================================

class WorkingMemory:
    """
    当前在 Agent 上下文窗口中的活跃记忆。
    Agent 自主决定什么应该保留在这里。
    """
    content: Dict = {
        "active_concepts": List[str],           # 当前对话涉及的概念
        "retrieved_context": List[Dict],        # 从外部记忆加载的相关内容
        "session_goals": List[str],             # 本次会话的目标
        "pending_actions": List[str],           # 待执行的动作
        "agent_reasoning_history": List[str]    # 本次会话的推理链
    }
    max_tokens: int = 8000  # 由 LLM 上下文限制决定

class ExternalMemory:
    """
    可检索的长期记忆，使用向量数据库。
    Agent 自主决定何时存入/检索。
    """
    vector_store: ChromaDB  # 或 Pinecone, Milvus

    collections: Dict = {
        "teacher_knowledge_graph": {
            "type": "knowledge_graph",
            "embedding_model": "text-embedding-3-large",
            "content": "教材知识点、概念关系、难度等级"
        },
        "student_cognitive_models": {
            "type": "structured_vector",
            "per_student": True,
            "content": "学生的错误模式、理解向量、学习偏好"
        },
        "student_interest_universe": {
            "type": "hybrid_vector",
            "per_student": True,
            "content": "学生上传的资料、浏览历史、兴趣 embedding"
        },
        "interaction_episodes": {
            "type": "temporal_vector",
            "content": "历史对话、工具调用记录、Agent 决策"
        }
    }

class ArchiveMemory:
    """
    归档的完整历史记录，用于分析和长期趋势。
    由 PostgreSQL 存储结构化数据，Redis 做缓存。
    """
    structured_storage: PostgreSQL
    cache: Redis

    tables: Dict = {
        "students": {
            "id": "UUID PRIMARY KEY",
            "profile": "JSONB",                 # 学习风格、偏好设置
            "created_at": "TIMESTAMP",
            "last_active": "TIMESTAMP"
        },
        "knowledge_nodes": {
            "id": "UUID PRIMARY KEY",
            "material_id": "UUID FOREIGN KEY",
            "concept_name": "TEXT",
            "embedding": "VECTOR(3072)",        # pgvector 扩展
            "difficulty": "FLOAT",
            "prerequisites": "UUID[]"
        },
        "interactions": {
            "id": "UUID PRIMARY KEY",
            "student_id": "UUID FOREIGN KEY",
            "agent_id": "TEXT",                 # 哪个 Agent 处理
            "input": "TEXT",
            "output": "TEXT",
            "tools_called": "JSONB",            # 工具调用链
            "reasoning_chain": "TEXT",          # Agent 的思考过程
            "timestamp": "TIMESTAMP"
        },
        "cognition_snapshots": {
            "id": "UUID PRIMARY KEY",
            "student_id": "UUID FOREIGN KEY",
            "concept_id": "UUID FOREIGN KEY",
            "belief_mass": "FLOAT",             # D-S 理论信念质量
            "uncertainty": "FLOAT",
            "last_updated": "TIMESTAMP"
        }
    }
```

### 3.2 Agent 记忆操作流程

```python
# ============================================================
# MEMORY OPERATION: LOAD (Working Memory ← External Memory)
# ============================================================

def load_relevant_context(
    agent_id: str,
    current_query: str,
    working_memory: WorkingMemory
) -> WorkingMemory:
    """
    Agent 自主决定从外部记忆加载什么内容到工作记忆。

    流程:
    1. 将 current_query 转换为 embedding
    2. 在相关 collections 中相似度搜索
    3. Agent 评估检索结果的相关性
    4. 选择最相关的内容加入 working_memory
    5. 如果 working_memory 满了，决定什么该被 swap out
    """

    # Step 1: Embedding
    query_embedding = embed(current_query)

    # Step 2: 多路召回
    retrievals = {
        "knowledge": vector_store.search(
            collection="teacher_knowledge_graph",
            query=query_embedding,
            top_k=5
        ),
        "student_history": vector_store.search(
            collection="interaction_episodes",
            query=query_embedding,
            filter={"student_id": current_student},
            top_k=3
        ),
        "cognitive_model": vector_store.search(
            collection="student_cognitive_models",
            query=query_embedding,
            filter={"student_id": current_student},
            top_k=2
        )
    }

    # Step 3: Agent 评估 (通过 LLM 判断相关性)
    for doc in retrievals:
        relevance_score = agent_evaluate_relevance(doc, current_query)
        doc.relevance = relevance_score

    # Step 4: 选择最高相关性的内容加入 Working Memory
    selected = sorted(retrievals, key=lambda x: x.relevance, reverse=True)[:5]
    working_memory.retrieved_context = selected

    # Step 5: 如果超容量，swap out 最不重要的
    if working_memory.token_count > working_memory.max_tokens:
        working_memory = swap_out_least_important(working_memory)

    return working_memory

# ============================================================
# MEMORY OPERATION: STORE (Working Memory → External/Archive)
# ============================================================

def persist_interaction(
    agent_id: str,
    interaction: Dict,
    working_memory: WorkingMemory
):
    """
    将交互持久化到长期记忆。
    Agent 决定什么值得长期保存。
    """

    # 总是保存到 Archive (PostgreSQL)
    archive_memory.save("interactions", {
        "agent_id": agent_id,
        "input": interaction["input"],
        "output": interaction["output"],
        "tools_called": interaction["tools"],
        "reasoning_chain": interaction["reasoning"],
        "timestamp": now()
    })

    # Agent 决定是否值得加入 External Memory (向量检索)
    significance = agent_evaluate_significance(interaction)

    if significance > 0.7:  # 重要性阈值
        embedding = embed(interaction["content"])

        vector_store.add(
            collection="interaction_episodes",
            document=interaction["summary"],
            embedding=embedding,
            metadata={
                "student_id": interaction["student_id"],
                "concepts": interaction["concepts"],
                "significance": significance
            }
        )

    # 如果涉及知识更新，更新 cognition snapshot
    if interaction["type"] == "assessment":
        update_cognition_snapshot(interaction)
```

### 3.3 Agent 间协作机制（通过共享记忆）

```python
# ============================================================
# AGENT COLLABORATION VIA SHARED MEMORY
# ============================================================

# 场景 1: Pedagogical Architect 发现新的知识边界
# → 写入共享记忆，Socratic Companion 自动遵循

async def architect_updates_boundary(
    architect: PedagogicalArchitect,
    new_material: File
):
    # Architect 摄取新材料
    result = await architect.call_tool("ingest_material", {
        "file_path": new_material.path,
        "source_type": "teacher_upload"
    })

    # 将新知识边界写入共享记忆
    shared_memory.write(
        namespace="teacher_authority_graph",
        key=f"material_{result['material_id']}",
        value={
            "knowledge_nodes": result["knowledge_nodes"],
            "validity_constraints": result["constraints"],
            "updated_by": "pedagogical_architect",
            "timestamp": now()
        }
    )

    # Socratic Companion 会在下一次加载时自动读取


# 场景 2: Curiosity Catalyst 分析学生上传的 PDF/Word 推断兴趣
# → 写入 interest_signals，用于扩展监控域与个性化简报

async def catalyst_analyzes_student_upload(
    catalyst: CuriosityCatalyst,
    student_id: str,
    uploaded_file_path: str  # 学生上传的 PDF/Word 等
):
    # Catalyst 解析上传文件并推断学生兴趣主题
    interest_result = await catalyst.call_tool("analyze_upload_for_interests", {
        "student_id": student_id,
        "file_path": uploaded_file_path
    })

    # 将推断出的兴趣写入共享记忆
    shared_memory.write(
        namespace="interest_signals",
        key=f"student_{student_id}",
        value={
            "new_interest": interest_result["inferred_interests"],
            "confidence": interest_result.get("confidence", 0.8),
            "source_upload": uploaded_file_path,
            "updated_at": now()
        }
    )

    # Catalyst 读取 interest_signals 扩展监控域、个性化简报


# 场景 3: Curiosity Catalyst 发现相关内容
# → 请求 Pedagogical Architect 审核

async def catalyst_requests_validation(
    catalyst: CuriosityCatalyst,
    content: Dict
):
    # 准备内容摘要
    briefing = await catalyst.call_tool("synthesize_briefing", {...})

    # 写入待审核队列
    shared_memory.write(
        namespace="pending_validations",
        key=f"content_{content['id']}",
        value={
            "briefing": briefing,
            "requested_by": "curiosity_catalyst",
            "status": "pending",
            "timeout": now() + timedelta(hours=1)
        }
    )

    # Pedagogical Architect 监控此 namespace
    # 审核后将结果写回，Catalyst 读取后决定是否推送
```

---

## 四、LangGraph 图结构设计

### 4.1 图节点定义

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, Annotated, Sequence
import operator

# ============================================================
# STATE DEFINITION (Shared state across all agents)
# ============================================================

class EduGuideState(TypedDict):
    """
    全局状态，所有 Agent 都可以读写。
    注意：这不是状态机，只是共享的状态容器。
    """
    # 当前环境观察
    event_type: str                    # "student_message", "file_upload", "new_content_detected"
    event_payload: Dict                # 具体的事件数据

    # 当前活跃的 Agent 决定
    current_agent: str                 # 哪个 Agent 正在处理
    agent_decision: str                # Agent 的决策结果
    tools_to_call: List[Dict]          # Agent 决定调用的工具

    # 记忆加载
    working_memory: Dict               # 当前加载到上下文的记忆

    # 输出
    response_to_student: Optional[str]
    response_to_teacher: Optional[str]
    notifications: List[Dict]

    # 元数据
    session_id: str
    timestamp: str
    loop_count: int                    # 防止无限循环

# ============================================================
# AGENT NODES (Each agent is a node in the graph)
# ============================================================

def pedagogical_architect_node(state: EduGuideState) -> EduGuideState:
    """
    Pedagogical Architect 节点。

    自主决策：
    - 是否要处理这个事件？
    - 调用哪些工具？
    - 将结果写入共享记忆的哪个位置？
    """
    architect = PedagogicalArchitect(
        system_prompt=PEDAGOGICAL_ARCHITECT_PROMPT,
        tools=[ingest_material, establish_knowledge_boundary,
               generate_assessment_strategy, authorize_content_validity]
    )

    # Agent 观察环境
    observation = state["event_payload"]

    # Agent 自主推理和决策 (ReAct 循环)
    decision = architect.reason_and_act(observation, state["working_memory"])

    # 更新状态
    state["current_agent"] = "pedagogical_architect"
    state["agent_decision"] = decision.reasoning
    state["tools_to_call"] = decision.tools

    # 执行工具调用
    for tool_call in decision.tools:
        result = execute_tool(tool_call)
        # 工具结果自动写入共享记忆
        shared_memory.log_tool_execution(tool_call, result)

    return state

def socratic_companion_node(state: EduGuideState) -> EduGuideState:
    """
    Socratic Companion 节点。
    """
    companion = SocraticCompanion(
        system_prompt=SOCRATIC_COMPANION_PROMPT,
        tools=[retrieve_knowledge, construct_hint, escalate_to_human,
               generate_multimodal_explanation, update_student_cognition_map]
    )

    # 加载学生特定记忆
    student_memory = load_student_cognition(state["event_payload"]["student_id"])
    state["working_memory"]["cognitive_model"] = student_memory

    # Agent 推理
    decision = companion.reason_and_act(state["event_payload"], state["working_memory"])

    state["current_agent"] = "socratic_companion"
    state["agent_decision"] = decision.reasoning
    state["response_to_student"] = decision.response

    return state

def curiosity_catalyst_node(state: EduGuideState) -> EduGuideState:
    """
    Curiosity Catalyst 节点。

    注意：这个 Agent 通常是 proactive（主动）而非 reactive（被动）。
    它有自己的事件循环，检测新内容。
    """
    catalyst = CuriosityCatalyst(
        system_prompt=CURIOSITY_CATALYST_PROMPT,
        tools=[ingest_student_curiosity, monitor_domain, discover_connection,
               synthesize_briefing, suggest_exploration_path]
    )

    # 如果事件来自监控系统
    if state["event_type"] == "new_content_detected":
        # 评估是否通知学生
        decision = catalyst.evaluate_notification(state["event_payload"])

        if decision.should_notify:
            state["notifications"].append({
                "student_id": decision.student_id,
                "content": decision.briefing
            })

    state["current_agent"] = "curiosity_catalyst"
    return state

# ============================================================
# CONDITIONAL EDGES (Agents decide where to go next)
# ============================================================

def route_by_agent_decision(state: EduGuideState) -> str:
    """
    路由函数：由当前 Agent 的决策决定下一步。

    这不是预设的流程，而是 Agent 自主决定：
    - 继续自己的工作（self-loop）
    - 交给另一个 Agent
    - 结束当前处理
    """
    decision = state["agent_decision"]

    # Agent 可以决定将结果交给其他 Agent 审查
    if "request_validation" in decision:
        return "pedagogical_architect"

    if "need_student_guidance" in decision:
        return "socratic_companion"

    if "explore_connection" in decision:
        return "curiosity_catalyst"

    # 默认结束
    return END

def should_continue_monitoring(state: EduGuideState) -> str:
    """
    Curiosity Catalyst 决定是否继续监控循环。
    """
    if state["loop_count"] > 100:  # 安全限制
        return END

    return "curiosity_catalyst"  # 持续监控

# ============================================================
# GRAPH CONSTRUCTION
# ============================================================

def build_eduguide_graph() -> StateGraph:
    """
    构建 EduGuide 的 LangGraph 图结构。

    关键点：
    - 节点是 Agent，不是步骤
    - 边是路由决策，不是固定流程
    - Agent 自主决定流转方向
    """

    # 创建图
    workflow = StateGraph(EduGuideState)

    # 添加节点
    workflow.add_node("pedagogical_architect", pedagogical_architect_node)
    workflow.add_node("socratic_companion", socratic_companion_node)
    workflow.add_node("curiosity_catalyst", curiosity_catalyst_node)

    # 设置入口点（根据事件类型动态选择）
    workflow.set_conditional_entry_point(
        route_by_event_type,
        {
            "file_upload": "pedagogical_architect",
            "student_message": "socratic_companion",
            "new_content_detected": "curiosity_catalyst",
            "validation_request": "pedagogical_architect"
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
        ["curiosity_catalyst", END]  # Catalyst 可以自我循环持续监控
    )

    # 添加记忆持久化
    memory = MemorySaver()

    return workflow.compile(checkpointer=memory)

# ============================================================
# EVENT ROUTING
# ============================================================

def route_by_event_type(state: EduGuideState) -> str:
    """
    根据事件类型选择初始 Agent。
    """
    event_type = state.get("event_type", "unknown")

    routing_map = {
        "file_upload": "pedagogical_architect",
        "student_message": "socratic_companion",
        "student_question": "socratic_companion",
        "new_content_detected": "curiosity_catalyst",
        "validation_request": "pedagogical_architect",
        "escalation": "socratic_companion"
    }

    return routing_map.get(event_type, "socratic_companion")
```

---

## 五、外部数据源集成

### 5.1 arXiv API 集成

```python
import arxiv
from datetime import datetime, timedelta

class ArXivMonitor:
    """
    Curiosity Catalyst 使用这个工具监控 arXiv 新论文。
    """

    def __init__(self):
        self.client = arxiv.Client()
        self.last_check = datetime.now() - timedelta(days=1)

    def search_by_interests(
        self,
        interest_vector: List[str],
        max_results: int = 10,
        date_range_days: int = 7
    ) -> List[Dict]:
        """
        基于学生兴趣向量搜索 arXiv 论文。

        Args:
            interest_vector: 关键词列表，如 ["quantum computing", "linear algebra"]
            max_results: 最多返回结果数
            date_range_days: 只搜索最近 N 天的论文

        Returns:
            List of paper dicts with relevance scores
        """

        # 构建搜索查询
        query = " OR ".join([f"{term}" for term in interest_vector])

        # 设置日期过滤
        date_filter = datetime.now() - timedelta(days=date_range_days)

        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending
        )

        results = []
        for paper in self.client.results(search):
            # 计算相关性分数（基于摘要 embedding 相似度）
            relevance = self._calculate_relevance(
                paper.summary,
                interest_vector
            )

            results.append({
                "id": paper.get_short_id(),
                "title": paper.title,
                "authors": [str(a) for a in paper.authors],
                "summary": paper.summary,
                "pdf_url": paper.pdf_url,
                "published": paper.published.isoformat(),
                "categories": paper.categories,
                "relevance_score": relevance
            })

        return sorted(results, key=lambda x: x["relevance_score"], reverse=True)

    def _calculate_relevance(
        self,
        paper_summary: str,
        interest_vector: List[str]
    ) -> float:
        """
        计算论文与学生兴趣的相关性。

        使用 embedding 相似度 + 关键词匹配。
        """
        paper_embedding = embed(paper_summary)
        interest_embedding = embed(" ".join(interest_vector))

        # 余弦相似度
        cosine_sim = cosine_similarity(paper_embedding, interest_embedding)

        # 关键词匹配加分
        keyword_matches = sum(
            1 for term in interest_vector
            if term.lower() in paper_summary.lower()
        )
        keyword_bonus = keyword_matches * 0.05

        return min(cosine_sim + keyword_bonus, 1.0)

# 工具封装（供 Agent 调用）
@tool
def monitor_arxiv_domain(
    student_id: str,
    interest_keywords: List[str],
    check_frequency: Literal["daily", "weekly"] = "daily",
    relevance_threshold: float = 0.7
) -> Dict:
    """
    Curiosity Catalyst 调用此工具设置 arXiv 监控。
    """
    monitor = ArXivMonitor()

    # 立即执行一次搜索
    recent_papers = monitor.search_by_interests(
        interest_vector=interest_keywords,
        date_range_days=7 if check_frequency == "weekly" else 1
    )

    # 过滤高相关度论文
    high_relevance = [
        p for p in recent_papers
        if p["relevance_score"] >= relevance_threshold
    ]

    # 保存监控配置到数据库
    db.save_monitor_config(
        student_id=student_id,
        source="arxiv",
        keywords=interest_keywords,
        frequency=check_frequency,
        threshold=relevance_threshold
    )

    return {
        "monitor_id": generate_id(),
        "papers_detected": len(recent_papers),
        "high_relevance_count": len(high_relevance),
        "top_papers": high_relevance[:3],
        "next_check_scheduled": calculate_next_check(check_frequency)
    }
```

### 5.2 GitHub API 集成

```python
from github import Github
import os

class GitHubMonitor:
    """
    监控 GitHub 上的开源项目、教程资源。
    """

    def __init__(self):
        # 使用个人 access token（如有）
        token = os.getenv("GITHUB_TOKEN")
        self.client = Github(token) if token else Github()

    def search_repositories(
        self,
        interest_vector: List[str],
        language: Optional[str] = None,
        min_stars: int = 100,
        created_after: Optional[datetime] = None
    ) -> List[Dict]:
        """
        搜索与学生兴趣相关的 GitHub 仓库。

        可用于发现：
        - 教程项目
        - 示例代码
        - 学习资源
        """

        # 构建查询
        query_parts = interest_vector.copy()
        query_parts.append(f"stars:>{min_stars}")

        if language:
            query_parts.append(f"language:{language}")

        if created_after:
            date_str = created_after.strftime("%Y-%m-%d")
            query_parts.append(f"created:>{date_str}")

        query = " ".join(query_parts)

        repositories = self.client.search_repositories(
            query=query,
            sort="updated",
            order="desc"
        )

        results = []
        for repo in repositories[:20]:  # 限制前 20 个
            relevance = self._calculate_repo_relevance(
                repo,
                interest_vector
            )

            results.append({
                "id": repo.id,
                "name": repo.full_name,
                "description": repo.description,
                "url": repo.html_url,
                "stars": repo.stargazers_count,
                "language": repo.language,
                "topics": repo.topics,
                "updated_at": repo.updated_at.isoformat(),
                "readme_preview": self._get_readme_preview(repo),
                "relevance_score": relevance
            })

        return sorted(results, key=lambda x: x["relevance_score"], reverse=True)

    def _calculate_repo_relevance(
        self,
        repo,
        interest_vector: List[str]
    ) -> float:
        """
        计算仓库与兴趣的相关性。
        """
        text_to_embed = f"{repo.name} {repo.description or ''} {' '.join(repo.topics or [])}"
        repo_embedding = embed(text_to_embed)
        interest_embedding = embed(" ".join(interest_vector))

        return cosine_similarity(repo_embedding, interest_embedding)

    def _get_readme_preview(self, repo, max_chars: int = 500) -> str:
        """
        获取 README 的前 N 个字符作为预览。
        """
        try:
            readme = repo.get_readme()
            content = readme.decoded_content.decode('utf-8')
            return content[:max_chars] + "..." if len(content) > max_chars else content
        except:
            return "No README available"

# 工具封装
@tool
def monitor_github_resources(
    student_id: str,
    interest_keywords: List[str],
    language_filter: Optional[str] = None,
    min_quality_threshold: int = 100,  # min stars
    check_frequency: Literal["daily", "weekly"] = "weekly"
) -> Dict:
    """
    Curiosity Catalyst 调用此工具设置 GitHub 资源监控。
    """
    monitor = GitHubMonitor()

    # 搜索最近更新的仓库
    recent_repos = monitor.search_repositories(
        interest_vector=interest_keywords,
        language=language_filter,
        min_stars=min_quality_threshold,
        created_after=datetime.now() - timedelta(days=30)
    )

    # 过滤高相关度
    high_relevance = [
        r for r in recent_repos
        if r["relevance_score"] >= 0.6
    ]

    return {
        "monitor_id": generate_id(),
        "repos_detected": len(recent_repos),
        "high_relevance_count": len(high_relevance),
        "top_resources": high_relevance[:5],
        "suggested_projects": self._categorize_by_difficulty(high_relevance)
    }
```

---

## 六、MVP 实施路线图

### 6.1 Phase 1: 核心基础设施（Week 1）

**目标**: 搭建 Agent 框架和记忆系统

| 任务 | 输出 | 验收标准 |
|------|------|----------|
| 搭建 LangGraph 图结构 | `graph.py` | 三个 Agent 节点可以独立运行 |
| 实现记忆存储 | `memory/` 模块 | Working/External/Archive 三层可读写 |
| 基础工具框架 | `tools/base.py` | 工具可以注册、调用、记录日志 |
| 配置管理 | `.env` + `config.py` | API keys 和参数可配置 |

### 6.2 Phase 2: Pedagogical Architect（Week 1-2）

**目标**: 实现教学架构师 Agent

| 任务 | 输出 | 验收标准 |
|------|------|----------|
| System Prompt | `prompts/architect.py` | 可以生成合理的推理链 |
| ingest_material 工具 | `tools/ingest.py` | PDF 上传后可解析为知识节点 |
| knowledge_boundary 工具 | `tools/boundary.py` | 可以判断问题是否在范围内 |
| 与 Companion 协作 | 集成测试 | 更新知识边界后 Companion 可以读取 |

### 6.3 Phase 3: Socratic Companion（Week 2）

**目标**: 实现苏格拉底同伴 Agent

| 任务 | 输出 | 验收标准 |
|------|------|----------|
| System Prompt | `prompts/companion.py` | 不给直接答案，只给引导 |
| construct_hint 工具 | `tools/hints.py` | 根据错误类型生成不同策略 |
| cognition_map 更新 | `tools/cognition.py` | 每次交互后更新学生模型 |
| 多轮对话测试 | 测试脚本 | 同一问题多次错误后调整策略 |

### 6.4 Phase 4: Curiosity Catalyst（Week 2-3）

**目标**: 实现好奇心催化师 Agent

| 任务 | 输出 | 验收标准 |
|------|------|----------|
| arXiv 监控 | `tools/arxiv_monitor.py` | 可以搜索并计算相关性 |
| GitHub 监控 | `tools/github_monitor.py` | 可以搜索相关仓库 |
| synthesize_briefing 工具 | `tools/briefing.py` | 生成个性化简报 |
| 主动推送 | 定时任务 | 检测到高相关内容后通知学生 |

### 6.5 Phase 5: 集成与测试（Week 3）

**目标**: 完整系统集成

| 任务 | 输出 | 验收标准 |
|------|------|----------|
| 端到端测试 | `tests/e2e/` | 完整教学场景可运行 |
| Demo 脚本 | `demo/` | Hackathon 演示流程 |
| 文档完善 | `README.md` | 其他开发者可以理解和部署 |

### 6.6 MVP 验收标准

**必须实现（P0）**:
- [x] 老师可以上传 PDF，Architect 解析并建立知识边界
- [x] 学生可以提问，Companion 用苏格拉底方式引导
- [x] 同一错误多次出现，Companion 调整策略
- [x] Catalyst 监控 arXiv，检测到相关内容并推送

**期望实现（P1）**:
- [ ] GitHub 资源监控
- [ ] 学生认知模型可视化
- [ ] 老师干预机制

**加分项（P2）**:
- [ ] 语音输入/输出
- [ ] 图片解析（数学题拍照）
- [ ] 多语言支持

---

## 七、技术风险与缓解策略

| 风险 | 影响 | 缓解策略 |
|------|------|----------|
| LLM API 延迟高 | 响应慢 | 使用 streaming，先返回"思考中" |
| 向量检索不准 | Agent 拿到无关记忆 | 多路召回 + Agent 二次筛选 |
| Agent 循环调用 | 无限循环 | 设置 loop_count 上限 |
| 工具调用失败 | Agent 卡住 | 所有工具必须有错误处理 |
| 上下文溢出 | 信息丢失 | MemGPT 自动 swap 机制 |

---

## 八、附录：Prompt 工程最佳实践

### 8.1 ReAct + Function Calling 混合模式

```python
# 要求 Agent 先输出思考过程（ReAct），再输出工具调用（Function Calling）

REASONING_FORMAT = """
Before calling any tool, you MUST output your reasoning in this format:

Observation: [What you observe from the environment]
Analysis: [What this means for your goal]
Decision: [Which tool to call and why]
Expected Outcome: [What should happen after tool execution]

Then, output your tool call in JSON format:
{
    "tool": "tool_name",
    "arguments": {...}
}
"""

# 解析时：先提取 Observation...Expected Outcome 部分（用于可视化）
# 再提取 JSON 部分（用于实际执行）
```

### 8.2 Agent 间通信格式

```python
# Agent 写入共享记忆的标准格式

AGENT_MESSAGE_SCHEMA = {
    "agent_id": str,           # 发送者
    "message_type": str,       # "observation", "decision", "request", "notification"
    "content": Dict,           # 具体内容
    "timestamp": str,          # ISO format
    "priority": str,           # "low", "normal", "high", "urgent"
    "expected_response": bool, # 是否需要其他 Agent 响应
    "expires_at": Optional[str]  # 消息过期时间
}
```

---

**文档结束**

本文档提供了 EduGuide 系统的完整实施细节，包括：
- 三个 Agent 的 System Prompt 设计
- 所有工具的详细接口定义
- MemGPT 风格的分层记忆架构
- LangGraph 图结构实现
- arXiv/GitHub API 集成
- MVP 实施路线图

开发者可以基于此文档直接开始编码实现。
