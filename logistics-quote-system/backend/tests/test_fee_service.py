# backend/tests/test_fee_service.py
"""Tests for pure utility functions in fee_service.py."""
import pytest
from types import SimpleNamespace
from fee_service import convert_min_fee, apply_min_fee, clean_goods_detail, clean_goods_total


def _fee_item(**overrides):
    """Build a fake ORM fee-item object with sensible defaults."""
    defaults = dict(
        费用ID=1, 费用类型="海运费", 单价=100, 单位="箱", 数量=1,
        最低收费=None, 最低收费币种=None, 币种="RMB",
        原币金额=100.0, 人民币金额=700.0, 备注=None, 参与核算=1,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


# ── convert_min_fee ───────────────────────────────────────────────────────────

class TestConvertMinFee:
    def test_same_currency_returns_unchanged(self):
        rates = {'USD': 7.0, 'RMB': 1.0}
        assert convert_min_fee(100, 'USD', 'USD', rates) == 100

    def test_cross_currency_uses_rmb_as_pivot(self):
        rates = {'USD': 7.0, 'EUR': 7.7, 'RMB': 1.0}
        # 100 EUR -> RMB -> USD: 100 * 7.7 / 7.0
        assert convert_min_fee(100, 'EUR', 'USD', rates) == pytest.approx(100 * 7.7 / 7.0)

    def test_missing_currency_defaults_to_rmb_rate(self):
        rates = {'RMB': 1.0}
        assert convert_min_fee(100, 'XXX', 'RMB', rates) == pytest.approx(100 * 1.0 / 1.0)

    def test_zero_target_rate_returns_original(self):
        rates = {'USD': 0.0, 'RMB': 1.0}
        assert convert_min_fee(100, 'RMB', 'USD', rates) == 100


# ── apply_min_fee ─────────────────────────────────────────────────────────────

class TestApplyMinFee:
    def test_fee_above_minimum_unchanged(self):
        items = [_fee_item(最低收费=50, 最低收费币种="RMB", 原币金额=100.0, 人民币金额=700.0)]
        result = apply_min_fee(items)
        assert result[0]["原币金额"] == 100.0
        assert result[0]["人民币金额"] == 700.0

    def test_fee_below_minimum_bumped_and_rmb_scaled_proportionally(self):
        items = [_fee_item(最低收费=200, 最低收费币种="RMB", 原币金额=100.0, 人民币金额=700.0)]
        result = apply_min_fee(items)
        assert result[0]["原币金额"] == 200.0
        # RMB scaled by the same ratio the original-currency amount was bumped
        assert result[0]["人民币金额"] == pytest.approx(1400.0)

    def test_no_minimum_fee_leaves_amounts_untouched(self):
        items = [_fee_item(最低收费=None, 原币金额=100.0, 人民币金额=700.0)]
        result = apply_min_fee(items)
        assert result[0]["原币金额"] == 100.0
        assert result[0]["人民币金额"] == 700.0

    def test_zero_original_amount_keeps_rmb_as_raw(self):
        items = [_fee_item(最低收费=200, 最低收费币种="RMB", 原币金额=0.0, 人民币金额=0.0)]
        result = apply_min_fee(items)
        assert result[0]["原币金额"] == 200.0
        assert result[0]["人民币金额"] == 0.0

    def test_cross_currency_minimum_fee_converted_before_comparison(self):
        rates = {'USD': 7.0, 'RMB': 1.0}
        # min fee 30 USD -> 210 RMB, which exceeds the 100 RMB original amount
        items = [_fee_item(最低收费=30, 最低收费币种="USD", 币种="RMB", 原币金额=100.0, 人民币金额=100.0)]
        result = apply_min_fee(items, rates)
        assert result[0]["原币金额"] == pytest.approx(210.0)

    def test_default_rates_used_when_none_provided(self):
        items = [_fee_item(最低收费=50, 最低收费币种="RMB", 币种="RMB", 原币金额=100.0, 人民币金额=700.0)]
        result = apply_min_fee(items, rates=None)
        assert result[0]["原币金额"] == 100.0


# ── clean_goods_detail ────────────────────────────────────────────────────────

class TestCleanGoodsDetail:
    def test_strips_frontend_and_db_generated_keys(self):
        goods = {"货物ID": 1, "路线ID": 2, "创建时间": "x", "路线索引": 0,
                 "_index": 0, "总货值": 100, "品名": "电子产品"}
        result = clean_goods_detail(goods)
        for key in ["货物ID", "路线ID", "创建时间", "路线索引", "_index", "总货值"]:
            assert key not in result
        assert result["品名"] == "电子产品"

    def test_renames_unit_suffixed_keys_to_orm_attr_names(self):
        goods = {"重量(/kg)": 10.5, "总重量(/kg)": 100.0}
        result = clean_goods_detail(goods)
        assert result["重量"] == 10.5
        assert result["总重量"] == 100.0
        assert "重量(/kg)" not in result
        assert "总重量(/kg)" not in result

    def test_leaves_unrelated_keys_untouched_when_suffixed_keys_absent(self):
        goods = {"品名": "家具"}
        result = clean_goods_detail(goods)
        assert result == {"品名": "家具"}


# ── clean_goods_total ─────────────────────────────────────────────────────────

class TestCleanGoodsTotal:
    def test_strips_frontend_and_db_generated_keys(self):
        goods = {"整单货物ID": 1, "路线ID": 2, "创建时间": "x", "路线索引": 0,
                 "_index": 0, "品名": "机械设备"}
        result = clean_goods_total(goods)
        for key in ["整单货物ID", "路线ID", "创建时间", "路线索引", "_index"]:
            assert key not in result
        assert result["品名"] == "机械设备"

    def test_renames_unit_suffixed_keys_to_orm_attr_names(self):
        goods = {"实际重量(/kg)": 50.0, "总体积(/cbm)": 3.2}
        result = clean_goods_total(goods)
        assert result["实际重量"] == 50.0
        assert result["总体积"] == 3.2
        assert "实际重量(/kg)" not in result
        assert "总体积(/cbm)" not in result
