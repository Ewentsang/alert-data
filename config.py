import os
from dotenv import load_dotenv

load_dotenv()

# 数据库配置
# 优先使用环境变量中的 DATABASE_URL
# 如果未设置，Docker 环境使用 PostgreSQL，本地开发使用 SQLite
if os.getenv("DATABASE_URL"):
    DATABASE_URL = os.getenv("DATABASE_URL")
else:
    # 判断是否在 Docker 环境（通过检查 /app 目录或 POSTGRES_HOST 环境变量）
    if os.path.exists("/app") or os.getenv("POSTGRES_HOST"):
        # Docker 环境，使用 PostgreSQL（需要从环境变量获取连接信息）
        postgres_user = os.getenv("POSTGRES_USER", "alert_user")
        postgres_password = os.getenv("POSTGRES_PASSWORD", "alert_password")
        postgres_host = os.getenv("POSTGRES_HOST", "postgres")
        postgres_port = os.getenv("POSTGRES_PORT", "5432")
        postgres_db = os.getenv("POSTGRES_DB", "alert_db")
        DATABASE_URL = f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}"
    else:
        # 本地开发环境，使用 SQLite
        default_db_path = "./alert_database.db"
        DATABASE_URL = f"sqlite:///{default_db_path}"

# Dify Workflow API 配置
DIFY_WEBHOOK_URL = os.getenv("DIFY_WEBHOOK_URL", "")  # 接收告警数据的 Dify workflow webhook
DIFY_WEBHOOK_URL_TIMEOUT = os.getenv("DIFY_WEBHOOK_URL_TIMEOUT", "")  # 20分钟超时后触发的 Dify workflow webhook
DIFY_API_KEY = os.getenv("DIFY_API_KEY", "")  # Dify API Key (Bearer Token)
DIFY_USER_ID = os.getenv("DIFY_USER_ID", "alert-system")  # Dify User ID (可选，默认值)

# 超时时间配置（分钟，支持小数，例如 0.167 表示 10 秒）
ALERT_TIMEOUT_MINUTES = float(os.getenv("ALERT_TIMEOUT_MINUTES", "25"))

# 检查间隔（秒）
CHECK_INTERVAL_SECONDS = int(os.getenv("CHECK_INTERVAL_SECONDS", "60"))

