"""
四要素分析质量评测：规则版 vs LLM 生成式（Phase 3）

在固定样本（多篇代表性摘要）上对 StructuredExtractor（规则）与 FourElementAnalyzer（LLM）
各跑一遍，按启发式指标对比，产出 Markdown 报告：
  - 四要素非空率
  - 新方案编号化率（1./2./3. 结构化方法）
  - 效果量化率（含数字）
  - 具名约束率（约束/局限/依赖/受限于…）
  - 已有方案对比度（长度代理多方案对比）
  - 总字数

用法：python test/experiments/eval_four_element.py
输出：test/experiments/output/four_element_eval.md（并打印摘要）
"""

import os
import re
import sys
from datetime import datetime
from pathlib import Path

SCRIPTS = os.path.join(os.path.dirname(__file__), "..", "..", "agent-scholar", "scripts")
sys.path.insert(0, SCRIPTS)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from utils import Paper
from paper_analyzer import StructuredExtractor
from llm_analyzer import FourElementAnalyzer

OUT_DIR = Path(__file__).parent / "output"
FIELDS = ("problem", "existing_approaches", "new_approach", "results_limitations")
FIELD_LABELS = {
    "problem": "解决的问题",
    "existing_approaches": "已有方案",
    "new_approach": "新方案",
    "results_limitations": "效果及局限",
}

# 代表性样本（method / finding-survey / empirical）
SAMPLES = [
    {
        "key": "KRCA（方法型·多组件）",
        "title": "KRCA: Efficient Root Cause Analysis in Hyper-Scale Microservices via Agentic AI",
        "abstract": (
            "In hyper-scale microservice systems, root cause localization and fault classification "
            "are challenging due to extreme dynamism and massive scale. Deep learning methods achieve "
            "high accuracy but require frequent retraining that often exceeds the system variation "
            "cycle, precluding real-time deployment. LLM-based methods leverage in-context learning "
            "but suffer the Lost-in-the-Middle problem over extremely long contexts, struggling to "
            "extract true causal relations and prone to hallucination. We propose KRCA, an end-to-end "
            "system with a progressive multi-stage pipeline: (1) API-level drilldown recursively "
            "traverses the dependency graph to extract Top-N suspect services; (2) skeleton-based "
            "causal graph instantiation maps anomalous time series onto a universal causal skeleton as "
            "a high-recall structural prior; (3) a memory-augmented multi-agent framework combines RAG "
            "and hierarchical memory for collaborative causal validation. KRCA reaches AC@1 of 0.88 "
            "and 0.79, an absolute improvement over 31% versus the strongest baseline; deployed in "
            "production for over 6 months, reducing average diagnosis time by 77.3%. It depends on the "
            "completeness of the API-level dependency graph and is bounded by underlying LLM latency."),
    },
    {
        "key": "NetLLMeval（评测型·基准）",
        "title": "Toward Agentic SysAdmin: Rethinking System Administration with AI Agents",
        "abstract": (
            "There lacks an objective, scalable mechanism to evaluate LLM capability in network "
            "management tasks, and to systematically compare how different deployment architectures "
            "affect LLM network-reasoning accuracy. Existing benchmarks rely on static reference "
            "outputs or manual expert verification: static outputs cannot adapt to diverse real network "
            "states and lack closed-loop interaction; manual verification is time-consuming, error-prone "
            "and non-scalable. We propose NetLLMeval, a framework that uses live network emulation to "
            "create controllable environments and auto-generate ground truth. We implement four solver "
            "architectures: Bulk, Bulk+ReAct, Guided Retrieval Agent, and Planner Agent. Through over "
            "24000 full-factorial experiments across 10 task types and 6 network topologies of "
            "increasing complexity, we systematically evaluate combinations of 10 base models and 4 "
            "architectures. The solver architecture raises the accuracy of a 14B open-source model from "
            "0.43 to 0.88, matching frontier trillion-parameter API models. Limitations: the emulation "
            "environment differs from real production networks, tasks are confined to 10 types and 6 "
            "topologies, and more complex agentic architectures increase token cost and latency."),
    },
    {
        "key": "ScalingLaw（发现型·理论）",
        "title": "Scaling Laws for Language Models Revisited: A Power-Law View",
        "abstract": (
            "How validation loss scales with model size, data and compute is critical for model "
            "selection and training planning. Prior work assumes smooth power-law scaling but mixes "
            "regimes, leading to misprediction when models are overtrained or data is scarce. We show "
            "that, under fixed compute, validation loss follows a smooth power law with a sharp "
            "transition near the data-constrained regime, and we derive a closed-form expression "
            "predicting the optimal token-to-parameter ratio. The law is validated on benchmarks "
            "spanning three orders of magnitude in compute. We find that the optimal ratio is roughly "
            "constant within a regime but drops sharply once the data bottleneck binds; however, the "
            "prediction breaks for overtrained small models and for mixture-of-experts architectures, "
            "where routing imbalance introduces an extra loss term not captured by the law."),
    },
]


def _to_paper(s):
    return Paper(title=s["title"], authors=["A"], venue="", year=2026, doi="",
                 abstract=s["abstract"], keywords=[], citation_count=0,
                 venue_type="", ranking="", source="eval")


def _metrics(d):
    new = d.get("new_approach", "")
    res = d.get("results_limitations", "")
    exi = d.get("existing_approaches", "")
    return {
        "四要素非空": sum(bool((d.get(f) or "").strip()) for f in FIELDS),
        "新方案编号化": bool(re.search(r"(?:^|\n)\s*(?:[1-9]|[一二三四五])[、\.\)]\s*\S", new)),
        "效果量化(含数字)": bool(re.search(r"\d(?:\.|\s|%|/|x|×|,|倍|个|月|年|步)", res)) or bool(re.search(r"\d", res)),
        "具名约束": any(w in res for w in ["约束", "局限", "constraint", "limitation", "依赖", "受限于", "未验证", "bound"]),
        "已有方案对比度(字数)": len(exi),
        "总字数": sum(len(d.get(f, "")) for f in FIELDS),
    }


def main():
    rule = StructuredExtractor()
    llm = FourElementAnalyzer(use_fulltext=False)   # 评测用摘要-only（公平对比）

    if llm.provider is None:
        print("[eval] LLM 未配置（无 key），仅跑规则版。")

    rows_rule, rows_llm = [], []
    per_paper_md = []
    for s in SAMPLES:
        p = _to_paper(s)
        rd = rule.extract(p)
        ld = llm.analyze(p) if llm.provider is not None else {f: "" for f in FIELDS}
        rm, lm = _metrics(rd), _metrics(ld)
        rows_rule.append(rm)
        rows_llm.append(lm)

        per_paper_md.append(f"### {s['key']}\n")
        per_paper_md.append(f"**标题**：{s['title']}\n")
        for f in FIELDS:
            per_paper_md.append(f"\n**{FIELD_LABELS[f]}**\n")
            per_paper_md.append(f"- 规则：{rd.get(f,'') or '（空）'}\n")
            per_paper_md.append(f"- LLM ：{ld.get(f,'') or '（空）'}\n")
        per_paper_md.append("\n---\n")

    n = len(SAMPLES)

    def agg(rows, key):
        return sum(r[key] for r in rows)

    def rate(rows, key):
        return sum(1 for r in rows if r[key]) / n

    summary = [
        "# 四要素分析评测：规则版 vs LLM 生成式\n",
        f"\n生成时间：{datetime.now():%Y-%m-%d %H:%M}  | 样本数：{n}  | LLM："
        f"{'智谱 GLM（摘要-only）' if llm.provider is not None else '未配置'}\n",
        "\n## 指标汇总（LLM 路径启用时应全面优于规则）\n",
        "| 指标 | 规则版 | LLM 版 |\n|---|---|---|",
        f"| 四要素非空合计（满分 {4*n}） | {agg(rows_rule,'四要素非空')} | {agg(rows_llm,'四要素非空')} |",
        f"| 新方案编号化率 | {rate(rows_rule,'新方案编号化')*100:.0f}% | {rate(rows_llm,'新方案编号化')*100:.0f}% |",
        f"| 效果量化率 | {rate(rows_rule,'效果量化(含数字)')*100:.0f}% | {rate(rows_llm,'效果量化(含数字)')*100:.0f}% |",
        f"| 具名约束率 | {rate(rows_rule,'具名约束')*100:.0f}% | {rate(rows_llm,'具名约束')*100:.0f}% |",
        f"| 已有方案平均字数 | {agg(rows_rule,'已有方案对比度(字数)')//n} | {agg(rows_llm,'已有方案对比度(字数)')//n} |",
        f"| 总字数 | {agg(rows_rule,'总字数')} | {agg(rows_llm,'总字数')} |",
        "\n## 逐篇对比\n",
    ] + per_paper_md

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "four_element_eval.md"
    out.write_text("".join(summary), encoding="utf-8")

    print(f"[eval] 完成，报告：{out}")
    print("\n=== 指标摘要 ===")
    for line in summary[3:11]:
        print(line.strip("|"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
