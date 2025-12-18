# Dify Workflow 配置指南

本指南详细说明如何在 Dify Workflow 中配置 HTTP 请求节点，将"告警触发"和"告警恢复"数据发送到告警数据库。

## 📋 前置条件

1. **确保告警数据库服务已启动**
   - 本地测试：`http://localhost:8000`
   - 生产环境：`http://your-server-ip:8000` 或 `http://your-domain.com:8000`

2. **测试服务是否可用**
   ```bash
   curl http://localhost:8000/health
   ```
   应该返回：`{"status": "ok"}`

---

## 🔧 在 Dify 中配置 HTTP 请求节点

### 步骤 1：添加 HTTP 请求节点

1. 在 Dify Workflow 编辑器中，找到需要发送告警数据的位置
2. 添加一个 **HTTP Request** 节点（或类似的 HTTP 调用节点）
3. 将节点连接到你的工作流中

### 步骤 2：配置请求参数

#### 2.1 基本配置

- **URL**: 
  - 本地测试：`http://localhost:8000/api/alert`
  - 生产环境：`http://your-server-ip:8000/api/alert`
  - 或使用环境变量：`{{API_BASE_URL}}/api/alert`

- **请求方法**: `POST`

- **Headers**:
  ```
  Content-Type: application/json
  ```

#### 2.2 请求体配置（JSON 格式）

在 Dify 的 HTTP 请求节点中，配置请求体为 JSON 格式，使用变量引用：

```json
{
  "input": "{{alert_message}}",
  "enterprise_name": "{{enterprise_name}}",
  "time": "{{alert_time}}",
  "alert_type": "{{alert_type}}",
  "template_name": "{{template_name}}",
  "om_type": "{{om_type}}",
  "alert_key": "{{alert_key}}"
}
```

---

## 📝 字段说明和变量映射

### 必需字段

| 字段名 | 类型 | 说明 | Dify 变量示例 |
|--------|------|------|---------------|
| `input` | string | 告警消息的完整文本内容 | `{{alert_message}}` 或 `{{input}}` |
| `enterprise_name` | string | 企业名称 | `{{enterprise_name}}` |
| `time` | string | 告警时间，格式：`YYYY-MM-DD HH:MM:SS` | `{{alert_time}}` 或 `{{time}}` |
| `alert_type` | string | 告警类型：`"告警触发"` 或 `"告警恢复"` | `{{alert_type}}` |
| `template_name` | string | 模板名称/话术名称 | `{{template_name}}` |
| `om_type` | string | OM 类型（如 `ConnectionRate`） | `{{om_type}}` |
| `alert_key` | string | 告警唯一标识键 | `{{alert_key}}` |

### 字段详细说明

#### 1. `input` - 告警消息内容
完整的告警消息文本，通常包含：
- 告警类型标识（【告警触发】或【告警恢复】）
- 区域信息
- 指标信息
- 规则名称
- 告警链接
- 告警摘要
- 告警详情

**示例**：
```
🔴 **【告警触发】监控告警**
🌐 **区域 (Region):** IDN
📊 **指标 (Metric):** ConnectionRate
🔍 **规则名称 (Rule Name):** IDN-Enterprise-ConnectionRate
🔗 **告警链接 (GeneratorURL):** https://monitor.example.com/alert/xxx

**告警摘要:**
企业 KrediOne CG 的接通率

**告警详情:**
在过去十五分钟内的接通率为 14.03%
呼叫量为 2776
参考阈值: 0.5%~20%
```

#### 2. `enterprise_name` - 企业名称
例如：`KrediOne CG`、`Finture`

#### 3. `time` - 告警时间
格式必须为：`YYYY-MM-DD HH:MM:SS`

**示例**：`2025-12-10 10:25:34`

**在 Dify 中格式化时间**：
如果原始时间是其他格式，可以使用代码节点或函数节点转换：
```python
# 示例：将时间戳转换为格式化的时间字符串
from datetime import datetime
formatted_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
```

#### 4. `alert_type` - 告警类型
必须是以下两个值之一：
- `"告警触发"` - 表示告警开始
- `"告警恢复"` - 表示告警恢复

**在 Dify 中判断**：
```python
# 示例：根据消息内容判断告警类型
if "【告警触发】" in alert_message:
    alert_type = "告警触发"
elif "【告警恢复】" in alert_message:
    alert_type = "告警恢复"
else:
    alert_type = "告警触发"  # 默认值
```

#### 5. `template_name` - 模板名称
话术名称或模板名称，例如：`KrediOne`、`Finture`

#### 6. `om_type` - OM 类型
监控指标类型，例如：`ConnectionRate`、`AnswerRate`

#### 7. `alert_key` - 告警唯一标识
建议格式：`{enterprise_name}_{template_name}_{om_type}_{timestamp}`

**示例**：`KrediOne_CG_ConnectionRate_20251210_102534`

**在 Dify 中生成**：
```python
# 示例：生成告警唯一标识
from datetime import datetime
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
alert_key = f"{enterprise_name}_{template_name}_{om_type}_{timestamp}"
```

---

## 🎯 完整配置示例

### 示例 1：告警触发

假设你的 Dify Workflow 中已有以下变量：
- `alert_message` - 告警消息内容
- `enterprise` - 企业名称
- `template` - 模板名称
- `metric` - 指标类型

**HTTP 请求节点配置**：

**URL**: `http://localhost:8000/api/alert`

**Method**: `POST`

**Headers**:
```
Content-Type: application/json
```

**Body** (JSON):
```json
{
  "input": "{{alert_message}}",
  "enterprise_name": "{{enterprise}}",
  "time": "{{$timestamp}}",
  "alert_type": "告警触发",
  "template_name": "{{template}}",
  "om_type": "{{metric}}",
  "alert_key": "{{enterprise}}_{{template}}_{{metric}}_{{$timestamp}}"
}
```

### 示例 2：告警恢复

**Body** (JSON):
```json
{
  "input": "{{alert_message}}",
  "enterprise_name": "{{enterprise}}",
  "time": "{{$timestamp}}",
  "alert_type": "告警恢复",
  "template_name": "{{template}}",
  "om_type": "{{metric}}",
  "alert_key": "{{enterprise}}_{{template}}_{{metric}}_{{$timestamp}}"
}
```

### 示例 3：使用代码节点处理数据

如果需要在发送前处理数据，可以在 HTTP 请求节点前添加一个 **Code** 节点：

**Code 节点示例**：
```python
from datetime import datetime

# 从上游节点获取数据
alert_message = "{{alert_message}}"
enterprise = "{{enterprise}}"
template = "{{template}}"
metric = "{{metric}}"

# 判断告警类型
if "【告警触发】" in alert_message:
    alert_type = "告警触发"
elif "【告警恢复】" in alert_message:
    alert_type = "告警恢复"
else:
    alert_type = "告警触发"

# 格式化时间
current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 生成告警唯一标识
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
alert_key = f"{enterprise}_{template}_{metric}_{timestamp}"

# 输出变量供下游节点使用
output = {
    "input": alert_message,
    "enterprise_name": enterprise,
    "time": current_time,
    "alert_type": alert_type,
    "template_name": template,
    "om_type": metric,
    "alert_key": alert_key
}
```

然后在 HTTP 请求节点中使用：
```json
{
  "input": "{{output.input}}",
  "enterprise_name": "{{output.enterprise_name}}",
  "time": "{{output.time}}",
  "alert_type": "{{output.alert_type}}",
  "template_name": "{{output.template_name}}",
  "om_type": "{{output.om_type}}",
  "alert_key": "{{output.alert_key}}"
}
```

---

## 🔍 测试配置

### 方法 1：在 Dify 中测试

1. 在 Dify Workflow 编辑器中，点击"运行"或"测试"
2. 提供测试数据
3. 查看 HTTP 请求节点的响应
4. 成功响应应该返回：
```json
{
  "id": 1,
  "input": "...",
  "enterprise_name": "...",
  "time": "2025-12-10T10:25:34",
  "alert_type": "告警触发",
  "template_name": "...",
  "om_type": "...",
  "alert_key": "...",
  "processed": false,
  "timeout_triggered": false
}
```

### 方法 2：使用 curl 测试

```bash
curl -X POST "http://localhost:8000/api/alert" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "🔴 **【告警触发】监控告警**\n🌐 **区域 (Region):** IDN\n📊 **指标 (Metric):** ConnectionRate",
    "enterprise_name": "KrediOne CG",
    "time": "2025-12-10 10:25:34",
    "alert_type": "告警触发",
    "template_name": "KrediOne",
    "om_type": "ConnectionRate",
    "alert_key": "KrediOne_CG_ConnectionRate_20251210_102534"
  }'
```

### 方法 3：查看数据库

启动服务后，访问 API 文档页面：`http://localhost:8000/docs`

在 Swagger UI 中测试 `POST /api/alert` 接口。

---

## ⚠️ 常见问题

### 1. 连接失败

**问题**：无法连接到 `http://localhost:8000`

**解决方案**：
- 确保告警数据库服务已启动
- 检查端口 8000 是否被占用
- 如果 Dify 和数据库服务不在同一台机器，使用服务器 IP 地址而不是 `localhost`

### 2. 时间格式错误

**问题**：返回 422 错误，提示时间格式不正确

**解决方案**：
- 确保时间格式为：`YYYY-MM-DD HH:MM:SS`
- 使用代码节点格式化时间：
  ```python
  from datetime import datetime
  formatted_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  ```

### 3. 告警类型不匹配

**问题**：超时监控不工作

**解决方案**：
- 确保 `alert_type` 字段的值严格为 `"告警触发"` 或 `"告警恢复"`（包含引号）
- 检查是否有额外的空格或字符

### 4. 变量未定义

**问题**：Dify 提示变量不存在

**解决方案**：
- 检查变量名是否正确
- 确保上游节点已输出该变量
- 使用代码节点处理数据，确保所有必需字段都有值

---

## 📚 参考资源

- API 文档：`http://localhost:8000/docs`
- 测试脚本：`test_api.py`
- 项目 README：`README.md`

---

## 🎉 完成配置后

配置完成后，你的 Dify Workflow 将能够：
1. ✅ 自动将"告警触发"和"告警恢复"数据发送到数据库
2. ✅ 系统会自动监控 20 分钟超时
3. ✅ 可以通过 API 查询告警数据

查询告警数据：
```bash
# 查询所有告警
curl http://localhost:8000/api/alerts

# 查询特定企业的告警
curl http://localhost:8000/api/alerts?enterprise_name=KrediOne%20CG

# 查询告警触发
curl http://localhost:8000/api/alerts?alert_type=告警触发
```


