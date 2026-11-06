"""调用 OpenAI 兼容接口（DeepSeek / 通义 / Kimi 等），要求模型返回 JSON。"""
import json
import os
import re
from pathlib import Path

import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env", override=False)

RESULT_FIELDS = {
    "score",
    "matched_skills",
    "missing_skills",
    "reasons",
    "suggestions",
}


def _extract_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            return json.loads(m.group(0))
        raise


def _validate_result(data: dict) -> dict:
    """校验并规范化模型结果，避免结构错误进入页面。"""
    if not isinstance(data, dict):
        raise ValueError("模型返回的不是 JSON 对象")
    missing_fields = RESULT_FIELDS - data.keys()
    if missing_fields:
        raise ValueError(f"缺少字段：{', '.join(sorted(missing_fields))}")

    score = data["score"]
    if isinstance(score, bool) or not isinstance(score, int) or not 0 <= score <= 100:
        raise ValueError("score 必须是 0-100 的整数")

    normalized = {"score": score}
    for field in ("matched_skills", "missing_skills"):
        values = data[field]
        if not isinstance(values, list) or not all(isinstance(value, str) and value.strip() for value in values):
            raise ValueError(f"{field} 必须是字符串数组，且每个元素不能为空")
        normalized[field] = list(dict.fromkeys(value.strip() for value in values))

    overlap = set(normalized["matched_skills"]) & set(normalized["missing_skills"])
    if overlap:
        raise ValueError(f"技能同时出现在匹配和缺口列表：{sorted(overlap)}")

    for field in ("reasons", "suggestions"):
        values = data[field]
        if (
            not isinstance(values, list)
            or not 2 <= len(values) <= 3
            or not all(isinstance(value, str) and value.strip() for value in values)
        ):
            raise ValueError(f"{field} 必须包含 2-3 条非空字符串")
        normalized[field] = [value.strip() for value in values[:3]]

    return normalized


def chat_json(system: str, user: str, retries: int = 2) -> dict | None:
    """没有配置 API Key 时返回 None，由调用方回退到规则打分。"""
    api_key = os.getenv("LLM_API_KEY") or os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    base = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1").rstrip("/")
    model = os.getenv("LLM_MODEL", "deepseek-chat")
    last_err = None
    for _ in range(retries + 1):
        try:
            resp = requests.post(
                f"{base}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": model,
                    "temperature": 0.2,
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                },
                timeout=60,
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            return _validate_result(_extract_json(content))
        except Exception as e:  # noqa: BLE001
            last_err = e
    print(f"[llm] 调用失败，回退规则模式：{last_err}")
    return None
