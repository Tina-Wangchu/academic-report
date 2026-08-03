"""
测试 llm_analyzer.py（四要素 LLM 分析，Phase 1）
覆盖：ZhipuProvider 请求构造、FourElementAnalyzer 分层（LLM→规则）、JSON/标签解析、缓存、config。
不联网：mock requests.post + FakeProvider；强制显式传 provider，避免读到真实 env token。
"""

import json
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'academic-report', 'scripts'))

from utils import Paper
import llm_analyzer
from llm_analyzer import ZhipuProvider, FourElementAnalyzer


def _paper(title="KRCA: Root Cause Analysis",
           abstract="A method abstract describing the approach and its results."):
    return Paper(title=title, authors=["A"], venue="", year=2026, doi="",
                 abstract=abstract, keywords=[], citation_count=0,
                 venue_type="", ranking="", source="test")


# ----------------------------- Fake provider ---------------------------- #

class FakeProvider:
    """模拟 ZhipuProvider：返回预设文本；记录调用。"""
    model = "fake-model"

    def __init__(self, return_text="", raise_exc=None):
        self._text = return_text
        self._exc = raise_exc
        self.calls = []

    def summarize(self, system_prompt, user_text):
        self.calls.append((system_prompt, user_text))
        if self._exc:
            raise self._exc
        return self._text


# --------------------------- ZhipuProvider 请求 -------------------------- #

class TestZhipuProviderRequest:
    def test_posts_to_messages_endpoint_with_bearer(self, monkeypatch):
        captured = {}

        class FakeResp:
            status_code = 200
            def json(self):
                return {"content": [{"type": "text", "text": '{"problem":"p"}'}]}

        def fake_post(url, headers=None, json=None, timeout=None):
            captured.update(url=url, headers=headers, body=json)
            return FakeResp()

        monkeypatch.setattr(llm_analyzer.requests, "post", fake_post)
        p = ZhipuProvider(api_key="k.xy", base_url="https://open.bigmodel.cn/api/anthropic",
                         model="glm-5-turbo", min_interval=0)
        out = p.summarize("SYS", "USER")
        assert out == '{"problem":"p"}'
        assert captured["url"].endswith("/v1/messages")
        assert captured["headers"]["Authorization"] == "Bearer k.xy"
        assert captured["headers"]["x-api-key"] == "k.xy"
        assert captured["headers"]["anthropic-version"] == "2023-06-01"
        assert captured["body"]["model"] == "glm-5-turbo"
        assert captured["body"]["temperature"] == 0
        assert captured["body"]["system"] == "SYS"
        assert captured["body"]["messages"][0]["content"] == "USER"

    def test_raises_on_http_error(self, monkeypatch):
        class FakeResp:
            status_code = 401
            text = "unauthorized"
            def json(self):
                return {}
        monkeypatch.setattr(llm_analyzer.requests, "post",
                            lambda *a, **k: FakeResp())
        p = ZhipuProvider(api_key="bad", base_url="https://x/api/anthropic",
                         model="m", min_interval=0)
        with pytest.raises(RuntimeError):
            p.summarize("s", "u")

    def test_429_retries_then_succeeds(self, monkeypatch):
        import time as _time
        monkeypatch.setattr(_time, "sleep", lambda *a: None)   # 不真等
        calls = {"n": 0}

        class Resp:
            def __init__(self, code, payload):
                self.status_code = code
                self._p = payload
                self.text = ""
            def json(self):
                return self._p

        def fake_post(*a, **k):
            calls["n"] += 1
            if calls["n"] == 1:
                return Resp(429, {})
            return Resp(200, {"content": [{"type": "text", "text": "ok"}]})

        monkeypatch.setattr(llm_analyzer.requests, "post", fake_post)
        p = ZhipuProvider(api_key="k", base_url="https://x/api/anthropic",
                         model="m", min_interval=0)
        out = p.summarize("s", "u")
        assert out == "ok"
        assert calls["n"] == 2                      # 重试一次后成功


# ------------------------- FourElementAnalyzer -------------------------- #

VALID_JSON = json.dumps({
    "problem": "在超大规模微服务系统中如何高效定位根因。",
    "existing": "深度学习方法需频繁重训；LLM 方法易陷入 Lost in the Middle。",
    "new": "提出 KRCA 系统：1. API-level drilldown；2. 因果骨架图；3. 多智能体框架。",
    "results": "AC@1 达 0.88/0.79，提升 31%。约束：依赖依赖图完整性。",
}, ensure_ascii=False)


class TestLLMTier:
    def test_llm_valid_json(self, tmp_path):
        prov = FakeProvider(return_text=VALID_JSON)
        out = FourElementAnalyzer(provider=prov, cache_path=tmp_path / "c.json").analyze(_paper())
        assert out["analysis_source"] == "llm"
        assert "根因" in out["problem"]
        assert "1." in out["new_approach"]            # 编号化
        assert "0.88" in out["results_limitations"]
        assert len(prov.calls) == 1

    def test_llm_json_in_code_fence(self, tmp_path):
        fenced = "```json\n" + VALID_JSON + "\n```"
        prov = FakeProvider(return_text=fenced)
        out = FourElementAnalyzer(provider=prov, cache_path=tmp_path / "c.json").analyze(_paper())
        assert out["analysis_source"] == "llm"
        assert "根因" in out["problem"]

    def test_llm_label_text_fallback_parse(self, tmp_path):
        text = ("解决的问题：如何定位根因。\n"
                "已有方案：深度学习需重训。\n"
                "新方案：1. drilldown 2. 因果图。\n"
                "效果及局限：AC@1=0.88。约束：依赖图。")
        prov = FakeProvider(return_text=text)
        out = FourElementAnalyzer(provider=prov, cache_path=tmp_path / "c.json").analyze(_paper())
        assert out["analysis_source"] == "llm"
        assert "定位根因" in out["problem"]
        assert "drilldown" in out["new_approach"]

    def test_llm_garbage_falls_back_to_rule(self, tmp_path):
        prov = FakeProvider(return_text="本服务无法回答该问题。")  # 无法解析
        out = FourElementAnalyzer(provider=prov, cache_path=tmp_path / "c.json").analyze(
            _paper(abstract="We propose X. It outperforms baselines."))
        assert out["analysis_source"] == "rule"
        assert out["new_approach"]                    # 规则仍给出新方案

    def test_llm_exception_falls_back_to_rule(self, tmp_path):
        prov = FakeProvider(raise_exc=RuntimeError("network down"))
        out = FourElementAnalyzer(provider=prov, cache_path=tmp_path / "c.json").analyze(
            _paper(abstract="We propose X. It outperforms baselines."))
        assert out["analysis_source"] == "rule"

    def test_no_provider_uses_rule(self, tmp_path):
        out = FourElementAnalyzer(provider=None, cache_path=tmp_path / "c.json").analyze(
            _paper(abstract="We propose X. It outperforms baselines."))
        assert out["analysis_source"] == "rule"
        assert out["new_approach"]


class TestCache:
    def test_cache_hit_skips_provider(self, tmp_path):
        cp = tmp_path / "c.json"
        prov = FakeProvider(return_text=VALID_JSON)
        a = FourElementAnalyzer(provider=prov, cache_path=cp)
        a.analyze(_paper())                           # 首次：调用 LLM
        assert len(prov.calls) == 1
        prov2 = FakeProvider(return_text=VALID_JSON)
        b = FourElementAnalyzer(provider=prov2, cache_path=cp)
        out = b.analyze(_paper())                     # 二次：应命中缓存
        assert out["analysis_source"] == "cache"
        assert len(prov2.calls) == 0                  # 未再调 LLM
        assert "根因" in out["problem"]

    def test_refresh_ignores_cache(self, tmp_path):
        cp = tmp_path / "c.json"
        prov = FakeProvider(return_text=VALID_JSON)
        FourElementAnalyzer(provider=prov, cache_path=cp).analyze(_paper())
        prov2 = FakeProvider(return_text=VALID_JSON)
        FourElementAnalyzer(provider=prov2, cache_path=cp, use_cache=False).analyze(_paper())
        assert len(prov2.calls) == 1                  # use_cache=False → 再调


# ------------------------- 语言控制（zh/en/bilingual）--------------------- #

class TestLanguageControl:
    """四要素 LLM 分析必须按 intent.language 切换输出语种（修复点：旧版恒中文）。"""

    def test_prompt_zh_directive(self):
        p = llm_analyzer._system_prompt("zh")
        assert "输出语言：**中文**" in p
        assert "双语" not in p
        assert "Output language: **English**" not in p

    def test_prompt_en_directive(self):
        p = llm_analyzer._system_prompt("en")
        assert "Output language: **English**" in p
        assert "输出语言：**中文**" not in p
        assert "双语" not in p

    def test_prompt_bilingual_directive(self):
        p = llm_analyzer._system_prompt("bilingual")
        assert "输出语言：**双语**" in p
        assert "Output language: **bilingual**" in p   # 中英两条指令都在

    def test_prompt_invalid_defaults_bilingual(self):
        assert llm_analyzer._system_prompt("fr") == llm_analyzer._system_prompt("bilingual")
        assert llm_analyzer._system_prompt(None) == llm_analyzer._system_prompt("bilingual")
        assert llm_analyzer._system_prompt("") == llm_analyzer._system_prompt("bilingual")

    def test_analyze_passes_en_prompt_to_provider(self, tmp_path):
        prov = FakeProvider(return_text=VALID_JSON)
        FourElementAnalyzer(provider=prov, cache_path=tmp_path / "c.json").analyze(
            _paper(), language="en")
        assert "Output language: **English**" in prov.calls[0][0]

    def test_analyze_passes_bilingual_prompt_to_provider(self, tmp_path):
        prov = FakeProvider(return_text=VALID_JSON)
        FourElementAnalyzer(provider=prov, cache_path=tmp_path / "c.json").analyze(
            _paper(), language="bilingual")
        assert "输出语言：**双语**" in prov.calls[0][0]

    def test_default_language_is_bilingual(self, tmp_path):
        """analyze 不传 language → 默认 bilingual prompt。"""
        prov = FakeProvider(return_text=VALID_JSON)
        FourElementAnalyzer(provider=prov, cache_path=tmp_path / "c.json").analyze(_paper())
        assert "输出语言：**双语**" in prov.calls[0][0]

    def test_cache_key_differs_by_language(self, tmp_path):
        """同论文不同 language → 不同缓存键 → 各自调用 LLM（不串用，避免 zh 命中 bilingual）。"""
        prov = FakeProvider(return_text=VALID_JSON)
        a = FourElementAnalyzer(provider=prov, cache_path=tmp_path / "c.json")
        a.analyze(_paper(), language="zh")
        a.analyze(_paper(), language="en")          # 同论文，不同语言
        assert len(prov.calls) == 2                 # 两次都调 LLM（键不同）

    def test_cache_hit_same_language(self, tmp_path):
        """同论文同 language → 命中缓存，只调一次 LLM。"""
        prov = FakeProvider(return_text=VALID_JSON)
        a = FourElementAnalyzer(provider=prov, cache_path=tmp_path / "c.json")
        a.analyze(_paper(), language="bilingual")
        a.analyze(_paper(), language="bilingual")   # 同语言 → 缓存命中
        assert len(prov.calls) == 1

    def test_cache_key_deterministic(self):
        a = FourElementAnalyzer._cache_key(_paper())
        b = FourElementAnalyzer._cache_key(_paper())
        c = FourElementAnalyzer._cache_key(_paper(title="Different"))
        assert a == b
        assert a != c


# ------------------------------- config --------------------------------- #

# ---------------------------- Phase 2: fulltext -------------------------- #

class TestFulltextHelpers:
    def test_to_arxiv_pdf_url(self):
        from llm_analyzer import _to_arxiv_pdf_url
        assert _to_arxiv_pdf_url("http://arxiv.org/abs/2607.01788v1") == \
            "https://arxiv.org/pdf/2607.01788v1"
        assert _to_arxiv_pdf_url("https://arxiv.org/pdf/2607.01788") == \
            "https://arxiv.org/pdf/2607.01788"
        assert _to_arxiv_pdf_url("https://openalex.org/W123") is None
        assert _to_arxiv_pdf_url("") is None

    def test_extract_key_sections_finds_headings(self):
        from llm_analyzer import _extract_key_sections
        text = ("Intro text. " * 50
                + "\n3 Method\nWe build a pipeline with three stages. " * 10
                + "\n4 Results\nAC@1 reaches 0.88. " * 10
                + "\n5 Limitations\nDepends on graph completeness. " * 5)
        out = _extract_key_sections(text, max_chars=3000)
        assert "Method" in out
        assert "0.88" in out
        assert "Limitations" in out

    def test_extract_key_sections_fallback_truncation(self):
        from llm_analyzer import _extract_key_sections
        text = "x" * 5000
        out = _extract_key_sections(text, max_chars=1000)
        assert len(out) <= 1000

    def test_input_text_includes_fulltext(self):
        from llm_analyzer import FourElementAnalyzer
        p = _paper(abstract="abs text")
        base = FourElementAnalyzer._input_text(p, "")
        with_ft = FourElementAnalyzer._input_text(p, "METHOD STUFF")
        assert "METHOD STUFF" not in base
        assert "METHOD STUFF" in with_ft
        assert "abs text" in with_ft

    def test_fetch_fulltext_none_for_non_arxiv(self):
        from llm_analyzer import _fetch_fulltext
        # 非 arXiv paper → 不发请求，直接 ""
        assert _fetch_fulltext(_paper(), max_chars=100) == ""

    def test_fetch_fulltext_mocked_arxiv(self, monkeypatch):
        import llm_analyzer as la
        # mock requests.get 返回伪响应（含 headers/text/json 供新流程用）
        class FakeResp:
            status_code = 200
            content = b"%PDF-fake"
            headers = {"content-type": "application/pdf"}
            text = ""
            def json(self):
                return {}
        monkeypatch.setattr(la.requests, "get", lambda *a, **k: FakeResp())
        monkeypatch.setattr(la, "_pdf_bytes_to_text",
                            lambda data: "\nMethod\nWe do X.\nResults\n0.9 acc.")
        out = la._fetch_fulltext(
            _paper(), max_chars=500)  # _paper 默认 doi，无 url/pdf_url → 候选空 → ""
        assert out == ""
        # 给一个 arXiv url 再测
        p = _paper()
        p.url = "https://arxiv.org/abs/2607.01788v1"
        out2 = la._fetch_fulltext(p, max_chars=500)
        assert "Method" in out2 and "0.9" in out2


class TestNoAbstractForcesFulltext:
    def test_empty_abstract_forces_fulltext_even_if_disabled(self, monkeypatch, tmp_path):
        import llm_analyzer as la
        monkeypatch.setattr(la, "_fetch_fulltext",
                            lambda p, *a, **k: "FULLTEXT BODY")
        prov = FakeProvider(return_text='{"problem":"p","existing":"e","new":"n","results":"r"}')
        p = _paper(abstract="")                       # 无摘要
        out = FourElementAnalyzer(provider=prov, cache_path=tmp_path / "c.json",
                                  use_fulltext=False).analyze(p)
        # use_fulltext=False 但无摘要 → 仍抓全文，并喂给 LLM
        assert "FULLTEXT BODY" in prov.calls[0][1]
        assert out["analysis_source"] == "llm"

    def test_abstract_present_skips_fulltext_when_disabled(self, monkeypatch, tmp_path):
        import llm_analyzer as la
        called = []
        monkeypatch.setattr(la, "_fetch_fulltext",
                            lambda p, *a, **k: called.append(1) or "FT")
        prov = FakeProvider(return_text='{"problem":"p","existing":"e","new":"n","results":"r"}')
        p = _paper(abstract="has abstract")           # 有摘要 + use_fulltext=False
        FourElementAnalyzer(provider=prov, cache_path=tmp_path / "c.json",
                            use_fulltext=False).analyze(p)
        assert called == []                           # 不抓全文

    def test_unavailable_when_no_abstract_and_no_fulltext(self, monkeypatch, tmp_path):
        """闭源：无摘要 + 抓不到全文 → unavailable，不调 LLM，给检索链接"""
        import llm_analyzer as la
        monkeypatch.setattr(la, "_fetch_fulltext", lambda p, *a, **k: "")  # 全文抓不到
        prov = FakeProvider(return_text="should-not-be-called")
        p = _paper(abstract="", )  # 无摘要
        p.doi = "10.1038/test"
        out = FourElementAnalyzer(provider=prov, cache_path=tmp_path / "c.json").analyze(p)
        assert out["analysis_source"] == "unavailable"
        assert len(prov.calls) == 0                   # 未浪费 LLM 调用
        assert "doi.org/10.1038/test" in out["access_url"]
        assert all(not out[k] for k in
                   ("problem", "existing_approaches", "new_approach", "results_limitations"))


class TestGetLLMConfig:
    def test_reads_env_and_defaults(self, monkeypatch):
        # 隔离真实 env：删掉 ANTHROPIC_*，设显式 LLM_* 值
        for k in ("ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL"):
            monkeypatch.delenv(k, raising=False)
        monkeypatch.setenv("LLM_ENABLED", "true")
        monkeypatch.setenv("LLM_API_KEY", "testkey")
        monkeypatch.setenv("LLM_MODEL", "glm-4-flash")
        from config_manager import ConfigManager
        cfg = ConfigManager().get_llm_config()
        assert cfg["enabled"] is True
        assert cfg["api_key"] == "testkey"
        assert cfg["model"] == "glm-4-flash"
        assert "bigmodel.cn" in cfg["base_url"]       # 默认智谱端点

    def test_disabled_when_no_key(self, monkeypatch):
        for k in ("ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL", "LLM_API_KEY",
                  "ZHIPU_API_KEY", "LLM_ENABLED"):
            monkeypatch.delenv(k, raising=False)
        # 阻止 ConfigManager 从 ~/.hermes/.env 重新注入 key
        monkeypatch.setattr("config_manager.ConfigManager._load_env_file",
                            lambda self: None)
        from config_manager import ConfigManager
        cfg = ConfigManager().get_llm_config()
        assert cfg["enabled"] is False
        assert cfg["api_key"] == ""
