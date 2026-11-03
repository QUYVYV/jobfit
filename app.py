"""JobFit — AI 岗位匹配与技能缺口分析助手（Streamlit 界面）。"""
import os

import plotly.graph_objects as go
import streamlit as st

from core.scorer import analyze
from core.skills import extract, load_skills

st.set_page_config(page_title="JobFit · AI 岗位匹配助手", page_icon="🎯", layout="wide")

SKILLS = load_skills()

DEMO_JD = """大模型应用开发实习生
负责大模型应用的产品化落地，参与 RAG 知识库建设与 Prompt 工程优化；
熟悉 Python，了解 LangChain 或 LlamaIndex；有向量数据库（FAISS/Chroma）使用经验优先；
负责接口开发与效果评测，能够快速搭建可演示的原型。"""

DEMO_RESUME = """吴汶洳，湖南大学智能科学与技术专业大三。
国家级大创 FinRiskEye 项目负责人，设计「规则引擎 + 大模型 + RAG + 风险评分」四层链路，
负责整体技术路线与系统架构；使用 Python 调用大模型 API，设计 Prompt，参与多模态内容识别方案；
参与省级大创，做图对比学习相关文献调研与框架梳理。熟悉 C++、Git，正在学习 PyTorch 与机器学习。"""

st.title("🎯 JobFit · AI 岗位匹配与技能缺口分析")
st.caption("粘贴 JD 与简历 → 输出匹配分、已匹配技能、缺口技能与改进建议")

col1, col2 = st.columns(2)
with col1:
    jd = st.text_area("岗位描述（JD）", DEMO_JD, height=260)
with col2:
    resume = st.text_area("你的简历文本", DEMO_RESUME, height=260)

use_llm = st.checkbox(
    "使用大模型增强（需配置 LLM_API_KEY）",
    value=bool(os.getenv("LLM_API_KEY") or os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")),
)

if st.button("开始分析", type="primary"):
    if not jd.strip() or not resume.strip():
        st.warning("请先填写 JD 与简历文本")
        st.stop()

    with st.spinner("分析中…"):
        result = analyze(jd, resume, use_llm=use_llm)

    left, right = st.columns([1, 2])
    with left:
        score = int(result.get("score", 0))
        st.metric("匹配度", f"{score} / 100")
        st.caption("规则模式：技能覆盖率 65% + 文本相似度 35%" if result.get("mode") == "rule" else "大模型模式")
        comp = result.get("components")
        if comp:
            st.caption(
                f"技能覆盖率 {comp['coverage']:.0%} × {comp['w_coverage']:.0%} + "
                f"文本相似度 {comp['similarity']:.2f} × {comp['w_similarity']:.0%} = {score} 分"
            )
    with right:
        matched = result.get("matched_skills", [])
        missing = result.get("missing_skills", [])
        if matched or missing:
            total = len(matched) + len(missing)
            fig = go.Figure(
                go.Scatterpolar(
                    r=[len(matched) / total if total else 0, score / 100, 1 - (len(missing) / total if total else 0)],
                    theta=["技能命中", "综合匹配", "岗位适配"],
                    fill="toself",
                )
            )
            fig.update_layout(polar=dict(radialaxis=dict(range=[0, 1])), height=280, margin=dict(t=30, b=20))
            st.plotly_chart(fig, use_container_width=True)

    a, b = st.columns(2)
    with a:
        st.subheader("✅ 已匹配技能")
        st.write("、".join(result.get("matched_skills", [])) or "暂无明显匹配")
    with b:
        st.subheader("⚠️ 缺口技能")
        st.write("、".join(result.get("missing_skills", [])) or "无")

    st.subheader("📋 评估理由")
    for r in result.get("reasons", []):
        st.write("- " + str(r))

    st.subheader("🚀 改进建议")
    for s in result.get("suggestions", []):
        st.write("- " + str(s))

    with st.expander("查看抽取出的技能明细"):
        st.write("JD：", ", ".join(sorted(extract(jd, SKILLS).keys())) or "无")
        st.write("简历：", ", ".join(sorted(extract(resume, SKILLS).keys())) or "无")

    with st.expander("查看分数构成与原始返回"):
        comp = result.get("components")
        if comp:
            st.write(
                {
                    "技能覆盖率": comp["coverage"],
                    "文本相似度": comp["similarity"],
                    "技能覆盖率权重": comp["w_coverage"],
                    "文本相似度权重": comp["w_similarity"],
                }
            )
        st.json(result)

st.divider()
st.caption("JobFit · 一周项目 · 用规则 + 大模型完成岗位匹配，并用评测集量化效果")
