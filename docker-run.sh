#!/bin/bash

# Docker 快速运行脚本

echo "开始构建和运行告警数据库服务..."
echo "这将启动两个服务：PostgreSQL 数据库和后端 API 服务"

# 创建数据目录
mkdir -p data

# 检查是否有 .env 文件
if [ ! -f .env ]; then
    echo "警告: 未找到 .env 文件，将使用默认配置"
    echo "建议复制 env_template.txt 为 .env 并配置 DIFY_WEBHOOK_URL_TIMEOUT"
fi

# 使用 docker-compose 启动
docker-compose up -d --build

echo ""
echo "服务已启动！"
echo "访问地址: http://localhost:8000"
echo "API 文档: http://localhost:8000/docs"
echo ""
echo "查看日志: docker-compose logs -f"
echo "停止服务: docker-compose down"

