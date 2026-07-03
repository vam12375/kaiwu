"""Skills API routes."""

from pathlib import Path

from fastapi.responses import JSONResponse

from server.config import SKILLS_DIR


DEFAULT_SKILL_CATEGORY = "方法论"


def _clean_meta_value(value: str) -> str:
    return value.strip().strip('"').strip("'")


def _parse_frontmatter(content: str) -> dict[str, str]:
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}

    meta: dict[str, str] = {}
    for line in lines[1:]:
        stripped = line.strip()
        if stripped == "---":
            break
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        meta[key.strip()] = _clean_meta_value(value)
    return meta


def _first_body_summary(content: str) -> str:
    in_frontmatter = False
    frontmatter_closed = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped == "---" and not frontmatter_closed:
            in_frontmatter = not in_frontmatter
            if not in_frontmatter:
                frontmatter_closed = True
            continue
        if in_frontmatter or not stripped or stripped.startswith("#"):
            continue
        return stripped[:120]
    return ""


def _find_skill_file(skill_dir: Path) -> Path | None:
    nested_skill = skill_dir / "skills" / skill_dir.name / "SKILL.md"
    if nested_skill.exists():
        return nested_skill

    for candidate in sorted(skill_dir.rglob("SKILL.md")):
        if candidate.is_file():
            return candidate

    for candidate in sorted(skill_dir.glob("*.md")):
        if candidate.is_file():
            return candidate

    return None


def _read_skill(skill_dir: Path) -> dict[str, str] | None:
    skill_file = _find_skill_file(skill_dir)
    if not skill_file:
        return None

    content = skill_file.read_text(encoding="utf-8")
    meta = _parse_frontmatter(content)
    name = meta.get("display_name") or meta.get("name") or skill_dir.name
    description = (
        meta.get("description_zh")
        or meta.get("description")
        or _first_body_summary(content)
        or name
    )
    category = meta.get("category") or DEFAULT_SKILL_CATEGORY

    return {
        "id": skill_dir.name,
        "name": name,
        "description": description,
        "category": category,
        "version": meta.get("version", ""),
        "source": "external",
        "entry_file": skill_file.relative_to(SKILLS_DIR).as_posix(),
        "full_content": content,
    }


def list_external_skills():
    """List external skills from the configured skill directory."""
    if not SKILLS_DIR.exists():
        return []

    skills = []
    for skill_dir in sorted(SKILLS_DIR.iterdir(), key=lambda item: item.name):
        if not skill_dir.is_dir() or skill_dir.name.startswith("."):
            continue
        skill = _read_skill(skill_dir)
        if skill:
            skills.append(skill)
    return skills


def register_skills_routes(app):
    """Register Skills routes on the FastAPI app."""

    @app.get("/api/skills")
    def api_list_skills():
        return list_external_skills()

    @app.get("/api/skills/{skill_id}")
    def api_get_skill(skill_id: str):
        for skill in list_external_skills():
            if skill["id"] == skill_id:
                return skill
        return JSONResponse({"error": "Skill not found"}, status_code=404)
