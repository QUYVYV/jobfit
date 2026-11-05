# JobFit · AI 岗位匹配与技能缺口分析助手

> 粘贴一份 JD 和一份简历，输出匹配分、已匹配技能、缺口技能与可执行的改进建议。

一个面向 **AI 应用开发 / 数据分析实习岗位** 的小型 RAG + LLM 应用：
规则负责可解释的技能匹配，大模型负责语义判断与建议生成，评测脚本负责量化效果。

![JobFit 界面截图](docs/screenshot.png)

## 功能

- **技能抽取**：内置 100+ 技能词典（中英文别名），从 JD 与简历中抽取标准化技能
- **岗位检索**：TF-IDF 在岗位库中检索相似 JD，作为大模型判断的上下文（最小 RAG 实现）
- **匹配打分**：技能覆盖率与文本相似度加权计算，权重集中在 `core/scorer.py` 配置，可解释、可复现
- **大模型增强**：接入任意 OpenAI 兼容接口（DeepSeek / 通义 / Kimi / OpenAI），输出结构化 JSON
- **可视化**：Streamlit 页面 + 雷达图 + 缺口技能列表
- **可评测**：30 组人工标注样本，输出三分类准确率与混淆矩阵

## 架构

```
┌────────────┐     ┌──────────────┐     ┌───────────────┐
│  JD 文本    │────▶│  技能抽取     │────▶│  规则打分       │
└────────────┘     │  (skills.py)  │     │  (scorer.py)   │
┌────────────┐     └──────────────┘     └───────┬───────┘
│  简历文本   │──────────────────────────────────┘
└────────────┘             │
                           ▼
                  ┌────────────────┐     ┌──────────────┐
                  │  相似 JD 检索   │────▶│  LLM 结构化输出│
                  │ (retrieval.py) │     │   (llm.py)    │
                  └────────────────┘     └──────┬───────┘
                                                ▼
                                      ┌──────────────────┐
                                      │ Streamlit 可视化  │
                                      └──────────────────┘
```

## 快速开始

```bash
git clone https://github.com/<你的用户名>/jobfit.git
cd jobfit
pip install -r requirements.txt

# 不配置 API Key 也能跑（规则模式）
streamlit run app.py

# 想用大模型增强：复制 .env.example 为 .env 并填入 Key
# Windows PowerShell:
$env:LLM_API_KEY="sk-xxx"
$env:LLM_BASE_URL="https://api.deepseek.com/v1"
$env:LLM_MODEL="deepseek-chat"
streamlit run app.py
```

## 评测

1. 复制 `eval/labels_template.csv` 为 `eval/labels.csv`
2. 准备 30 组 `(JD, 简历, 人工标签 high/mid/low)`，其中 high/mid/low 各 10 组
3. 运行：

```bash
python eval/evaluate.py --labels eval/labels.csv
```

输出示例：

```
样本数：30
三分类准确率：76.67%

混淆矩阵（行=人工标签，列=模型预测）：
           high     mid     low
 high         8       2       0
  mid         2       6       2
  low         0       2       8
```

> `labels.csv` 可能包含个人简历信息，已在 `.gitignore` 中排除；如需公开，请先脱敏。

## 目录结构

```
jobfit/
├── app.py                  # Streamlit 入口
├── core/
│   ├── skills.py           # 技能词典抽取
│   ├── retrieval.py        # TF-IDF 相似岗位检索
│   ├── scorer.py           # 规则打分 / LLM 打分
│   └── llm.py              # OpenAI 兼容接口调用
├── data/
│   ├── skills.json         # 技能词典（可自行扩充）
│   └── jds.jsonl           # 岗位库（可自行扩充）
├── eval/
│   ├── evaluate.py         # 评测脚本
│   └── labels_template.csv # 标注模板
├── requirements.txt
└── .env.example
```

## 我的收获

- 理解了 **规则 + 大模型的分工**：规则保证下限与可解释性，大模型补语义与表达
- 走通了 **RAG 的最小闭环**：检索 → 拼上下文 → 结构化生成 → 评测
- 用 **混淆矩阵** 定位错误类型，而不是只看一个准确率
- 体会到 **Prompt 的结构化约束**（要求 JSON、失败重试）对工程稳定性的影响

## Roadmap

- [ ] 支持 PDF 简历上传与自动解析
- [ ] 扩充岗位库到 200 条，并按岗位类型分桶评测
- [ ] 接入向量嵌入检索，对比 TF-IDF 的召回差异
- [ ] 增加「简历改写建议」的一键生成

## 说明

本项目为个人学习与实践项目，用于演示 AI 应用开发中的「技能抽取 + 检索 + 大模型 + 评测」链路，
不构成任何招聘建议。原有演示 JD 与示例简历为虚构数据；新增岗位语料来自公开招聘页面，
仅保留检索所需的职责摘要并记录来源，岗位信息可能随时间变化。
