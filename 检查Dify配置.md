# 检查 Dify Webhook URL 配置

## 配置要求

### DIFY_WEBHOOK_URL_TIMEOUT 格式

这个配置应该是**完整的 HTTP/HTTPS URL**，用于发送 POST 请求。

**正确的格式示例：**

1. **Dify API 格式**：
   ```
   https://api.dify.ai/v1/workflows/run?user_id=xxx&api_key=xxx
   ```

2. **Dify Webhook 格式**：
   ```
   https://api.dify.ai/v1/workflows/webhook/xxx?user_id=xxx&api_key=xxx
   ```

3. **自定义 Webhook URL**：
   ```
   https://your-domain.com/webhook/timeout
   ```

**错误的格式：**
- ❌ `app-TcJyn` - 这只是应用 ID，不是完整 URL
- ❌ `app-Ixxx` - 这只是部分标识，不是完整 URL
- ❌ `dify-workflow-123` - 缺少协议和域名

## 如何获取正确的 URL

### 方法 1：从 Dify 工作流获取

1. 在 Dify 中打开你的工作流
2. 找到 **HTTP 请求节点** 或 **Webhook 节点**
3. 复制完整的 URL（包括 `https://` 和所有参数）

### 方法 2：Dify API 格式

如果你使用的是 Dify API，格式应该是：
```
https://api.dify.ai/v1/workflows/run?user_id={user_id}&api_key={api_key}
```

或者：
```
https://api.dify.ai/v1/workflows/{workflow_id}/run?user_id={user_id}&api_key={api_key}
```

### 方法 3：检查 Dify 文档

查看 Dify 的官方文档，确认正确的 API 端点格式。

## 检查当前配置

### 步骤 1：查看 .env 文件

```bash
# 查看配置
cat .env | grep DIFY_WEBHOOK_URL
```

### 步骤 2：检查服务中的环境变量

```bash
# 查看 Docker 容器中的环境变量
docker-compose exec backend env | grep DIFY_WEBHOOK_URL
```

### 步骤 3：测试 URL 是否有效

```bash
# 测试超时 webhook URL（需要替换为实际值）
curl -X POST "你的_DIFY_WEBHOOK_URL_TIMEOUT" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "测试",
    "enterprise_name": "测试企业",
    "time": "2025-12-11 14:00:00"
  }'
```

## 常见问题

### Q1: 配置看起来不完整怎么办？

**A**: 如果配置值像 `app-TcJyn` 或 `app-Ixxx`，这可能是：
1. 应用 ID 而不是完整 URL
2. URL 被截断了
3. 需要添加完整的前缀

**解决方案**：
- 检查 Dify 工作流设置，获取完整的 webhook URL
- 确保包含 `https://` 协议
- 确保包含所有必需的参数（如 `api_key`、`user_id` 等）

### Q2: 如何确认 URL 是否正确？

**A**: 
1. URL 应该以 `http://` 或 `https://` 开头
2. 应该包含完整的域名
3. 如果使用 Dify API，应该包含认证参数

### Q3: 配置错误会有什么影响？

**A**: 
- 如果 `DIFY_WEBHOOK_URL_TIMEOUT` 未配置或格式错误：
  - 超时通知不会发送
  - 但 `timeout_triggered` 字段仍然会更新为 `True`
  - 日志中会显示警告：`未配置 DIFY_WEBHOOK_URL_TIMEOUT，无法触发超时通知`

## 正确的配置示例

```env
# Dify Workflow API 配置
# 接收告警数据的 Dify workflow webhook（可选）
DIFY_WEBHOOK_URL=https://api.dify.ai/v1/workflows/run?user_id=your_user_id&api_key=your_api_key

# 20分钟超时后触发的 Dify workflow webhook（必需）
DIFY_WEBHOOK_URL_TIMEOUT=https://api.dify.ai/v1/workflows/run?user_id=your_user_id&api_key=your_api_key

# 或者使用 webhook 格式
DIFY_WEBHOOK_URL_TIMEOUT=https://api.dify.ai/v1/workflows/webhook/your_webhook_id?user_id=your_user_id&api_key=your_api_key
```

## 验证配置

配置完成后：

1. **重启服务**：
   ```bash
   docker-compose restart backend
   ```

2. **查看日志**，确认配置已加载：
   ```bash
   docker-compose logs backend | grep -i "DIFY_WEBHOOK_URL_TIMEOUT\|未配置"
   ```

3. **测试超时触发**，查看日志中是否有错误：
   ```bash
   docker-compose logs -f backend | grep -i "超时\|timeout\|workflow"
   ```


