# 告警数据库项目

这是一个用于管理和监控告警数据的后端服务，支持从 Dify workflow 接收告警数据，并在20分钟内未收到同类型告警时触发超时通知。

## 功能特性

- ✅ 接收来自 Dify workflow 的告警数据（告警触发和告警恢复）
- ✅ 自动解析告警消息中的结构化信息
- ✅ 存储告警数据到数据库
- ✅ 监控20分钟内未收到同企业、同话术、同告警类型的"告警触发"消息
- ✅ 自动触发超时后的 Dify workflow API
- ✅ RESTful API 接口查询告警数据

## 项目结构

```
alert_database/
├── main.py           # FastAPI 主应用
├── database.py       # 数据库模型和连接
├── models.py         # Pydantic 数据模型
├── parser.py         # 告警数据解析器
├── config.py         # 配置文件
├── requirements.txt  # Python 依赖
├── .env.example      # 环境变量示例
└── README.md         # 项目文档
```

## 安装和运行

### 方式一：使用 Docker（推荐，解决依赖问题）

**前置要求：** 安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/) 或 Docker Engine

**步骤：**

1. **创建环境变量文件**（如果需要自定义配置）：
   ```bash
   # Windows PowerShell
   Copy-Item env_template.txt .env
   
   # Linux/Mac
   cp env_template.txt .env
   ```
   然后编辑 `.env` 文件，设置 `DIFY_WEBHOOK_URL_TIMEOUT` 等配置。

2. **快速启动（推荐）**：
   
   Windows 用户：
   ```bash
   docker-run.bat
   ```
   
   Linux/Mac 用户：
   ```bash
   chmod +x docker-run.sh
   ./docker-run.sh
   ```
   
   或者手动使用 docker-compose：
   ```bash
   docker-compose up -d --build
   ```

3. **或者使用 Docker 命令**：
   ```bash
   # 构建镜像
   docker build -t alert-database .
   
   # 运行容器
   docker run -d \
     --name alert_database \
     -p 8000:8000 \
     -v $(pwd)/data:/app/data \
     --env-file .env \
     alert-database
   ```

4. **查看日志**：
   ```bash
   docker-compose logs -f
   # 或
   docker logs -f alert_database
   ```

5. **停止服务**：
   ```bash
   docker-compose down
   # 或
   docker stop alert_database
   ```

服务将在 `http://localhost:8000` 启动。

**服务说明：**
- **PostgreSQL 数据库服务**：端口 5432，数据持久化到 Docker volume `postgres_data`
- **后端 API 服务**：端口 8000，负责读写数据库和处理告警逻辑

**数据持久化：** PostgreSQL 数据保存在 Docker volume 中，即使删除容器也不会丢失数据。

**查看服务状态：**
```bash
# 查看所有服务状态
docker-compose ps

# 查看 PostgreSQL 日志
docker-compose logs postgres

# 查看后端服务日志
docker-compose logs backend
```

---

### 方式二：本地安装

### 1. 安装依赖

**方法一：使用国内镜像源（推荐，解决网络问题）**

Windows 用户可以直接运行：
```bash
install_dependencies.bat
```

或者手动使用镜像源：
```bash
# 使用清华镜像源
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# 如果清华源失败，可以尝试阿里云镜像源
pip install -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt
```

**方法二：直接安装（如果网络良好）**

```bash
pip install -r requirements.txt
```

**如果遇到 pydantic-core 安装失败：**

1. 确保网络连接稳定
2. 使用国内镜像源（推荐清华或阿里云）
3. 可以尝试升级 pip：
   ```bash
   python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```

### 2. 配置环境变量

**注意：** 如果使用 Docker，可以跳过此步骤，直接使用 docker-compose.yml 中的环境变量或 .env 文件。

复制 `.env.example` 为 `.env` 并填写配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# 数据库配置（默认使用 SQLite）
DATABASE_URL=sqlite:///./alert_database.db

# Dify Workflow API 配置
DIFY_WEBHOOK_URL=https://api.dify.ai/v1/workflows/run  # 接收告警数据的 webhook（可选）
DIFY_WEBHOOK_URL_TIMEOUT=https://api.dify.ai/v1/workflows/timeout  # 20分钟超时后触发的 webhook

# 超时时间配置（分钟）
ALERT_TIMEOUT_MINUTES=20

# 检查间隔（秒）
CHECK_INTERVAL_SECONDS=60
```

### 3. 运行服务

```bash
python main.py
```

或者使用 uvicorn：

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

服务将在 `http://localhost:8000` 启动。

## API 接口

### 1. 接收告警数据

**POST** `/api/alert`

接收来自 Dify workflow 的告警数据。

**请求体：**

```json
{
  "input": "🔴 **【告警触发】监控告警**\n🌐 **区域 (Region):** IDN\n...",
  "enterprise_name": "KrediOne CG",
  "time": "2025-12-10 10:25:34"
}
```

**响应：**

```json
{
  "id": 1,
  "alert_type": "告警触发",
  "enterprise_name": "KrediOne CG",
  "metric": "ConnectionRate",
  "rule_name": "IDN-Enterprise-ConnectionRate",
  "time": "2025-12-10T10:25:34",
  "processed": false,
  "timeout_triggered": false
}
```

### 2. 查询告警列表

**GET** `/api/alerts`

查询告警列表，支持过滤和分页。

**查询参数：**
- `enterprise_name` (可选): 按企业名称过滤
- `alert_type` (可选): 按告警类型过滤（"告警触发" 或 "告警恢复"）
- `skip` (可选, 默认 0): 跳过条数
- `limit` (可选, 默认 100): 返回条数

### 3. 查询单个告警

**GET** `/api/alerts/{alert_id}`

查询单个告警的详细信息。

### 4. 健康检查

**GET** `/health`

检查服务健康状态。

## 工作流程

1. **接收告警数据**
   - Dify workflow 调用 `/api/alert` 接口
   - 系统解析告警消息，提取结构化信息
   - 将数据存储到数据库

2. **监控超时**
   - 当收到"告警触发"消息时，启动20分钟倒计时
   - 如果在20分钟内收到同企业、同话术、同告警类型的"告警触发"消息，则取消超时通知
   - 如果20分钟内未收到，则触发超时 Dify workflow API

3. **定期检查**
   - 后台任务每隔60秒检查一次所有未处理的告警
   - 确保不会遗漏超时通知

## 数据库

项目使用 **PostgreSQL** 作为数据库（Docker 环境）或 **SQLite**（本地开发环境）。

### 连接数据库

**Docker 环境连接 PostgreSQL：**
```bash
# 使用 psql 连接
docker-compose exec postgres psql -U alert_user -d alert_db

# 或者从外部连接（如果需要）
psql -h localhost -p 5432 -U alert_user -d alert_db
```

**数据库连接信息（Docker）：**
- 主机：`postgres` (容器内) 或 `localhost` (外部)
- 端口：`5432`
- 用户名：`alert_user`
- 密码：`alert_password`
- 数据库名：`alert_db`

### 数据库模型

### Alert 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| alert_type | String | 告警类型（"告警触发" 或 "告警恢复"） |
| region | String | 区域 |
| metric | String | 指标 |
| rule_name | String | 规则名称 |
| generator_url | Text | 告警链接 |
| alert_summary | Text | 告警摘要 |
| alert_details | Text | 告警详情 |
| enterprise_name | String | 企业名称 |
| script_name | String | 话术名称 |
| time | DateTime | 告警时间 |
| raw_input | Text | 原始 input 字段 |
| processed | Boolean | 是否已处理 |
| timeout_triggered | Boolean | 是否已触发超时通知 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

## 注意事项

1. **话术名称提取**：系统会尝试从告警摘要中提取话术名称。如果提取失败，`script_name` 可能为 `None`。

2. **超时判断逻辑**：
   - 当收到"告警触发"时，启动 20 分钟倒计时
   - 如果在 20 分钟内收到同 `enterprise_name` 和 `alert_key` 的"告警恢复"，则取消超时通知
   - 如果 20 分钟内没有收到匹配的"告警恢复"，则触发超时通知
   - 一个"告警恢复"可以取消多个匹配的"告警触发"的超时通知

3. **数据库选择**：默认使用 SQLite，生产环境建议使用 PostgreSQL。修改 `.env` 中的 `DATABASE_URL` 即可。

## 开发

### 代码检查

```bash
# 安装开发依赖（可选）
pip install black flake8

# 格式化代码
black .

# 检查代码风格
flake8 .
```

## 许可证

MIT

