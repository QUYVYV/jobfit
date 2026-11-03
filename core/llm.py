"""调用 OpenAI 兼容接口（DeepSeek / 通义 / Kimi 等），要求模型返回 JSON。"""
import json
import os
import re

import requests


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
            return _extract_json(content)
        except Exception as e:  # noqa: BLE001
            last_err = e
    print(f"[llm] 调用失败，回退规则模式：{last_err}")
    return None
