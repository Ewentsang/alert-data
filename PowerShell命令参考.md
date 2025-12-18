# PowerShell 命令参考

在 Windows PowerShell 中，不能直接使用 Linux 的 `grep` 命令。以下是 PowerShell 的替代命令：

## 查看环境变量

### 方法 1：使用 Select-String（推荐）
```powershell
docker-compose exec backend env | Select-String "DIFY"
```

### 方法 2：使用 findstr
```powershell
docker-compose exec backend env | findstr "DIFY"
```

### 方法 3：直接在容器内执行
```powershell
docker-compose exec backend sh -c "env | grep DIFY"
```

## 查看日志

### 方法 1：使用 Select-String
```powershell
docker-compose logs backend | Select-String -Pattern "API_KEY|未配置" -CaseSensitive:$false
```

### 方法 2：使用 findstr
```powershell
docker-compose logs backend | findstr /i "API_KEY 未配置"
```

### 方法 3：查看最近的日志
```powershell
docker-compose logs backend --tail 50
```

## 其他常用命令

### 查看所有日志
```powershell
docker-compose logs backend
```

### 实时查看日志
```powershell
docker-compose logs -f backend
```

### 查看服务状态
```powershell
docker-compose ps
```

### 重启服务
```powershell
docker-compose restart backend
```


