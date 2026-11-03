"""技能词典抽取：把 JD / 简历里的技能词映射到统一名称。"""
import json
import re
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data" / "skills.json"


def load_skills(path: Path = DATA) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract(text: str, skills: dict) -> dict:
    """返回 {标准化技能: 命中的原始写法集合}。长词优先，避免 'C++' 被 'C' 误伤。"""
    text_l = text.lower()
    found = {}
    for canon, aliases in skills.items():
        hits = set()
        for alias in aliases:
            a = alias.lower()
            # 英文用词边界，中文直接包含
            if re.fullmatch(r"[a-z0-9+.#\- /]+", a):
                if re.search(rf"(?<![a-z0-9]){re.escape(a)}(?![a-z0-9])", text_l):
                    hits.add(alias)
            elif a in text_l:
                hits.add(alias)
        if hits:
            found[canon] = hits
    return found


def coverage(jd_skills: set, resume_skills: set) -> dict:
    if not jd_skills:
        return {"coverage": 0.0, "matched": [], "missing": []}
    matched = sorted(jd_skills & resume_skills)
    missing = sorted(jd_skills - resume_skills)
    return {"coverage": len(matched) / len(jd_skills), "matched": matched, "missing": missing}
