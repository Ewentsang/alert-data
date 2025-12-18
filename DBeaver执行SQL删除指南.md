# DBeaver 执行 SQL 删除指南

## 步骤 1：连接数据库

如果还没有连接，请参考 `DBeaver连接说明.md` 进行配置：

- **主机：** `localhost`
- **端口：** `5432`（注意：docker-compose.yml 中映射的是 5436:5432，但容器内是 5432）
- **数据库：** `alert_db`
- **用户名：** `alert_user`
- **密码：** `alert_password`

## 步骤 2：打开 SQL 编辑器

### 方法 1：通过菜单
1. 右键点击数据库连接 → **SQL 编辑器** → **新建 SQL 脚本**
2. 或点击顶部菜单：**SQL 编辑器** → **新建 SQL 脚本**

### 方法 2：快捷键
- **Windows/Linux：** `Ctrl + \` 或 `Ctrl + Alt + S`
- **Mac：** `Cmd + \` 或 `Cmd + Alt + S`

### 方法 3：右键表
1. 在数据库导航器中找到 `alerts` 表
2. 右键点击 → **查看数据** → 在数据查看器中点击 **SQL** 标签

## 步骤 3：执行删除 SQL

### 方案 A：模拟定时删除任务的逻辑（推荐）

这个 SQL 会按照代码中的逻辑删除旧数据：

```sql
-- 设置时区为北京时间
SET timezone = 'Asia/Shanghai';

-- 开始事务（可以回滚）
BEGIN;

-- 查看将要删除的数据（先查询，确认后再删除）
SELECT 
    COUNT(*) as total_to_delete,
    COUNT(CASE WHEN time < (CURRENT_DATE AT TIME ZONE 'Asia/Shanghai')::timestamp - INTERVAL '25 minutes' THEN 1 END) as before_23_35,
    COUNT(CASE WHEN time >= (CURRENT_DATE AT TIME ZONE 'Asia/Shanghai')::timestamp - INTERVAL '25 minutes' 
              AND time < (CURRENT_DATE AT TIME ZONE 'Asia/Shanghai')::timestamp 
              AND (timeout_triggered = true OR processed = true) THEN 1 END) as after_23_35_processed
FROM alerts
WHERE time < (CURRENT_DATE AT TIME ZONE 'Asia/Shanghai')::timestamp
AND NOT (
    time >= (CURRENT_DATE AT TIME ZONE 'Asia/Shanghai')::timestamp - INTERVAL '25 minutes'
    AND time < (CURRENT_DATE AT TIME ZONE 'Asia/Shanghai')::timestamp
    AND timeout_triggered = false
    AND processed = false
);

-- 如果确认无误，执行删除
-- 删除条件1：昨天 23:35 之前的所有数据
DELETE FROM alerts 
WHERE time < (CURRENT_DATE AT TIME ZONE 'Asia/Shanghai')::timestamp - INTERVAL '25 minutes';

-- 删除条件2：昨天 23:35-00:00 之间，但已处理或已超时的数据
DELETE FROM alerts 
WHERE time >= (CURRENT_DATE AT TIME ZONE 'Asia/Shanghai')::timestamp - INTERVAL '25 minutes'
  AND time < (CURRENT_DATE AT TIME ZONE 'Asia/Shanghai')::timestamp
  AND (timeout_triggered = true OR processed = true);

-- 查看删除结果
SELECT COUNT(*) as remaining_count FROM alerts;

-- 提交事务（如果确认删除正确）
COMMIT;

-- 如果发现删除错误，可以回滚
-- ROLLBACK;
```

### 方案 B：删除指定日期的数据

```sql
-- 删除 2025-12-11 的所有数据（示例）
DELETE FROM alerts 
WHERE DATE(time AT TIME ZONE 'Asia/Shanghai') = '2025-12-11';

-- 查看删除结果
SELECT COUNT(*) FROM alerts;
```

### 方案 C：删除指定日期之前的所有数据

```sql
-- 删除 2025-12-12 之前的所有数据（示例）
DELETE FROM alerts 
WHERE time < '2025-12-12 00:00:00'::timestamp;

-- 查看删除结果
SELECT COUNT(*) FROM alerts;
```

### 方案 D：删除单个记录

```sql
-- 删除指定 ID 的记录
DELETE FROM alerts WHERE id = 10;

-- 查看删除结果
SELECT * FROM alerts WHERE id = 10;  -- 应该返回空
```

### 方案 E：删除已处理或已超时的记录

```sql
-- 删除所有已处理或已超时的记录
DELETE FROM alerts 
WHERE processed = true OR timeout_triggered = true;

-- 查看删除结果
SELECT COUNT(*) FROM alerts;
```

## 步骤 4：执行 SQL

### 方法 1：执行整个脚本
- 点击工具栏的 **执行 SQL 脚本** 按钮（▶️ 图标）
- 或按快捷键：**Ctrl + Enter**（Windows/Linux）或 **Cmd + Enter**（Mac）

### 方法 2：执行选中的 SQL
1. 选中要执行的 SQL 语句
2. 按 **Ctrl + Enter**（Windows/Linux）或 **Cmd + Enter**（Mac）
3. 或右键 → **执行 SQL 语句**

### 方法 3：执行当前光标所在语句
- 将光标放在 SQL 语句中
- 按 **Ctrl + Enter**（Windows/Linux）或 **Cmd + Enter**（Mac）

## 步骤 5：查看执行结果

执行后，在 **结果** 标签页中可以看到：
- 删除的记录数（如：`DELETE 5`）
- 查询结果（如果执行了 SELECT）

## 安全建议

### ⚠️ 删除前先查询

**强烈建议：** 在执行 DELETE 之前，先用 SELECT 查看将要删除的数据：

```sql
-- 1. 先查询，看看会删除哪些数据
SELECT * FROM alerts 
WHERE time < (CURRENT_DATE AT TIME ZONE 'Asia/Shanghai')::timestamp - INTERVAL '25 minutes'
ORDER BY time DESC;

-- 2. 确认无误后，再执行删除
DELETE FROM alerts 
WHERE time < (CURRENT_DATE AT TIME ZONE 'Asia/Shanghai')::timestamp - INTERVAL '25 minutes';
```

### ⚠️ 使用事务

使用 `BEGIN` 和 `COMMIT`/`ROLLBACK` 可以确保安全：

```sql
BEGIN;  -- 开始事务

DELETE FROM alerts WHERE ...;  -- 执行删除

-- 检查结果
SELECT COUNT(*) FROM alerts;

-- 如果确认无误
COMMIT;

-- 如果发现错误，可以回滚
-- ROLLBACK;
```

### ⚠️ 备份重要数据

删除前可以导出数据：

1. 在 DBeaver 中右键 `alerts` 表
2. 选择 **导出数据**
3. 选择格式（CSV、SQL、Excel 等）
4. 保存备份文件

## 常用查询 SQL（删除前检查）

### 查看数据统计

```sql
-- 按日期统计
SELECT 
    DATE(time AT TIME ZONE 'Asia/Shanghai') as date,
    COUNT(*) as count,
    COUNT(CASE WHEN processed = true THEN 1 END) as processed,
    COUNT(CASE WHEN timeout_triggered = true THEN 1 END) as timeout
FROM alerts
GROUP BY DATE(time AT TIME ZONE 'Asia/Shanghai')
ORDER BY date DESC;
```

### 查看将要删除的数据

```sql
-- 查看今天之前的所有数据
SELECT 
    id,
    enterprise_name,
    om_type,
    time,
    processed,
    timeout_triggered
FROM alerts
WHERE time < (CURRENT_DATE AT TIME ZONE 'Asia/Shanghai')::timestamp
ORDER BY time DESC;
```

### 查看保留窗口内的数据

```sql
-- 查看昨天 23:35 之后的数据（应该保留的）
SELECT 
    id,
    enterprise_name,
    om_type,
    time,
    processed,
    timeout_triggered
FROM alerts
WHERE time >= (CURRENT_DATE AT TIME ZONE 'Asia/Shanghai')::timestamp - INTERVAL '25 minutes'
  AND time < (CURRENT_DATE AT TIME ZONE 'Asia/Shanghai')::timestamp
ORDER BY time DESC;
```

## 完整示例：执行定时删除逻辑

```sql
-- ============================================
-- 定时删除旧数据（模拟代码中的 delete_old_alerts 函数）
-- ============================================

-- 设置时区
SET timezone = 'Asia/Shanghai';

-- 开始事务
BEGIN;

-- 1. 查看当前数据统计
SELECT 
    '删除前统计' as status,
    COUNT(*) as total,
    COUNT(CASE WHEN time < (CURRENT_DATE AT TIME ZONE 'Asia/Shanghai')::timestamp THEN 1 END) as old_data,
    COUNT(CASE WHEN time >= (CURRENT_DATE AT TIME ZONE 'Asia/Shanghai')::timestamp - INTERVAL '25 minutes'
              AND time < (CURRENT_DATE AT TIME ZONE 'Asia/Shanghai')::timestamp
              AND timeout_triggered = false
              AND processed = false THEN 1 END) as to_keep
FROM alerts;

-- 2. 查看将要删除的数据详情
SELECT 
    id,
    enterprise_name,
    om_type,
    time,
    processed,
    timeout_triggered,
    CASE 
        WHEN time < (CURRENT_DATE AT TIME ZONE 'Asia/Shanghai')::timestamp - INTERVAL '25 minutes' THEN '条件1：23:35之前'
        WHEN time >= (CURRENT_DATE AT TIME ZONE 'Asia/Shanghai')::timestamp - INTERVAL '25 minutes'
         AND time < (CURRENT_DATE AT TIME ZONE 'Asia/Shanghai')::timestamp
         AND (timeout_triggered = true OR processed = true) THEN '条件2：23:35后已处理'
        ELSE '保留'
    END as delete_reason
FROM alerts
WHERE time < (CURRENT_DATE AT TIME ZONE 'Asia/Shanghai')::timestamp
AND NOT (
    time >= (CURRENT_DATE AT TIME ZONE 'Asia/Shanghai')::timestamp - INTERVAL '25 minutes'
    AND time < (CURRENT_DATE AT TIME ZONE 'Asia/Shanghai')::timestamp
    AND timeout_triggered = false
    AND processed = false
)
ORDER BY time DESC;

-- 3. 执行删除（条件1）
DELETE FROM alerts 
WHERE time < (CURRENT_DATE AT TIME ZONE 'Asia/Shanghai')::timestamp - INTERVAL '25 minutes';

-- 4. 执行删除（条件2）
DELETE FROM alerts 
WHERE time >= (CURRENT_DATE AT TIME ZONE 'Asia/Shanghai')::timestamp - INTERVAL '25 minutes'
  AND time < (CURRENT_DATE AT TIME ZONE 'Asia/Shanghai')::timestamp
  AND (timeout_triggered = true OR processed = true);

-- 5. 查看删除后统计
SELECT 
    '删除后统计' as status,
    COUNT(*) as remaining_count
FROM alerts;

-- 6. 提交事务（确认无误后）
COMMIT;

-- 如果发现错误，可以回滚
-- ROLLBACK;
```

## 注意事项

1. **端口问题：** 如果使用 docker-compose，注意端口映射是 `5436:5432`，但容器内 PostgreSQL 监听的是 5432 端口。如果从外部连接，需要使用映射后的端口 5436。

2. **时区问题：** 确保 SQL 中使用 `AT TIME ZONE 'Asia/Shanghai'` 来处理时区。

3. **权限问题：** 确保 `alert_user` 有 DELETE 权限（通常创建表时自动拥有）。

4. **数据备份：** 删除前建议先导出数据作为备份。

## 快速操作流程

1. **打开 DBeaver** → 连接到数据库
2. **打开 SQL 编辑器** → `Ctrl + \`
3. **粘贴 SQL** → 先执行 SELECT 查看数据
4. **确认无误** → 执行 DELETE
5. **查看结果** → 确认删除成功

