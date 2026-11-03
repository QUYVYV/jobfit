"""两种打分：规则模式（无需 API）与大模型模式（有 API 时）。"""
import json
from pathlib import Path

from .llm import chat_json
from .retrieval import load_corpus, similar, similarity
from .skills import coverage, extract, load_skills

SKILLS = load_skills()

SYSTEM = (
    "你是招聘匹配评估助手。只输出 JSON，不要输出解释性文字。"
    "score 为 0-100 的整数；matched_skills / missing_skills 为技能名数组；"
    "reasons 为 3 条以内的字符串数组；suggestions 为 3 条可执行的改进建议。"
)

USER_TMPL = """【岗位描述】
{jd}

【候选人简历】
{resume}

【已抽取技能】JD：{jd_skills}；简历：{resume_skills}
【相似岗位参考】{similar}

请评估匹配度，输出 JSON：
{{"score": 0, "matched_skills": [], "missing_skills": [], "reasons": [], "suggestions": []}}"""


def analyze(jd: str, resume: str, use_llm: bool = True) -> dict:
    jd_sk = set(extract(jd, SKILLS).keys())
    rs_sk = set(extract(resume, SKILLS).keys())
    cov = coverage(jd_sk, rs_sk)
    sim = similarity(jd, resume)
    rule_score = round(100 * (0.65 * cov["coverage"] + 0.35 * sim))
    refs = similar(jd, load_corpus(), k=3)

    rule = {
        "score": rule_score,
        "matched_skills": cov["matched"],
        "missing_skills": cov["missing"],
        "components": {
            "coverage": round(cov["coverage"], 4),
            "similarity": round(sim, 4),
            "w_coverage": 0.65,
            "w_similarity": 0.35,
        },
        "reasons": [
            f"岗位要求的 {len(jd_sk)} 项技能中命中 {len(cov['matched'])} 项（覆盖率 {cov['coverage']:.0%}）",
            f"简历与岗位描述的文本相似度为 {sim:.2f}",
        ],
        "suggestions": [f"补充与「{s}」相关的项目或课程证据" for s in cov["missing"][:3]],
        "mode": "rule",
    }
    if not use_llm:
        return rule

    llm = chat_json(
        SYSTEM,
        USER_TMPL.format(
            jd=jd[:1500],
            resume=resume[:2000],
            jd_skills=", ".join(sorted(jd_sk)) or "无",
            resume_skills=", ".join(sorted(rs_sk)) or "无",
            similar=json.dumps(refs, ensure_ascii=False),
        ),
    )
    if not llm:
        return rule
    llm["mode"] = "llm"
    llm["rule_score"] = rule_score
    llm["components"] = rule["components"]
    return llm
