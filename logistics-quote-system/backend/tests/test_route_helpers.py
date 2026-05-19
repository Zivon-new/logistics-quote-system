# backend/tests/test_route_helpers.py
"""Tests for pure utility functions in route_helpers.py."""
import pytest
from route_helpers import sf, dedupe_agents


# ── sf (safe float conversion) ────────────────────────────────────────────────

class TestSf:
    def test_none_returns_default(self):
        assert sf(None) == 0.0

    def test_none_with_custom_default(self):
        assert sf(None, default=1.5) == 1.5

    def test_valid_int(self):
        assert sf(3) == 3.0

    def test_valid_float(self):
        assert sf(3.14) == pytest.approx(3.14)

    def test_valid_numeric_string(self):
        assert sf("3.5") == pytest.approx(3.5)

    def test_invalid_string_returns_default(self):
        assert sf("abc") == 0.0

    def test_empty_string_returns_default(self):
        assert sf("") == 0.0

    def test_zero_is_preserved(self):
        assert sf(0) == 0.0

    def test_negative_value(self):
        assert sf(-10.5) == pytest.approx(-10.5)


# ── dedupe_agents ─────────────────────────────────────────────────────────────

class TestDedupeAgents:
    def test_empty_list(self):
        assert dedupe_agents([]) == {}

    def test_single_agent(self):
        agents = [{'代理商': 'A公司', '运输方式': '海运'}]
        result = dedupe_agents(agents)
        assert len(result) == 1
        assert '|'.join(['A公司', '海运']) in result

    def test_same_name_different_transport_both_kept(self):
        """Prior learning: composite key must use (代理商, 运输方式) — name alone is wrong."""
        agents = [
            {'代理商': 'A公司', '运输方式': '海运'},
            {'代理商': 'A公司', '运输方式': '空运'},
        ]
        result = dedupe_agents(agents)
        assert len(result) == 2

    def test_same_key_no_fees_first_wins(self):
        agents = [
            {'代理商': 'A公司', '运输方式': '海运', 'extra': 'first'},
            {'代理商': 'A公司', '运输方式': '海运', 'extra': 'second'},
        ]
        result = dedupe_agents(agents)
        assert len(result) == 1
        assert result['A公司|海运']['extra'] == 'first'

    def test_same_key_second_has_fee_items_wins(self):
        agents = [
            {'代理商': 'A公司', '运输方式': '海运', 'extra': 'no-fees'},
            {'代理商': 'A公司', '运输方式': '海运', 'extra': 'has-fees', 'fee_items': [{'费用类型': '海运费'}]},
        ]
        result = dedupe_agents(agents)
        assert result['A公司|海运']['extra'] == 'has-fees'

    def test_same_key_second_has_summary_wins(self):
        agents = [
            {'代理商': 'B公司', '运输方式': '空运'},
            {'代理商': 'B公司', '运输方式': '空运', 'summary': {'小计': 1000}},
        ]
        result = dedupe_agents(agents)
        assert 'summary' in result['B公司|空运']

    def test_agent_with_empty_name_excluded(self):
        agents = [
            {'代理商': '', '运输方式': '海运'},
            {'代理商': 'A公司', '运输方式': '海运'},
        ]
        result = dedupe_agents(agents)
        assert len(result) == 1
        assert 'A公司|海运' in result

    def test_agent_with_missing_name_key_excluded(self):
        agents = [
            {'运输方式': '海运'},
            {'代理商': 'A公司', '运输方式': '海运'},
        ]
        result = dedupe_agents(agents)
        assert len(result) == 1

    def test_multiple_distinct_agents_all_kept(self):
        agents = [
            {'代理商': 'A公司', '运输方式': '海运'},
            {'代理商': 'B公司', '运输方式': '空运'},
            {'代理商': 'C公司', '运输方式': '专线'},
        ]
        result = dedupe_agents(agents)
        assert len(result) == 3
