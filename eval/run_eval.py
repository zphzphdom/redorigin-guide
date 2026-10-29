# -*- coding: utf-8 -*-
"""真实评测：对 testset.jsonl 逐条跑 Agent，统计意图准确率、时延与来源覆盖。

运行：python eval/run_eval.py
输出：eval/results.json（供报告与图表使用）
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agent.respond import Agent  # noqa: E402

LABEL_ALIAS = {"kb": "history", "history": "history"}


def main() -> None:
    agent = Agent()
    rows = []
    for line in (ROOT / "eval" / "testset.jsonl").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        item = json.loads(line)
        mem: dict = {}
        t0 = time.perf_counter()
        reply = agent.answer(item["q"], mem)
        ms = (time.perf_counter() - t0) * 1000
        got = LABEL_ALIAS.get(reply.intent, reply.intent)
        exp = LABEL_ALIAS.get(item["expected"], item["expected"])
        rows.append({
            "q": item["q"], "expected": exp, "got": got, "ok": got == exp,
            "latency_ms": round(ms, 2), "sources": len(reply.sources),
            "chars": len(reply.text), "intent": reply.intent,
        })

    total = len(rows)
    correct = sum(1 for r in rows if r["ok"])
    by_intent: dict[str, dict[str, int]] = {}
    for r in rows:
        b = by_intent.setdefault(r["expected"], {"n": 0, "ok": 0})
        b["n"] += 1
        b["ok"] += int(r["ok"])
    lat = sorted(r["latency_ms"] for r in rows)
    result = {
        "total": total,
        "correct": correct,
        "accuracy": round(correct / total, 4),
        "by_intent": {k: {**v, "acc": round(v["ok"] / v["n"], 3)} for k, v in by_intent.items()},
        "latency_ms": {
            "avg": round(sum(lat) / total, 2),
            "p50": round(lat[total // 2], 2),
            "p95": round(lat[min(total - 1, int(total * 0.95))], 2),
            "max": round(lat[-1], 2),
        },
        "source_coverage": round(sum(1 for r in rows if r["sources"] > 0) / total, 4),
        "avg_chars": round(sum(r["chars"] for r in rows) / total, 1),
        "kb_docs": len(agent.kb.docs),
        "errors": [r for r in rows if not r["ok"]],
        "rows": rows,
    }
    (ROOT / "eval" / "results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"评测集 {total} 条｜意图准确率 {result['accuracy']:.1%}｜平均时延 {result['latency_ms']['avg']} ms"
          f"｜P95 {result['latency_ms']['p95']} ms｜含来源比例 {result['source_coverage']:.1%}")
    for k, v in sorted(result["by_intent"].items()):
        print(f"  {k:10s} {v['ok']}/{v['n']}  {v['acc']:.0%}")
    if result["errors"]:
        print("未命中：")
        for e in result["errors"]:
            print(f"  - {e['q']}  期望 {e['expected']} 实际 {e['got']}")


if __name__ == "__main__":
    main()
