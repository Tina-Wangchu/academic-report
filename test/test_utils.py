"""
测试 utils.py 的纯函数：format_apa_citation（APA 7th）、parse_date_range、
clean_doi、validate_email、safe_filename。不联网。
"""

import pytest
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'academic-report', 'scripts'))

from utils import Paper, format_apa_citation, parse_date_range, clean_doi, validate_email, safe_filename


def _p(authors=None, year=2024, title="T", venue="V", doi=""):
    return Paper(title=title, authors=authors or ["Author A"], venue=venue,
                 year=year, doi=doi, abstract="", keywords=[], citation_count=0,
                 venue_type="journal", ranking="普通", source="test")


# --------------------------- APA 7th --------------------------- #

class TestAPA:
    def test_single_author(self):
        assert format_apa_citation(_p(authors=["Smith J"], year=2024)) == \
            "Smith J (2024). T. *V*"

    def test_two_authors_oxford_comma(self):
        """两位作者用 ', & '（APA 7th Oxford 逗号）"""
        out = format_apa_citation(_p(authors=["Smith J", "Lee K"]))
        assert "Smith J, & Lee K" in out

    def test_three_authors_all_listed(self):
        out = format_apa_citation(_p(authors=["A", "B", "C"]))
        assert "A, B, & C" in out

    def test_twenty_authors_all_listed(self):
        """≤20 位全部列出（APA 7th），最后一位前用 & """
        auths = [f"A{i}" for i in range(20)]
        out = format_apa_citation(_p(authors=auths))
        assert "..." not in out
        assert out.startswith("A0, A1,")
        assert "& A19" in out

    def test_over_twenty_authors_ellipsis(self):
        """>20 位：前 19 + ... + 最后 1 位"""
        auths = [f"A{i}" for i in range(25)]
        out = format_apa_citation(_p(authors=auths))
        assert "..." in out
        assert "A18" in out           # 前 19 的最后一位（A0..A18）
        assert "A24" in out           # 最后一位
        assert "A19" not in out       # A19 被省略

    def test_doi_appended(self):
        out = format_apa_citation(_p(authors=["X"], doi="10.1234/abc"))
        assert "https://doi.org/10.1234/abc" in out

    def test_empty_authors(self):
        p = Paper(title="T", authors=[], venue="V", year=2024, doi="",
                  abstract="", keywords=[], citation_count=0,
                  venue_type="journal", ranking="普通", source="test")
        out = format_apa_citation(p)
        assert out.startswith("(2024)")


# ------------------------ parse_date_range --------------------- #

class TestParseDateRange:
    def test_absolute_range(self):
        s, e = parse_date_range("2023-01-01至2023-12-31")
        assert s == datetime(2023, 1, 1)
        assert e == datetime(2023, 12, 31)

    def test_absolute_range_tilde(self):
        s, e = parse_date_range("2024-06-01 ~ 2024-06-30")
        assert s == datetime(2024, 6, 1)
        assert e == datetime(2024, 6, 30)

    def test_single_year(self):
        s, e = parse_date_range("2024年")
        assert s == datetime(2024, 1, 1)
        assert e.year == 2024 and e.month == 12

    def test_relative_years(self):
        s, e = parse_date_range("近1年")
        assert e - s <= timedelta(days=366)
        assert e - s >= timedelta(days=364)

    def test_relative_weeks(self):
        s, e = parse_date_range("近2周")
        assert e - s >= timedelta(days=13)
        assert e - s <= timedelta(days=15)

    def test_unlimited(self):
        s, e = parse_date_range("不限")
        assert s is None

    def test_none_input(self):
        assert parse_date_range("") == (None, None)
        assert parse_date_range(None) == (None, None)

    def test_no_match(self):
        assert parse_date_range("hello world") == (None, None)


# ------------------------- 其它工具 ---------------------------- #

class TestOtherUtils:
    def test_clean_doi(self):
        assert clean_doi("https://doi.org/10.1234/abc") == "10.1234/abc"
        assert clean_doi("10.1234/abc") == "10.1234/abc"
        assert clean_doi("") == ""

    def test_validate_email(self):
        assert validate_email("a@b.com") is True
        assert validate_email("not-an-email") is False

    def test_safe_filename(self):
        assert "/" not in safe_filename("a/b\\c:d")
        assert safe_filename("normal") == "normal"
