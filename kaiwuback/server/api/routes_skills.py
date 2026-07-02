"""Skills API 路由 —— 从 main.py 抽取"""
from pathlib import Path
from server.config import SKILLS_DIR


def list_external_skills():
    """列出差异性skills目录下的外部技能"""
    skills = []
    if not SKILLS_DIR.exists():
        return skills
    for skill_dir in SKILLS_DIR.iterdir():
        if not skill_dir.is_dir() or skill_dir.name.startswith('.'):
            continue
        name = skill_dir.name
        desc = ""
        skill_md = skill_dir / "skills" / name / "SKILL.md"
        if not skill_md.exists():
            for f in skill_dir.glob("*.md"):
                skill_md = f
                break
        if skill_md.exists():
            content = skill_md.read_text(encoding='utf-8')
            for line in content.split('\n'):
                if line.startswith('description:'):
                    desc = line.split(':', 1)[1].strip()
                    break
            if not desc:
                in_fm = False
                for line in content.split('\n'):
                    if line.strip() == '---':
                        in_fm = not in_fm
                        continue
                    if not in_fm and line.strip() and not line.startswith('#'):
                        desc = line.strip()[:100]
                        break
        skills.append({
            "id": name, "name": name,
            "description": desc or name,
            "full_content": skill_md.read_text(encoding='utf-8') if skill_md and skill_md.exists() else "",
        })
    return skills


def register_skills_routes(app):
    """向 FastAPI app 注册 Skills 相关路由"""
    from fastapi.responses import JSONResponse

    @app.get("/api/skills")
    def api_list_skills():
        return list_external_skills()

    @app.get("/api/skills/{skill_id}")
    def api_get_skill(skill_id: str):
        for s in list_external_skills():
            if s['id'] == skill_id:
                return s
        return JSONResponse({"error": "Skill not found"}, status_code=404)
