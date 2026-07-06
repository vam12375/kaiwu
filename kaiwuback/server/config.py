"""配置管理 —— 所有敏感信息从环境变量读取"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 自动加载 kaiwuback/.env.local（config.py 的上两级目录）
_env_path = Path(__file__).parent.parent / ".env.local"
if _env_path.exists():
    load_dotenv(_env_path)

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

# ═══════════════════════════════════════
# 差异性技能库 & 报告模板
# ═══════════════════════════════════════
SKILLS_DIR = Path(
    os.getenv("KAIWU_SKILLS_DIR", str(Path(__file__).parent.parent / "skills-files"))
).expanduser()
REPORT_TEMPLATES_DIR = Path(__file__).parent.parent / "report_templates"

# ═══════════════════════════════════════
# 存储路径
# ═══════════════════════════════════════
MD_STORE = Path(__file__).parent.parent / "conversations"
MD_STORE.mkdir(parents=True, exist_ok=True)
IMG_STORE = Path(__file__).parent.parent / "project-images"
IMG_STORE.mkdir(parents=True, exist_ok=True)
PROJECT_LIB = Path(__file__).parent.parent / "project-files"
for folder in ["编程文件库", "AI 对话产出", "创业资料", "产品设计", "营销素材", "最近文件"]:
    (PROJECT_LIB / folder).mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════
# MySQL 数据库
# ═══════════════════════════════════════
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "password",
    "database": "kaiwu",
    "charset": "utf8mb4",
}

# ═══════════════════════════════════════
# 数据真实性铁律
# ═══════════════════════════════════════
DATA_INTEGRITY = """
[数据真实性铁律]
当前日期：2026年6月23日。所有数据需基于实际观测，严禁虚构品牌名、人物名、具体数字。
找不到真实数据时标注[建议人工复核]，不要编造。
"""
