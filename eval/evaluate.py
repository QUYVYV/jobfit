"""评测三分类匹配效果，输出准确率、混淆矩阵和每类指标。

用法：
    python eval/evaluate.py --labels eval/labels.csv
    python eval/evaluate.py --labels eval/benchmark.csv --mode rule
    python eval/evaluate.py --labels eval/benchmark.csv --mode llm
    python eval/evaluate.py --labels eval/benchmark.csv --mode compare

human_label 取值：high / mid / low。
"""
import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.scorer import analyze  # noqa: E402

LABELS = ("high", "mid", "low")
REQUIRED_COLUMNS = {"id", "jd", "resume", "human_label"}


def to_bucket(score: int) -> str:
    if score >= 70:
        return "high"
    if score >= 45:
        return "mid"
    return "low"


def load_rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames:
            raise ValueError("CSV 缺少表头")
        missing = REQUIRED_COLUMNS - set(reader.fieldnames)
        if missing:
            raise ValueError(f"CSV 缺少字段：{', '.join(sorted(missing))}")
        rows = list(reader)

    if not rows:
        raise ValueError("labels.csv 为空")

    ids = [row.get("id", "").strip() for row in rows]
    if any(not sample_id for sample_id in ids):
        raise ValueError("存在空 id")
    if len(ids) != len(set(ids)):
        raise ValueError("存在重复 id")

    for row in rows:
        if not row.get("jd", "").strip() or not row.get("resume", "").strip():
            raise ValueError(f"样本 {row['id']} 的 JD 或简历为空")
        row["human_label"] = row["human_label"].strip().lower()
        if row["human_label"] not in LABELS:
            raise ValueError(f"样本 {row['id']} 的标签非法：{row['human_label']}")

    return rows


def metrics(human: list[str], predicted: list[str]) -> dict:
    total = len(human)
    correct = sum(expected == actual for expected, actual in zip(human, predicted))
    confusion = Counter(zip(human, predicted))
    per_class = {}
    for label in LABELS:
        tp = confusion[(label, label)]
        support = sum(confusion[(label, actual)] for actual in LABELS)
        predicted_count = sum(confusion[(expected, label)] for expected in LABELS)
        precision = tp / predicted_count if predicted_count else 0.0
        recall = tp / support if support else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class[label] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": support,
        }
    return {
        "total": total,
        "correct": correct,
        "accuracy": correct / total,
        "confusion": confusion,
        "per_class": per_class,
        "macro_f1": sum(item["f1"] for item in per_class.values()) / len(LABELS),
    }


def print_report(title: str, human: list[str], predicted: list[str], failures: int = 0) -> None:
    result = metrics(human, predicted)
    print(f"\n===== {title} =====")
    print(f"样本数：{result['total']}")
    print(f"三分类准确率：{result['accuracy']:.2%}（{result['correct']}/{result['total']}）")
    print(f"Macro F1：{result['macro_f1']:.4f}")
    if failures:
        print(f"大模型失败/回退样本：{failures}")

    print("\n混淆矩阵（行=人工标签，列=模型预测）：")
    print("        " + "".join(f"{label:>8}" for label in LABELS))
    for expected in LABELS:
        counts = [result["confusion"][(expected, actual)] for actual in LABELS]
        print(f"{expected:>6}  " + "".join(f"{count:>8}" for count in counts))

    print("\n分类指标：")
    print(f"{'label':>8} {'precision':>10} {'recall':>10} {'f1':>10} {'support':>10}")
    for label in LABELS:
        item = result["per_class"][label]
        print(
            f"{label:>8} {item['precision']:>10.4f} {item['recall']:>10.4f} "
            f"{item['f1']:>10.4f} {item['support']:>10}"
        )


def evaluate_rule(rows: list[dict]) -> tuple[list[str], list[str]]:
    human, predicted = [], []
    for index, row in enumerate(rows, 1):
        result = analyze(row["jd"], row["resume"], use_llm=False)
        score = int(result["score"])
        human.append(row["human_label"])
        predicted.append(to_bucket(score))
        print(f"规则评测 {index}/{len(rows)}：{row['id']}，score={score}", flush=True)
    return human, predicted


def evaluate_llm(rows: list[dict]) -> tuple[list[str], list[str], int]:
    human, predicted = [], []
    failures = 0
    for index, row in enumerate(rows, 1):
        result = analyze(row["jd"], row["resume"], use_llm=True)
        if result.get("mode") != "llm":
            failures += 1
            human.append(row["human_label"])
            predicted.append("failed")
            print(f"大模型评测 {index}/{len(rows)}：{row['id']}，调用失败并回退", flush=True)
            continue
        score = int(result["score"])
        human.append(row["human_label"])
        predicted.append(to_bucket(score))
        print(f"大模型评测 {index}/{len(rows)}：{row['id']}，score={score}", flush=True)
    return human, predicted, failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--labels", default=str(ROOT / "eval" / "labels.csv"))
    parser.add_argument("--mode", choices=("rule", "llm", "compare"), default="rule")
    args = parser.parse_args()

    rows = load_rows(Path(args.labels))
    distribution = Counter(row["human_label"] for row in rows)
    print(f"数据文件：{args.labels}")
    print(f"标签分布：{dict(distribution)}")

    if args.mode in ("rule", "compare"):
        human, predicted = evaluate_rule(rows)
        print_report("规则模式", human, predicted)

    failures = 0
    if args.mode in ("llm", "compare"):
        human_llm, predicted_llm, failures = evaluate_llm(rows)
        print_report("大模型模式", human_llm, predicted_llm, failures)

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
