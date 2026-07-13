"""配置管理 —— 所有敏感信息从环境变量读取"""
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from dotenv import load_dotenv

_BACKEND_ROOT = Path(__file__).parent.parent

# 自动加载 kaiwuback/.env.local 和 kaiwuback/.env；系统环境变量优先。
for _env_name in (".env.local", ".env"):
    _env_path = _BACKEND_ROOT / _env_name
    if _env_path.exists():
        load_dotenv(_env_path, override=False)


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value in (None, ""):
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value in (None, ""):
        return default
    return value.strip().lower() not in ("0", "false", "no", "off")

# ═══════════════════════════════════════
# DeepSeek 客户端
# ═══════════════════════════════════════
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"           # 默认：快速稳定，用于意图识别和一般对话
DEEPSEEK_REASONING_MODEL = "deepseek-v4-pro"  # 推理模型：用于深度分析和策略推演

# ═══════════════════════════════════════
# 豆包 Seed 模型
# ═══════════════════════════════════════
DOUBAO_API_KEY = os.getenv("DOUBAO_API_KEY", "")
DOUBAO_URL = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
DOUBAO_MODEL = "doubao-seed-2-0-lite-260215"
REPORT_MODEL = "doubao-seed-2-1-pro-260628"

# ═══════════════════════════════════════
# 火山方舟 文生图（Node3）
# ═══════════════════════════════════════
SEEDREAM_API_KEY = os.getenv("SEEDREAM_API_KEY", "")
SEEDREAM_URL = "https://ark.cn-beijing.volces.com/api/v3/images/generations"
SEEDREAM_MODEL = "doubao-seedream-5-0-lite-260128"

PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").strip().rstrip("/")
KAIWU_BYPASS_NODE_PREREQUISITES = _env_bool("KAIWU_BYPASS_NODE_PREREQUISITES", True)


def public_url(path: str) -> str:
    normalized_path = "/" + path.lstrip("/")
    if not PUBLIC_BASE_URL:
        return normalized_path
    return f"{PUBLIC_BASE_URL}{normalized_path}"

# ═══════════════════════════════════════
# 差异性技能库 & 报告模板
# ═══════════════════════════════════════
SKILLS_DIR = Path(
    os.getenv("KAIWU_SKILLS_DIR", str(_BACKEND_ROOT / "skills-files"))
).expanduser()
REPORT_TEMPLATES_DIR = _BACKEND_ROOT / "report_templates"

# ═══════════════════════════════════════
# 存储路径
# ═══════════════════════════════════════
MD_STORE = _BACKEND_ROOT / "conversations"
MD_STORE.mkdir(parents=True, exist_ok=True)
IMG_STORE = _BACKEND_ROOT / "project-images"
IMG_STORE.mkdir(parents=True, exist_ok=True)
PROJECT_IMAGE_PREVIEW_STORE = _BACKEND_ROOT / "project-image-previews"
PROJECT_IMAGE_PREVIEW_STORE.mkdir(parents=True, exist_ok=True)
PROJECT_LIB = _BACKEND_ROOT / "project-files"
for folder in ["编程文件库", "AI 对话产出", "创业资料", "产品设计", "营销素材", "最近文件"]:
    (PROJECT_LIB / folder).mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════
# MySQL 数据库
# ═══════════════════════════════════════
DB_CONFIG = {
    "host": os.getenv("KAIWU_DB_HOST", "localhost"),
    "port": _env_int("KAIWU_DB_PORT", 3306),
    "user": os.getenv("KAIWU_DB_USER", ""),
    "password": os.getenv("KAIWU_DB_PASSWORD", ""),
    "database": os.getenv("KAIWU_DB_NAME", "kaiwu"),
    "charset": os.getenv("KAIWU_DB_CHARSET", "utf8mb4"),
}

DB_POOL_CONFIG = {
    "pool_size": _env_int("KAIWU_DB_POOL_SIZE", 5),
    "max_overflow": _env_int("KAIWU_DB_MAX_OVERFLOW", 10),
    "pool_timeout": _env_int("KAIWU_DB_POOL_TIMEOUT", 30),
    "pool_recycle": _env_int("KAIWU_DB_POOL_RECYCLE", 3600),
}

DB_CONNECT_ARGS = {
    "connect_timeout": _env_int("KAIWU_DB_CONNECT_TIMEOUT", 5),
    "read_timeout": _env_int("KAIWU_DB_READ_TIMEOUT", 30),
    "write_timeout": _env_int("KAIWU_DB_WRITE_TIMEOUT", 30),
}

# ═══════════════════════════════════════
# 数据真实性铁律
# ═══════════════════════════════════════
def _current_timezone() -> ZoneInfo:
    timezone_name = os.getenv("KAIWU_TIMEZONE", "Asia/Shanghai")
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        return ZoneInfo("Asia/Shanghai")


def current_date_cn() -> str:
    now = datetime.now(_current_timezone())
    return f"{now.year}年{now.month}月{now.day}日"


def data_integrity_prompt() -> str:
    return f"""
[数据真实性铁律]
当前日期：{current_date_cn()}。如果节点模板、历史消息或上游内容中出现其他固定日期，以本条当前日期为准。
所有数据需基于实际观测或明确测算，严禁虚构品牌名、人物名、具体数字、来源名称或发布日期。
时间敏感数据（市场规模、竞品门店数、融资/营收、政策、价格、用户规模、平台规则）必须标注来源名称与数据截至时间；找不到真实来源时标注[待人工调研确认]或[行业测算，可人工复核]，不要编造。
不得把旧年份数据包装成当前数据；引用上一年度或更早数据时，必须写明“公开数据截至YYYY年/最新公开来源为YYYY年”，并说明时效限制。
预测和估算必须显式标注[预测]或[行业测算]，并写出测算依据。当前年份如果只有部分公开数据，应写“YYYY年（截至最新公开数据）”，不要简单写“YYYY年(估)”。未来1-2年数据可以输出，但必须单列为预测补充，不能与已发生/当前数据混写。
"""


DATA_INTEGRITY = data_integrity_prompt()
