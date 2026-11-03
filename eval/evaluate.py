"""评测脚本：读取 labels.csv，跑规则打分，输出准确率与混淆矩阵。

用法：
    python eval/evaluate.py --labels eval/labels.csv

human_label 取值：high / mid / low
"""
import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.scorer import analyze  # noqa: E402


def to_bucket(score: int) -> str:
    if score >= 70:
        return "high"
    if score >= 45:
        return "mid"
    return "low"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--labels", default=str(ROOT / "eval" / "labels.csv"))
    args = parser.parse_args()

    path = Path(args.labels)
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    if not rows:
        print("labels.csv 为空")
        return

    correct = 0
    confusion = Counter()
    abs_err = 0
    for r in rows:
        result = analyze(r["jd"], r["resume"], use_llm=False)
        pred = to_bucket(int(result["score"]))
        human = r["human_label"].strip().lower()
        confusion[(human, pred)] += 1
        correct += pred == human

    n = len(rows)
    print(f"样本数：{n}")
    print(f"三分类准确率：{correct / n:.2%}")
    print("\n混淆矩阵（行=人工标签，列=模型预测）：")
    labels = ["high", "mid", "low"]
    print("        " + "".join(f"{l:>8}" for l in labels))
    for h in labels:
        print(f"{h:>6}  " + "".join(f"{confusion[(h, p)]:>8}" for p in labels))


if __name__ == "__main__":
    main()
