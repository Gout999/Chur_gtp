# 🚀 ChurGPT 部署指南

## 快速开始 (推荐)

### 使用 Docker Compose 部署 (最简方式)

```bash
# 1. 进入项目目录
cd /Users/gout/Chur_gtp

# 2. 运行部署脚本
./deploy.sh prod
```

部署完成后：
- 前端: http://localhost
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

## 手动部署

### 方式一: 使用 Docker (生产环境推荐)

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置强密码和 API 密钥

# 2. 构建并启动服务
docker-compose -f docker-compose.prod.yml up -d

# 3. 运行数据库迁移
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# 4. 查看日志
docker-compose -f docker-compose.prod.yml logs -f
```

### 方式二: 本地开发部署

**后端部署：**

```bash
# 1. 安装 Python 依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，使用 SQLite 数据库: DATABASE_URL=sqlite:///./churgpt.db

# 3. 运行数据库迁移
alembic upgrade head

# 4. 启动后端服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**前端部署：**

```bash
# 1. 进入前端目录
cd frontend

# 2. 安装依赖
npm install

# 3. 启动开发服务器
npm run dev
```

前端将在 http://localhost:5173 运行
后端将在 http://localhost:8000 运行

## 环境变量配置

### 必需配置

```env
# 应用安全
SECRET_KEY=your-strong-secret-key-here

# 数据库 (生产环境使用 PostgreSQL)
DATABASE_URL=postgresql://postgres:your-password@db:5432/churgpt

# AI 功能 (可选，没有也能运行)
OPENAI_API_KEY=your-openai-api-key
```

### 完整配置示例

```env
# === 应用配置 ===
APP_ENV=production
LOG_LEVEL=INFO
SECRET_KEY=change-this-to-a-random-string-32-chars

# === 数据库 ===
DATABASE_URL=postgresql://postgres:strongpassword@db:5432/churgpt

# === Redis 缓存 ===
REDIS_URL=redis://redis:6379/0

# === AI API (可选) ===
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxx

# === MiniMax (国内替代) ===
MINIMAX_API_KEY=your-minimax-key
MINIMAX_BASE_URL=https://api.minimax.io/anthropic
```

## 部署架构

```
┌─────────────────┐
│   用户浏览器     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│   Nginx (80)    │────▶│  前端 (React)   │
│   (前端静态文件)  │     │  (Docker)       │
└─────────────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│   后端 API      │────▶│   FastAPI       │
│   (8000端口)    │     │   (Docker)      │
└─────────────────┘     └────────┬────────┘
         │                        │
         │         ┌──────────────┼──────────────┐
         │         ▼              ▼              ▼
         │    ┌─────────┐   ┌─────────┐   ┌─────────┐
         │    │PostgreSQL│   │  Redis  │   │ 文件存储 │
         │    │(DB)     │   │(Cache)  │   │(Uploads)│
         │    └─────────┘   └─────────┘   └─────────┘
         │
         ▼
┌─────────────────┐
│   AI 服务       │
│  (OpenAI等)     │
└─────────────────┘
```

## 数据持久化

Docker 部署会自动创建以下数据卷：

- `postgres_data` - PostgreSQL 数据库文件
- `redis_data` - Redis 缓存数据
- `./uploads` - 用户上传的文件

## 更新部署

```bash
# 拉取最新代码
git pull

# 重新部署
./deploy.sh prod

# 或者手动
docker-compose -f docker-compose.prod.yml up -d --build
```

## 查看日志

```bash
# 所有服务日志
docker-compose -f docker-compose.prod.yml logs -f

# 只看后端
docker-compose -f docker-compose.prod.yml logs -f backend

# 只看前端
docker-compose -f docker-compose.prod.yml logs -f frontend

# 只看数据库
docker-compose -f docker-compose.prod.yml logs -f db
```

## 备份数据

```bash
# 备份 PostgreSQL 数据库
docker-compose -f docker-compose.prod.yml exec db pg_dump -U postgres churgpt > backup.sql

# 备份上传文件
tar -czvf uploads-backup.tar.gz uploads/
```

## 恢复数据

```bash
# 恢复数据库
docker-compose -f docker-compose.prod.yml exec -T db psql -U postgres churgpt < backup.sql

# 恢复上传文件
tar -xzvf uploads-backup.tar.gz
```

## 故障排除

### 后端无法启动

```bash
# 检查日志
docker-compose logs backend

# 常见问题：
# 1. 数据库连接失败 - 检查 DATABASE_URL
# 2. 端口被占用 - 检查 8000 端口是否被占用
# 3. 依赖缺失 - 重新构建镜像
```

### 前端无法访问

```bash
# 检查前端容器
docker-compose logs frontend

# 常见问题：
# 1. 构建失败 - 检查 Node.js 版本
# 2. Nginx 配置错误 - 检查 nginx.conf
```

### 数据库迁移失败

```bash
# 手动运行迁移
docker-compose exec backend alembic upgrade head

# 查看迁移状态
docker-compose exec backend alembic current

# 回滚迁移
docker-compose exec backend alembic downgrade -1
```

## 性能优化

### 生产环境建议

1. **使用 Nginx 反向代理**
   - 启用 Gzip 压缩
   - 配置静态文件缓存
   - SSL/TLS 加密

2. **数据库优化**
   - 启用 PostgreSQL 连接池
   - 定期备份
   - 监控慢查询

3. **缓存策略**
   - 使用 Redis 缓存热点数据
   - 配置 API 响应缓存

4. **监控**
   - 添加日志收集 (ELK)
   - 性能监控 (Prometheus + Grafana)
   - 错误追踪 (Sentry)

## 安全建议

1. **必做事项**
   - [ ] 更改默认 SECRET_KEY
   - [ ] 使用强数据库密码
   - [ ] 启用 HTTPS (使用 Let's Encrypt)
   - [ ] 配置防火墙规则
   - [ ] 定期更新依赖

2. **环境隔离**
   - [ ] 开发/生产环境分离
   - [ ] 使用不同的数据库
   - [ ] 限制生产环境访问

## API 接口文档

部署完成后，访问以下地址查看 API 文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## 技术支持

如有问题，请检查：
1. 环境变量是否正确设置
2. 端口是否被占用
3. Docker 服务是否正常运行
4. 日志中的错误信息

## 系统要求

- **CPU**: 2+ cores (推荐 4+)
- **内存**: 4GB+ RAM (推荐 8GB+)
- **存储**: 20GB+ 可用空间
- **操作系统**: Linux/macOS/Windows with WSL2
- **Docker**: 20.10+ 
- **Docker Compose**: 2.0+
