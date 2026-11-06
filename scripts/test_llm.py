"""连续运行 5 次大模型分析，验证 JSON 结构、字段类型和稳定性。"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.scorer import analyze  # noqa: E402

JD = """大模型应用开发实习生
负责 Agent、RAG 知识库与 Prompt 工程优化；熟悉 Python，
了解 LangChain、向量数据库和 Function Calling，能够完成接口开发与效果评测。"""

RESUME = """计算机专业大三学生，使用 Python 完成过 RAG 知识库项目，
设计过 Prompt 和基于规则的风险评分链路；熟悉 Git、C++，正在学习 Agent 开发。"""


def main() -> int:
    if not any(os.getenv(name) for name in ("LLM_API_KEY", "DEEPSEEK_API_KEY", "OPENAI_API_KEY")):
        print("未配置大模型 API Key")
        return 2

    failures = []
    for index in range(1, 6):
        try:
            result = analyze(JD, RESUME, use_llm=True)
            assert result.get("mode") == "llm", "调用失败并回退了规则模式"
            assert isinstance(result.get("score"), int) and 0 <= result["score"] <= 100
            for field in ("matched_skills", "missing_skills", "reasons", "suggestions"):
                assert isinstance(result.get(field), list), f"{field} 不是数组"
            print(f"第 {index}/5 次：通过，score={result['score']}")
        except Exception as exc:  # noqa: BLE001
            failures.append(f"第 {index}/5 次：{type(exc).__name__}: {exc}")
            print(failures[-1])

    print(f"结果：{5 - len(failures)}/5 次返回合法结果")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
