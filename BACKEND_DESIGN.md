# 後端架構設計文檔

## 1. 系統概覽

### 1.1 技術棧
- **框架**: FastAPI (Python)
- **數據庫**: PostgreSQL (主要數據), Redis (緩存/會話)
- **ORM**: SQLAlchemy 2.0
- **遷移**: Alembic
- **認證**: JWT + OAuth2
- **文件存儲**: 本地存儲 (開發) / AWS S3 (生產)
- **AI集成**: OpenAI API / Claude API

### 1.2 項目結構
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI入口
│   ├── config.py            # 配置管理
│   ├── dependencies.py      # 依賴注入
│   ├── database.py          # 數據庫連接
│   ├── models/              # SQLAlchemy模型
│   │   ├── __init__.py
│   │   ├── user.py          # 用戶模型
│   │   ├── class_.py        # 班級模型
│   │   ├── assignment.py    # 作業模型
│   │   ├── material.py      # 學習材料模型
│   │   ├── mistake.py       # 錯題模型
│   │   ├── submission.py    # 提交模型
│   │   └── ai_enhancement.py # AI增強模型
│   ├── schemas/             # Pydantic模型
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── class_.py
│   │   ├── assignment.py
│   │   ├── material.py
│   │   ├── mistake.py
│   │   ├── submission.py
│   │   └── ai_enhancement.py
│   ├── api/                 # API路由
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── auth.py      # 認證API
│   │       ├── users.py     # 用戶API
│   │       ├── classes.py   # 班級API
│   │       ├── assignments.py # 作業API
│   │       ├── materials.py # 材料API
│   │       ├── mistakes.py  # 錯題API
│   │       ├── submissions.py # 提交API
│   │       ├── ai.py        # AI功能API
│   │       └── chat.py      # 聊天API
│   ├── services/            # 業務邏輯
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── class_service.py
│   │   ├── assignment_service.py
│   │   ├── material_service.py
│   │   ├── mistake_service.py
│   │   ├── ai_service.py
│   │   └── file_service.py
│   ├── core/                # 核心功能
│   │   ├── __init__.py
│   │   ├── security.py      # 安全工具
│   │   ├── exceptions.py    # 自定義異常
│   │   └── utils.py         # 工具函數
│   └── tests/               # 測試
├── alembic/                 # 數據庫遷移
├── uploads/                 # 上傳文件存儲
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## 2. 數據庫設計

### 2.1 用戶相關

```sql
-- users 表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('teacher', 'student')),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- teacher_profiles 表
CREATE TABLE teacher_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    subject VARCHAR(100),
    bio TEXT,
    avatar_url VARCHAR(500)
);

-- student_profiles 表
CREATE TABLE student_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    grade_level VARCHAR(50),
    bio TEXT,
    avatar_url VARCHAR(500)
);
```

### 2.2 班級相關

```sql
-- classes 表
CREATE TABLE classes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    subject VARCHAR(100) NOT NULL,
    teacher_id UUID REFERENCES users(id) ON DELETE CASCADE,
    schedule VARCHAR(255),
    color VARCHAR(50) DEFAULT 'from-blue-500/20 to-blue-600/10',
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- class_students 表 (多對多關係)
CREATE TABLE class_students (
    class_id UUID REFERENCES classes(id) ON DELETE CASCADE,
    student_id UUID REFERENCES users(id) ON DELETE CASCADE,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (class_id, student_id)
);
```

### 2.3 學習材料相關

```sql
-- materials 表
CREATE TABLE materials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    subject VARCHAR(100) NOT NULL,
    description TEXT,
    file_name VARCHAR(255),
    file_path VARCHAR(500),
    file_type VARCHAR(50),
    file_size INTEGER,
    pages INTEGER,
    is_custom BOOLEAN DEFAULT false,
    uploaded_by UUID REFERENCES users(id),
    class_id UUID REFERENCES classes(id),
    color VARCHAR(50) DEFAULT 'blue',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- enhanced_notes 表 (AI增強筆記)
CREATE TABLE enhanced_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    original_material_id UUID REFERENCES materials(id),
    enhanced_file_name VARCHAR(255),
    enhanced_file_path VARCHAR(500),
    enhancement_settings JSONB,
    status VARCHAR(50) DEFAULT 'processing',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);
```

### 2.4 作業相關

```sql
-- assignments 表
CREATE TABLE assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    subject VARCHAR(100) NOT NULL,
    class_id UUID REFERENCES classes(id) ON DELETE CASCADE,
    created_by UUID REFERENCES users(id),
    max_score INTEGER DEFAULT 100,
    due_date TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'draft', 'closed')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- submissions 表
CREATE TABLE submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assignment_id UUID REFERENCES assignments(id) ON DELETE CASCADE,
    student_id UUID REFERENCES users(id) ON DELETE CASCADE,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'submitted' CHECK (status IN ('submitted', 'graded', 'late', 'missing')),
    score INTEGER,
    feedback TEXT,
    files JSONB, -- [{"file_name": "...", "file_path": "..."}]
    UNIQUE(assignment_id, student_id)
);
```

### 2.5 錯題相關

```sql
-- mistakes 表
CREATE TABLE mistakes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES users(id) ON DELETE CASCADE,
    subject VARCHAR(100) NOT NULL,
    question TEXT NOT NULL,
    student_answer TEXT,
    correct_answer TEXT,
    explanation TEXT,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'reviewed')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP
);

-- mistake_topics 表
CREATE TABLE mistake_topics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mistake_id UUID REFERENCES mistakes(id) ON DELETE CASCADE,
    topic VARCHAR(100) NOT NULL
);
```

### 2.6 AI功能相關

```sql
-- ai_enhancements 表
CREATE TABLE ai_enhancements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    material_id UUID REFERENCES materials(id),
    enhancement_type VARCHAR(50) NOT NULL,
    settings JSONB,
    result_content TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- chat_sessions 表
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_type VARCHAR(50) DEFAULT 'homework_help',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- chat_messages 表
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'ai')),
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 3. API設計

### 3.1 認證API

```
POST /api/v1/auth/register          # 註冊
POST /api/v1/auth/login             # 登錄
POST /api/v1/auth/refresh           # 刷新令牌
POST /api/v1/auth/logout            # 登出
GET  /api/v1/auth/me                # 獲取當前用戶
```

### 3.2 用戶API

```
GET    /api/v1/users/me             # 獲取個人資料
PUT    /api/v1/users/me             # 更新個人資料
GET    /api/v1/users/{id}           # 獲取用戶詳情 (管理員)
```

### 3.3 班級API

```
GET    /api/v1/classes              # 獲取班級列表
POST   /api/v1/classes              # 創建班級 (老師)
GET    /api/v1/classes/{id}         # 獲取班級詳情
PUT    /api/v1/classes/{id}         # 更新班級 (老師)
DELETE /api/v1/classes/{id}         # 刪除班級 (老師)
POST   /api/v1/classes/{id}/students # 添加學生 (老師)
DELETE /api/v1/classes/{id}/students/{student_id} # 移除學生
GET    /api/v1/classes/{id}/materials # 獲取班級材料
```

### 3.4 學習材料API

```
GET    /api/v1/materials            # 獲取材料列表
POST   /api/v1/materials            # 上傳材料
GET    /api/v1/materials/{id}       # 獲取材料詳情
PUT    /api/v1/materials/{id}       # 更新材料
DELETE /api/v1/materials/{id}       # 刪除材料
GET    /api/v1/materials/{id}/download # 下載材料
POST   /api/v1/materials/{id}/enhance  # 請求AI增強
GET    /api/v1/materials/enhanced   # 獲取AI增強筆記列表
```

### 3.5 作業API

```
GET    /api/v1/assignments          # 獲取作業列表
POST   /api/v1/assignments          # 創建作業 (老師)
GET    /api/v1/assignments/{id}     # 獲取作業詳情
PUT    /api/v1/assignments/{id}     # 更新作業 (老師)
DELETE /api/v1/assignments/{id}     # 刪除作業 (老師)
POST   /api/v1/assignments/{id}/submit # 提交作業 (學生)
GET    /api/v1/assignments/{id}/submissions # 獲取提交列表 (老師)
PUT    /api/v1/assignments/{id}/submissions/{submission_id}/grade # 評分 (老師)
```

### 3.6 錯題API

```
GET    /api/v1/mistakes             # 獲取錯題列表
POST   /api/v1/mistakes             # 添加錯題
GET    /api/v1/mistakes/{id}        # 獲取錯題詳情
PUT    /api/v1/mistakes/{id}        # 更新錯題
DELETE /api/v1/mistakes/{id}        # 刪除錯題
POST   /api/v1/mistakes/{id}/review # 標記為已復習
GET    /api/v1/mistakes/stats       # 獲取錯題統計
```

### 3.7 AI功能API

```
POST   /api/v1/ai/enhance           # AI增強材料
GET    /api/v1/ai/enhance/{id}/status # 獲取增強狀態
POST   /api/v1/ai/chat              # AI聊天
GET    /api/v1/ai/daily-papers      # 獲取每日推薦
POST   /api/v1/ai/generate-questions # 生成練習題
```

## 4. 實現計劃

### 階段1: 基礎設施 (1-2天)
1. 設置數據庫連接
2. 創建所有模型
3. 設置Alembic遷移
4. 配置JWT認證

### 階段2: 核心API (2-3天)
1. 實現認證API
2. 實現用戶管理
3. 實現班級管理
4. 實現文件上傳/下載

### 階段3: 業務API (3-4天)
1. 實現學習材料管理
2. 實現作業系統
3. 實現錯題追踪
4. 實現AI增強功能

### 階段4: 測試與部署 (1-2天)
1. API測試
2. 前後端聯調
3. 部署到服務器

## 5. 安全考慮

1. **認證**: JWT令牌 + 刷新機制
2. **授權**: 角色基礎訪問控制 (RBAC)
3. **文件安全**: 文件類型驗證 + 大小限制
4. **API限流**: 防止濫用
5. **數據驗證**: 輸入驗證和消毒

## 6. 擴展性考慮

1. **數據庫**: 支持讀寫分離
2. **文件存儲**: 支持S3等對象存儲
3. **AI服務**: 支持多種AI提供商
4. **緩存**: Redis緩存熱門數據
