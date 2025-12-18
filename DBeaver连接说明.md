# DBeaver 连接 PostgreSQL 配置说明

## 连接信息

根据 `docker-compose.yml` 配置，请按以下信息填写：

### 主要 (Main) 标签页

**连接方式 (Connection Method):**
- 选择 **"主机" (Host)**

**服务器设置 (Server Settings):**
- **主机 (Host):** `localhost`
- **端口 (Port):** `5432`
- **数据库 (Database):** `alert_db` ⚠️ **注意：不是 postgres**
- **显示所有数据库 (Show all databases):** 可选，如果需要可以勾选

**认证 (Authentication):**
- **认证方式 (Authentication):** `Database Native`（默认）
- **用户名 (Username):** `alert_user` ⚠️ **注意：不是 postgres**
- **密码 (Password):** `alert_password` ⚠️ **注意：填写密码**
- **保存密码 (Save password):** 建议勾选（方便下次使用）

### 连接前检查

1. **确保 Docker 服务正在运行**
   ```bash
   docker-compose ps
   ```
   应该看到 `postgres` 和 `backend` 两个服务都在运行。

2. **测试数据库是否可访问**
   ```bash
   docker-compose exec postgres psql -U alert_user -d alert_db -c "SELECT version();"
   ```

### 完整配置示例

```
连接方式: 主机
主机: localhost
端口: 5432
数据库: alert_db
用户名: alert_user
密码: alert_password
```

### 常见问题

**Q: 连接失败，提示认证失败？**
A: 检查用户名和密码是否正确：
   - 用户名：`alert_user`（不是 `postgres`）
   - 密码：`alert_password`

**Q: 连接失败，提示连接被拒绝？**
A: 检查：
   1. Docker 容器是否在运行：`docker-compose ps`
   2. PostgreSQL 端口是否开放：`docker-compose logs postgres`
   3. 主机和端口是否正确：`localhost:5432`

**Q: 找不到数据库 `alert_db`？**
A: 确保后端服务已经启动并初始化了数据库。可以运行：
   ```bash
   docker-compose logs backend
   ```
   查看是否有数据库初始化错误。

**Q: 如果端口 5432 被占用？**
A: 可以在 `docker-compose.yml` 中修改端口映射：
   ```yaml
   ports:
     - "5433:5432"  # 改为 5433，然后在 DBeaver 中使用 5433 端口
   ```



