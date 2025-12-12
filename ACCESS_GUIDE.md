# 服务访问指南

## 端口说明

### 1. `http://localhost:8000` - 后端 API 服务 ✅

这是 HTTP API 服务，可以通过浏览器或 HTTP 客户端访问。

**可用的路径：**

- **根路径（服务信息）**：`http://localhost:8000/`
  - 显示服务信息和所有可用端点
  
- **API 文档（Swagger UI）**：`http://localhost:8000/docs`
  - 交互式 API 文档，可以测试所有接口
  
- **ReDoc 文档**：`http://localhost:8000/redoc`
  - 另一种格式的 API 文档
  
- **健康检查**：`http://localhost:8000/health`
  - 返回 `{"status": "ok"}` 表示服务正常

- **API 端点**：
  - `POST /api/alert` - 创建告警
  - `GET /api/alerts` - 获取告警列表
  - `GET /api/alerts/{id}` - 获取单个告警

### 2. `localhost:5432` - PostgreSQL 数据库 ❌

**这个端口不能用浏览器访问！**

PostgreSQL 是数据库服务，不是 HTTP 服务。它使用 PostgreSQL 协议，需要通过数据库客户端工具连接。

**如何连接 PostgreSQL：**

#### 方式一：使用 Docker 命令连接
```bash
docker-compose exec postgres psql -U alert_user -d alert_db
```

#### 方式二：使用外部数据库客户端
- **DBeaver**：免费的数据库管理工具
- **pgAdmin**：PostgreSQL 官方管理工具
- **VS Code 插件**：PostgreSQL 扩展

连接信息：
- 主机：`localhost`
- 端口：`5432`
- 用户名：`alert_user`
- 密码：`alert_password`
- 数据库：`alert_db`

#### 方式三：使用 Python 脚本
```python
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    user="alert_user",
    password="alert_password",
    database="alert_db"
)
```

## 快速测试

### 1. 测试 API 服务是否运行

在浏览器访问：`http://localhost:8000/`

应该看到类似这样的 JSON 响应：
```json
{
  "service": "Alert Database API",
  "version": "1.0.0",
  "description": "告警数据库服务 API",
  "endpoints": { ... }
}
```

### 2. 查看 API 文档

访问：`http://localhost:8000/docs`

这里可以：
- 查看所有 API 端点
- 测试 API 接口
- 查看请求/响应格式

### 3. 测试健康检查

访问：`http://localhost:8000/health`

应该返回：`{"status": "ok"}`

### 4. 测试数据库连接

使用 Docker 命令：
```bash
docker-compose exec postgres psql -U alert_user -d alert_db -c "SELECT COUNT(*) FROM alerts;"
```

或者使用 Python 脚本（test_api.py）测试 API。

## 常见问题

### Q: 为什么 `localhost:5432` 打不开？

A: PostgreSQL 不是 Web 服务，它使用数据库协议。需要用数据库客户端工具连接。

### Q: 访问 `localhost:8000` 显示 "Not Found"？

A: 请访问 `/` 根路径或 `/docs` 文档页面。现在我已经添加了根路径，访问 `http://localhost:8000/` 会显示服务信息。

### Q: 如何查看服务日志？

```bash
# 查看所有服务日志
docker-compose logs -f

# 只看后端服务日志
docker-compose logs -f backend

# 只看数据库日志
docker-compose logs -f postgres
```

### Q: 如何重启服务？

```bash
# 重启所有服务
docker-compose restart

# 重启特定服务
docker-compose restart backend
docker-compose restart postgres
```


