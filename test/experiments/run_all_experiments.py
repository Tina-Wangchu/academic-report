"""
批量运行全部 12 场景，并生成「预计 vs 实际」汇总报告。

用法: python run_all_experiments.py
"""

import json
import sys
import time
from pathlib import Path

from scenarios import SCENARIOS
from run_experiment import run_experiment, OUTPUT_DIR

# 每场景的「预计」基线（用于对照）
EXPECTED = {
    "E1":  {"min_dedup": 5,  "expect_hotspots": "3-5",  "lang_skeleton": "bilingual", "note": "基线全链路"},
    "E2":  {"min_dedup": 3,  "expect_hotspots": "1-3(兜底英文Title Case)", "lang_skeleton": "bilingual", "note": "非AI兜底聚类"},
    "E3":  {"min_dedup": 0,  "expect_hotspots": "0-2",  "lang_skeleton": "bilingual", "note": "高被引≥100，过滤后少"},
    "E4":  {"min_dedup": 0,  "expect_hotspots": "1-3",  "lang_skeleton": "bilingual", "note": "仅SCI/EI venue"},
    "E5":  {"min_dedup": 3,  "expect_hotspots": "2-4",  "lang_skeleton": "bilingual", "note": "剔除预印本(无arXiv)"},
    "E6":  {"min_dedup": 0,  "expect_hotspots": "0-2",  "lang_skeleton": "bilingual", "note": "近1周，少结果"},
    "E7":  {"min_dedup": 5,  "expect_hotspots": "3-5",  "lang_skeleton": "zh(纯中文)", "note": "纯中文报告"},
    "E8":  {"min_dedup": 5,  "expect_hotspots": "3-5",  "lang_skeleton": "en(纯英文)", "note": "纯英文报告"},
    "E9":  {"min_dedup": 5,  "expect_hotspots": "3-5",  "lang_skeleton": "bilingual", "note": "HTML输出"},
    "E10": {"min_dedup": 8,  "expect_hotspots": "3-6(多)", "lang_skeleton": "bilingual", "note": "宽泛多热点，速览增长"},
    "E11": {"min_dedup": 0,  "expect_hotspots": "0",    "lang_skeleton": "bilingual", "note": "空结果不崩"},
    "E12": {"min_dedup": 2,  "expect_hotspots": "1-3",  "lang_skeleton": "bilingual", "note": "citation≥50"},
}


def run_all():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    all_metrics = []
    t_total = time.time()

    for sc in SCENARIOS:
        print(f"\n=== {sc['id']} {sc['desc']} ===", flush=True)
        try:
            m = run_experiment(sc)
        except Exception as e:
            m = {"id": sc["id"], "desc": sc["desc"], "fatal_error": f"{type(e).__name__}: {e}"}
            print(f"  ✗ 致命错误: {e}")
        all_metrics.append(m)
        print(f"  源={m.get('per_source')} 去重={m.get('pre_dedup')}→{m.get('post_dedup')} "
              f"过滤后={m.get('after_filter')} 热点={len(m.get('hotspots',{}))} "
              f"报告={m.get('report_chars','?')}字 "
              f"{'OK' if m.get('report_ok') else 'FAIL'}", flush=True)

    print(f"\n全部完成，总耗时 {round(time.time()-t_total,1)}s")

    # 汇总 JSON
    (OUTPUT_DIR / "all_metrics.json").write_text(
        json.dumps(all_metrics, ensure_ascii=False, indent=2), encoding="utf-8")

    # 汇总 Markdown 对照表
    write_summary(all_metrics)
    print(f"汇总: {OUTPUT_DIR / 'summary.md'}")


def write_summary(all_metrics):
    lines = ["# 实验汇总：预计 vs 实际\n"]
    lines.append(f"运行时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    lines.append("| ID | 描述 | 预计 | arXiv | S2 | OpenAlex | 去重后 | 过滤后 | 热点数 | 报告字符 | 奠基离线回退 | 状态 |")
    lines.append("|----|------|------|-------|-----|----------|--------|--------|--------|----------|-------------|------|")
    for m in all_metrics:
        exp = EXPECTED.get(m["id"], {})
        per = m.get("per_source", {})
        hotspots = m.get("hotspots", {})
        ok = "✅" if m.get("report_ok") else "❌"
        exp_str = f"热点{exp.get('expect_hotspots','?')}"
        lines.append(
            f"| {m['id']} | {m.get('desc','')} | {exp_str} | "
            f"{per.get('arxiv','-')} | {per.get('s2','-')} | {per.get('openalex','-')} | "
            f"{m.get('post_dedup','-')} | {m.get('after_filter','-')} | "
            f"{len(hotspots)} | {m.get('report_chars','-')} | "
            f"{'是' if m.get('foundational_offline_fallback') else '否'} | {ok} |"
        )

    lines.append("\n## 各场景热点分布\n")
    for m in all_metrics:
        hotspots = m.get("hotspots", {})
        if hotspots:
            dist = "、".join(f"{k}({v})" for k, v in hotspots.items())
        else:
            dist = "（无）"
        lines.append(f"- **{m['id']}** {m.get('desc','')}: {dist}")

    lines.append("\n## 预计要点对照\n")
    for m in all_metrics:
        exp = EXPECTED.get(m["id"], {})
        lines.append(f"- **{m['id']}** {exp.get('note','')}: 预计 {exp.get('expect_hotspots','?')} / "
                     f"实际 {len(m.get('hotspots',{}))} 热点")

    (OUTPUT_DIR / "summary.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    run_all()
