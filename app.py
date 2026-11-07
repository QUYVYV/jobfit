"""JobFit — AI 岗位匹配与技能缺口分析助手（Streamlit 界面）。"""
import html
import os

import plotly.graph_objects as go
import streamlit as st

from core.scorer import W_COVERAGE, W_SIMILARITY, analyze
from core.skills import extract, load_skills

st.set_page_config(page_title="JobFit · AI 岗位匹配助手", page_icon="🎯", layout="wide")

SKILLS = load_skills()

DEMO_AI_JD = """大模型应用开发实习生
负责大模型应用的产品化落地，参与 RAG 知识库建设与 Prompt 工程优化；
熟悉 Python，了解 LangChain 或 LlamaIndex；有向量数据库（FAISS/Chroma）使用经验优先；
负责接口开发与效果评测，能够快速搭建可演示的原型。"""

DEMO_AI_RESUME = """计算机学院智能科学与技术专业大三。
国家级大创项目负责人，设计「规则引擎 + 大模型 + RAG + 风险评分」链路，
使用 Python 调用大模型 API，完成 Prompt 设计并参与多模态内容识别方案。
熟悉 C++、Git，正在学习 PyTorch 与机器学习。"""

DEMO_DATA_JD = """数据分析实习生
负责业务数据的整理、清洗与可视化，建设核心指标体系；
熟练使用 SQL、Excel 与 Python/pandas，能够独立完成专题分析；
熟悉 A/B 实验、用户分层和经营分析报告，有 AI 工具提效经验优先。"""

DEMO_DATA_RESUME = """统计学与计算机交叉背景大三学生。
使用 SQL 和 Python/pandas 完成课程数据分析项目，
设计过用户行为指标与可视化看板，参与 A/B 实验方案讨论。
能够使用 Git 管理分析脚本，正在学习机器学习与因果推断。"""

if "jd_input" not in st.session_state:
    st.session_state.jd_input = ""
if "resume_input" not in st.session_state:
    st.session_state.resume_input = ""


def _load_example(jd: str, resume: str) -> None:
    st.session_state.jd_input = jd
    st.session_state.resume_input = resume


def _clear_inputs() -> None:
    st.session_state.jd_input = ""
    st.session_state.resume_input = ""


def _render_chips(skills: list[str], tone: str, empty_text: str) -> None:
    if not skills:
        chips = f'<span class="skill-chip muted">{html.escape(empty_text)}</span>'
    else:
        chips = "".join(f'<span class="skill-chip {tone}">{html.escape(str(skill))}</span>' for skill in skills)
    st.markdown(f'<div class="chip-row">{chips}</div>', unsafe_allow_html=True)


def _render_items(items: list[str], marker: str) -> None:
    if not items:
        st.caption("暂无内容")
        return
    rows = "".join(
        f'<div class="detail-item"><span>{html.escape(marker)}</span><p>{html.escape(str(item))}</p></div>'
        for item in items
    )
    st.markdown(rows, unsafe_allow_html=True)


st.markdown(
    """
<style>
    .stApp {
        background:
            radial-gradient(circle at 8% 0%, rgba(15, 118, 110, 0.10), transparent 30rem),
            linear-gradient(180deg, #f8fbfc 0%, #edf3f5 100%);
    }
    .block-container {
        max-width: 1180px;
        padding-top: 2.2rem;
        padding-bottom: 3rem;
    }
    .hero {
        position: relative;
        overflow: hidden;
        padding: 2rem 2.2rem;
        margin-bottom: 1.15rem;
        border: 1px solid rgba(15, 118, 110, 0.18);
        border-radius: 22px;
        background: linear-gradient(120deg, #0f2f33 0%, #124f50 62%, #0f766e 100%);
        box-shadow: 0 20px 50px rgba(19, 57, 61, 0.16);
    }
    .hero::after {
        content: "";
        position: absolute;
        width: 18rem;
        height: 18rem;
        right: -5rem;
        top: -9rem;
        border: 1px solid rgba(255, 255, 255, 0.14);
        border-radius: 50%;
        box-shadow: 0 0 0 3rem rgba(255, 255, 255, 0.03), 0 0 0 7rem rgba(255, 255, 255, 0.02);
    }
    .hero-kicker {
        color: #83e6d7 !important;
        font-size: 0.78rem;
        font-weight: 750;
        letter-spacing: 0.13em;
        text-transform: uppercase;
    }
    .hero-title {
        margin: 0.55rem 0 0.55rem;
        color: #ffffff !important;
        font-size: clamp(2rem, 4vw, 3.35rem);
        line-height: 1.08;
        font-weight: 800;
        letter-spacing: -0.035em;
    }
    .hero-subtitle {
        max-width: 48rem;
        margin: 0;
        color: #c8dddc;
        font-size: 1rem;
        line-height: 1.75;
    }
    .hero-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 0.55rem;
        margin-top: 1.2rem;
    }
    .hero-pill {
        padding: 0.35rem 0.7rem;
        border: 1px solid rgba(255, 255, 255, 0.16);
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.08);
        color: #e7f4f2;
        font-size: 0.78rem;
    }
    .hero-pill.ready {
        border-color: rgba(131, 230, 215, 0.48);
        background: rgba(131, 230, 215, 0.12);
        color: #a4f4e8;
    }
    .section-kicker {
        margin: 1.5rem 0 0.35rem;
        color: #0f766e;
        font-size: 0.75rem;
        font-weight: 750;
        letter-spacing: 0.12em;
        text-transform: uppercase;
    }
    .section-title {
        margin: 0 0 0.35rem;
        color: #132e33;
        font-size: 1.45rem;
        line-height: 1.3;
        font-weight: 760;
    }
    .section-copy {
        margin: 0 0 0.9rem;
        color: #5e7175;
        font-size: 0.9rem;
    }
    div[data-testid="stTextArea"] textarea {
        min-height: 230px;
        border-color: #d7e2e3 !important;
        border-radius: 12px !important;
        background: #fbfdfd !important;
        font-size: 0.92rem !important;
        line-height: 1.65 !important;
    }
    div[data-testid="stTextArea"] textarea:focus {
        border-color: #0f766e !important;
        box-shadow: 0 0 0 1px #0f766e !important;
    }
    div[data-testid="stButton"] button[kind="primary"] {
        min-height: 3rem;
        border: 0;
        border-radius: 11px;
        background: linear-gradient(90deg, #0f766e, #128a7e);
        font-weight: 750;
        box-shadow: 0 8px 22px rgba(15, 118, 110, 0.2);
    }
    div[data-testid="stButton"] button[kind="primary"]:hover {
        background: linear-gradient(90deg, #115e59, #0f766e);
    }
    div[data-testid="stMetric"] {
        padding: 1.1rem;
        border: 1px solid #dce7e8;
        border-radius: 15px;
        background: #ffffff;
        box-shadow: 0 8px 26px rgba(30, 66, 70, 0.06);
    }
    div[data-testid="stMetricValue"] {
        color: #0f766e;
        font-weight: 800;
    }
    .mode-line {
        margin: 0.25rem 0 0.75rem;
        color: #50666a;
        font-size: 0.86rem;
    }
    .mode-good {
        color: #0f766e;
        font-weight: 700;
    }
    .chip-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.45rem;
        min-height: 2rem;
    }
    .skill-chip {
        display: inline-flex;
        align-items: center;
        padding: 0.35rem 0.62rem;
        border-radius: 999px;
        font-size: 0.82rem;
        font-weight: 650;
    }
    .skill-chip.good {
        border: 1px solid #b9e7d7;
        background: #e9f8f2;
        color: #12634c;
    }
    .skill-chip.gap {
        border: 1px solid #f4d0bd;
        background: #fff4ed;
        color: #a34f24;
    }
    .skill-chip.muted {
        border: 1px solid #dce7e8;
        background: #f4f7f7;
        color: #728286;
    }
    .detail-item {
        display: grid;
        grid-template-columns: 1.35rem minmax(0, 1fr);
        gap: 0.5rem;
        padding: 0.65rem 0;
        border-bottom: 1px solid #edf1f1;
        color: #354c50;
        line-height: 1.6;
    }
    .detail-item:last-child {
        border-bottom: 0;
    }
    .detail-item p {
        margin: 0;
        font-size: 0.91rem;
    }
    .footer-note {
        margin-top: 1.5rem;
        padding-top: 1rem;
        border-top: 1px solid #d9e4e5;
        color: #728286;
        font-size: 0.8rem;
        line-height: 1.65;
    }
    @media (max-width: 700px) {
        .hero { padding: 1.5rem 1.25rem; border-radius: 17px; }
        .hero-title { font-size: 2.05rem; }
        .block-container { padding-top: 1rem; }
    }
</style>
""",
    unsafe_allow_html=True,
)

llm_ready = bool(
    os.getenv("LLM_API_KEY") or os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
)
llm_status = (
    '<span class="hero-pill ready">● 大模型已就绪</span>'
    if llm_ready
    else '<span class="hero-pill">● 本地规则模式</span>'
)
st.markdown(
    f"""
    <section class="hero">
        <div class="hero-kicker">JOBFIT · AI CAREER MATCH</div>
        <h1 class="hero-title">让岗位要求与简历证据<br>真正对上号</h1>
        <p class="hero-subtitle">
            粘贴一份 JD 和简历，获得可解释的匹配分、技能缺口与下一步改进建议。
            规则负责稳定抽取，大模型负责语义判断。
        </p>
        <div class="hero-meta">
            {llm_status}
            <span class="hero-pill">121 项技能词典</span>
            <span class="hero-pill">25 条岗位语料</span>
            <span class="hero-pill">结构化 JSON 校验</span>
        </div>
    </section>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="section-kicker">01 · 准备材料</div>', unsafe_allow_html=True)
st.markdown('<h2 class="section-title">先选一个示例，或粘贴自己的内容</h2>', unsafe_allow_html=True)
st.markdown(
    '<p class="section-copy">示例均为虚构数据。真实简历请先脱敏，不要粘贴身份证、手机号等个人信息。</p>',
    unsafe_allow_html=True,
)

example_ai, example_data, clear_col, _ = st.columns([1.5, 1.5, 1, 2])
with example_ai:
    st.button(
        "填入 AI 应用示例",
        key="load_ai_example",
        on_click=_load_example,
        args=(DEMO_AI_JD, DEMO_AI_RESUME),
    )
with example_data:
    st.button(
        "填入数据分析示例",
        key="load_data_example",
        on_click=_load_example,
        args=(DEMO_DATA_JD, DEMO_DATA_RESUME),
    )
with clear_col:
    st.button("清空内容", key="clear_inputs", on_click=_clear_inputs)

with st.container(border=True):
    jd_col, resume_col = st.columns(2)
    with jd_col:
        jd = st.text_area(
            "岗位描述（JD）",
            key="jd_input",
            height=250,
            placeholder="粘贴岗位职责、任职要求与加分项……",
        )
    with resume_col:
        resume = st.text_area(
            "简历文本",
            key="resume_input",
            height=250,
            placeholder="粘贴教育背景、项目经历、技能与实习经历……",
        )

st.markdown('<div class="section-kicker">02 · 选择分析方式</div>', unsafe_allow_html=True)
with st.container(border=True):
    use_llm = st.checkbox(
        "启用大模型语义增强",
        key="use_llm",
        value=llm_ready,
        help="关闭后只运行本地规则模式；开启后每次分析会调用一次大模型并产生少量 API 费用。",
    )
    if llm_ready:
        st.caption(f"当前模型：{os.getenv('LLM_MODEL', 'deepseek-chat')} · 结果会经过 JSON 结构校验")
    else:
        st.caption("尚未配置大模型，本次只使用本地规则模式。")
    analyze_clicked = st.button(
        "开始岗位匹配分析",
        key="analyze_button",
        type="primary",
        width="stretch",
    )

if analyze_clicked:
    if not jd.strip() or not resume.strip():
        st.warning("请先填写 JD 与简历文本，或点击上方示例按钮。")
        st.stop()

    with st.spinner("正在匹配岗位、抽取技能并生成建议…"):
        result = analyze(jd, resume, use_llm=use_llm)

    score = int(result.get("score", 0))
    mode = result.get("mode")
    mode_label = "大模型增强" if mode == "llm" else "本地规则"
    comp = result.get("components") or {}
    matched = result.get("matched_skills", [])
    missing = result.get("missing_skills", [])

    st.markdown('<div class="section-kicker">03 · 匹配结论</div>', unsafe_allow_html=True)
    left, right = st.columns([1, 1.55])
    with left:
        st.metric("综合匹配度", f"{score} / 100")
        st.progress(
            min(max(score, 0), 100) / 100,
            text="匹配度越高，简历与岗位要求的显性证据越充分。",
        )
        st.markdown(
            f'<p class="mode-line"><span class="mode-good">● {html.escape(mode_label)}</span>'
            f'　{"大模型综合判断" if mode == "llm" else "技能覆盖率与文本相似度加权"}</p>',
            unsafe_allow_html=True,
        )
        if comp:
            reference_score = int(result.get("rule_score", score))
            formula = (
                f"规则参考：{comp['coverage']:.0%} × {comp['w_coverage']:.0%} + "
                f"{comp['similarity']:.2f} × {comp['w_similarity']:.0%} = {reference_score} 分"
            )
            st.caption(formula)
        elif mode == "llm":
            st.caption(f"规则参考分：{result.get('rule_score', '未返回')}")

    with right:
        coverage = float(comp.get("coverage", len(matched) / max(len(matched) + len(missing), 1)))
        similarity = float(comp.get("similarity", score / 100))
        fig = go.Figure(
            go.Scatterpolar(
                r=[coverage, similarity, score / 100],
                theta=["技能覆盖", "文本相似", "综合匹配"],
                fill="toself",
                line={"color": "#0f766e", "width": 2},
                marker={"color": "#14b8a6", "size": 7},
                fillcolor="rgba(20, 184, 166, 0.20)",
                hovertemplate="%{theta}: %{r:.0%}<extra></extra>",
            )
        )
        fig.update_layout(
            height=300,
            margin={"t": 25, "b": 15, "l": 45, "r": 45},
            paper_bgcolor="rgba(0,0,0,0)",
            font={"color": "#52696d"},
            polar={
                "bgcolor": "rgba(255,255,255,0.62)",
                "radialaxis": {
                    "range": [0, 1],
                    "tickformat": ".0%",
                    "gridcolor": "#dce7e8",
                    "linecolor": "#dce7e8",
                },
                "angularaxis": {"gridcolor": "#dce7e8", "linecolor": "#dce7e8"},
            },
            showlegend=False,
        )
        st.plotly_chart(fig, width="stretch")

    matched_col, missing_col = st.columns(2)
    with matched_col:
        with st.container(border=True):
            st.subheader("✓ 已匹配技能")
            _render_chips(matched, "good", "暂无明显匹配")
    with missing_col:
        with st.container(border=True):
            st.subheader("! 缺口技能")
            _render_chips(missing, "gap", "没有发现明显缺口")

    reason_col, suggestion_col = st.columns(2)
    with reason_col:
        with st.container(border=True):
            st.subheader("评估依据")
            _render_items(result.get("reasons", []), "✓")
    with suggestion_col:
        with st.container(border=True):
            st.subheader("下一步建议")
            _render_items(result.get("suggestions", []), "→")

    with st.expander("查看抽取出的技能明细"):
        st.write("JD：", "、".join(sorted(extract(jd, SKILLS).keys())) or "无")
        st.write("简历：", "、".join(sorted(extract(resume, SKILLS).keys())) or "无")

    with st.expander("查看分数构成与原始返回"):
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

st.markdown(
    """
    <div class="footer-note">
        JobFit 使用规则抽取与结构化大模型判断辅助岗位分析，结果仅用于学习与准备参考。
        规则模式完全本地运行；大模型模式每次分析会调用一次 API，可能产生少量费用。
    </div>
    """,
    unsafe_allow_html=True,
)
