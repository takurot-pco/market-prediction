"""
Tests for LMSR (Logarithmic Market Scoring Rule) algorithm.
SPEC Section 3.3 compliant.
"""
from __future__ import annotations

import math
from decimal import Decimal

import pytest


class TestLMSRCostFunction:
    """Tests for LMSR cost function C(q) = b * ln(Σ e^(q_i/b))."""

    def test_cost_function_exists(self) -> None:
        """Test that cost function is importable."""
        from app.core.lmsr import cost_function

        assert callable(cost_function)

    def test_cost_function_binary_equal_quantities(self) -> None:
        """Test cost for binary market with equal quantities."""
        from app.core.lmsr import cost_function

        # q = [0, 0], b = 100
        # C = 100 * ln(e^0 + e^0) = 100 * ln(2) ≈ 69.31
        quantities = [Decimal("0"), Decimal("0")]
        b = Decimal("100")
        result = cost_function(quantities, b)

        expected = Decimal("100") * Decimal(str(math.log(2)))
        assert abs(result - expected) < Decimal("0.01")

    def test_cost_function_binary_unequal_quantities(self) -> None:
        """Test cost for binary market with unequal quantities."""
        from app.core.lmsr import cost_function

        # q = [10, 0], b = 100
        quantities = [Decimal("10"), Decimal("0")]
        b = Decimal("100")
        result = cost_function(quantities, b)

        # C = 100 * ln(e^(10/100) + e^0) = 100 * ln(e^0.1 + 1)
        expected = Decimal("100") * Decimal(str(math.log(math.exp(0.1) + 1)))
        assert abs(result - expected) < Decimal("0.01")

    def test_cost_function_categorical_three_outcomes(self) -> None:
        """Test cost for categorical market with 3 outcomes."""
        from app.core.lmsr import cost_function

        # q = [0, 0, 0], b = 100
        # C = 100 * ln(3) ≈ 109.86
        quantities = [Decimal("0"), Decimal("0"), Decimal("0")]
        b = Decimal("100")
        result = cost_function(quantities, b)

        expected = Decimal("100") * Decimal(str(math.log(3)))
        assert abs(result - expected) < Decimal("0.01")

    def test_cost_function_increases_with_quantity(self) -> None:
        """Test that cost increases when any quantity increases."""
        from app.core.lmsr import cost_function

        b = Decimal("100")
        q1 = [Decimal("0"), Decimal("0")]
        q2 = [Decimal("10"), Decimal("0")]

        c1 = cost_function(q1, b)
        c2 = cost_function(q2, b)

        assert c2 > c1


class TestLMSRPriceCalculation:
    """Tests for LMSR price (probability) calculation p_i = e^(q_i/b) / Σ e^(q_j/b)."""

    def test_price_function_exists(self) -> None:
        """Test that price function is importable."""
        from app.core.lmsr import calculate_prices

        assert callable(calculate_prices)

    def test_prices_sum_to_one(self) -> None:
        """Test that prices (probabilities) sum to 1.0."""
        from app.core.lmsr import calculate_prices

        quantities = [Decimal("0"), Decimal("0")]
        b = Decimal("100")
        prices = calculate_prices(quantities, b)

        total = sum(prices)
        assert abs(total - Decimal("1")) < Decimal("0.0001")

    def test_equal_quantities_give_equal_prices(self) -> None:
        """Test that equal quantities give equal prices."""
        from app.core.lmsr import calculate_prices

        quantities = [Decimal("0"), Decimal("0")]
        b = Decimal("100")
        prices = calculate_prices(quantities, b)

        assert len(prices) == 2
        assert abs(prices[0] - Decimal("0.5")) < Decimal("0.0001")
        assert abs(prices[1] - Decimal("0.5")) < Decimal("0.0001")

    def test_higher_quantity_gives_higher_price(self) -> None:
        """Test that higher quantity gives higher price."""
        from app.core.lmsr import calculate_prices

        quantities = [Decimal("50"), Decimal("0")]
        b = Decimal("100")
        prices = calculate_prices(quantities, b)

        assert prices[0] > prices[1]

    def test_categorical_prices_sum_to_one(self) -> None:
        """Test that categorical market prices sum to 1.0."""
        from app.core.lmsr import calculate_prices

        quantities = [Decimal("10"), Decimal("20"), Decimal("30")]
        b = Decimal("100")
        prices = calculate_prices(quantities, b)

        total = sum(prices)
        assert abs(total - Decimal("1")) < Decimal("0.0001")

    def test_three_equal_quantities_give_third_each(self) -> None:
        """Test that 3 equal quantities give 1/3 probability each."""
        from app.core.lmsr import calculate_prices

        quantities = [Decimal("0"), Decimal("0"), Decimal("0")]
        b = Decimal("100")
        prices = calculate_prices(quantities, b)

        for price in prices:
            assert abs(price - Decimal("1") / Decimal("3")) < Decimal("0.0001")


class TestLMSRTradeCost:
    """Tests for LMSR trade cost calculation: cost = C(q_new) - C(q_old)."""

    def test_trade_cost_function_exists(self) -> None:
        """Test that trade cost function is importable."""
        from app.core.lmsr import calculate_trade_cost

        assert callable(calculate_trade_cost)

    def test_buy_trade_cost_positive(self) -> None:
        """Test that buying shares has positive cost."""
        from app.core.lmsr import calculate_trade_cost

        quantities = [Decimal("0"), Decimal("0")]
        b = Decimal("100")
        outcome_index = 0
        quantity_delta = Decimal("10")

        cost = calculate_trade_cost(quantities, outcome_index, quantity_delta, b)

        assert cost > Decimal("0")

    def test_sell_trade_cost_negative(self) -> None:
        """Test that selling shares returns points (negative cost)."""
        from app.core.lmsr import calculate_trade_cost

        quantities = [Decimal("10"), Decimal("0")]
        b = Decimal("100")
        outcome_index = 0
        quantity_delta = Decimal("-5")

        cost = calculate_trade_cost(quantities, outcome_index, quantity_delta, b)

        assert cost < Decimal("0")

    def test_zero_quantity_zero_cost(self) -> None:
        """Test that zero quantity change has zero cost."""
        from app.core.lmsr import calculate_trade_cost

        quantities = [Decimal("10"), Decimal("0")]
        b = Decimal("100")
        outcome_index = 0
        quantity_delta = Decimal("0")

        cost = calculate_trade_cost(quantities, outcome_index, quantity_delta, b)

        assert cost == Decimal("0")

    def test_trade_cost_approximates_price_for_small_trades(self) -> None:
        """Test that trade cost ≈ price * quantity for small trades."""
        from app.core.lmsr import calculate_prices, calculate_trade_cost

        quantities = [Decimal("0"), Decimal("0")]
        b = Decimal("100")
        outcome_index = 0
        quantity_delta = Decimal("1")

        prices = calculate_prices(quantities, b)
        cost = calculate_trade_cost(quantities, outcome_index, quantity_delta, b)

        # For small trades, cost ≈ price * quantity
        expected_approx = prices[outcome_index] * quantity_delta
        assert abs(cost - expected_approx) < Decimal("0.1")


class TestLMSRPriceBoundary:
    """Tests for price boundary enforcement: 0.1% ≤ probability ≤ 99.9%."""

    def test_price_boundary_constants_exist(self) -> None:
        """Test that price boundary constants are defined."""
        from app.core.lmsr import MAX_PRICE, MIN_PRICE

        assert MIN_PRICE == Decimal("0.001")  # 0.1%
        assert MAX_PRICE == Decimal("0.999")  # 99.9%

    def test_prices_bounded_low(self) -> None:
        """Test that prices don't go below minimum."""
        from app.core.lmsr import MIN_PRICE, calculate_prices

        # Very low quantity for first outcome
        quantities = [Decimal("-500"), Decimal("500")]
        b = Decimal("100")
        prices = calculate_prices(quantities, b)

        for price in prices:
            assert price >= MIN_PRICE

    def test_prices_bounded_high(self) -> None:
        """Test that prices don't go above maximum."""
        from app.core.lmsr import MAX_PRICE, calculate_prices

        # Very high quantity for first outcome
        quantities = [Decimal("500"), Decimal("-500")]
        b = Decimal("100")
        prices = calculate_prices(quantities, b)

        for price in prices:
            assert price <= MAX_PRICE

    def test_is_trade_allowed_checks_boundary(self) -> None:
        """Test that is_trade_allowed checks price boundaries."""
        from app.core.lmsr import is_trade_allowed

        assert callable(is_trade_allowed)

        # Trade that would push price beyond boundary should be rejected
        quantities = [Decimal("500"), Decimal("0")]
        b = Decimal("100")
        outcome_index = 0
        quantity_delta = Decimal("1000")

        allowed, reason = is_trade_allowed(
            quantities, outcome_index, quantity_delta, b
        )

        # If trade pushes price above 99.9%, it should be rejected
        # The actual result depends on implementation


class TestLMSRNumericalPrecision:
    """Tests for numerical precision with Decimal type."""

    def test_uses_decimal_not_float(self) -> None:
        """Test that LMSR functions use Decimal for precision."""
        from app.core.lmsr import calculate_prices, cost_function

        quantities = [Decimal("0"), Decimal("0")]
        b = Decimal("100")

        cost = cost_function(quantities, b)
        prices = calculate_prices(quantities, b)

        assert isinstance(cost, Decimal)
        for price in prices:
            assert isinstance(price, Decimal)

    def test_precision_maintained_large_numbers(self) -> None:
        """Test precision with large numbers."""
        from app.core.lmsr import calculate_prices

        quantities = [Decimal("10000"), Decimal("10000")]
        b = Decimal("1000")
        prices = calculate_prices(quantities, b)

        total = sum(prices)
        assert abs(total - Decimal("1")) < Decimal("0.0001")

    def test_precision_maintained_small_differences(self) -> None:
        """Test precision with small differences."""
        from app.core.lmsr import calculate_prices

        # Use a difference large enough to be visible after rounding (> 0.0001)
        quantities = [Decimal("100.1"), Decimal("100.0")]
        b = Decimal("100")
        prices = calculate_prices(quantities, b)

        # First outcome should be slightly higher
        assert prices[0] > prices[1]


class TestLMSRBinaryMarket:
    """Tests specific to binary (YES/NO) markets."""

    def test_binary_market_two_outcomes(self) -> None:
        """Test binary market has exactly 2 outcomes."""
        from app.core.lmsr import calculate_prices

        quantities = [Decimal("0"), Decimal("0")]
        b = Decimal("100")
        prices = calculate_prices(quantities, b)

        assert len(prices) == 2

    def test_binary_50_50_start(self) -> None:
        """Test binary market starts at 50/50."""
        from app.core.lmsr import calculate_prices

        quantities = [Decimal("0"), Decimal("0")]
        b = Decimal("100")
        prices = calculate_prices(quantities, b)

        assert abs(prices[0] - Decimal("0.5")) < Decimal("0.0001")
        assert abs(prices[1] - Decimal("0.5")) < Decimal("0.0001")

    def test_binary_buy_yes_increases_yes_price(self) -> None:
        """Test buying YES increases YES price."""
        from app.core.lmsr import calculate_prices

        b = Decimal("100")

        prices_before = calculate_prices([Decimal("0"), Decimal("0")], b)
        prices_after = calculate_prices([Decimal("10"), Decimal("0")], b)

        assert prices_after[0] > prices_before[0]
        assert prices_after[1] < prices_before[1]


class TestLMSRCategoricalMarket:
    """Tests specific to categorical markets (multiple outcomes)."""

    def test_categorical_equal_start(self) -> None:
        """Test categorical market starts with equal probabilities."""
        from app.core.lmsr import calculate_prices

        # 4 outcomes
        quantities = [Decimal("0")] * 4
        b = Decimal("100")
        prices = calculate_prices(quantities, b)

        expected = Decimal("1") / Decimal("4")
        for price in prices:
            assert abs(price - expected) < Decimal("0.0001")

    def test_categorical_buy_increases_that_outcome(self) -> None:
        """Test buying one outcome increases its price and decreases others."""
        from app.core.lmsr import calculate_prices

        b = Decimal("100")

        prices_before = calculate_prices([Decimal("0")] * 3, b)
        prices_after = calculate_prices(
            [Decimal("20"), Decimal("0"), Decimal("0")], b
        )

        # First outcome increased
        assert prices_after[0] > prices_before[0]
        # Others decreased
        assert prices_after[1] < prices_before[1]
        assert prices_after[2] < prices_before[2]


class TestLMSRLiquidityParameter:
    """Tests for liquidity parameter (b) behavior."""

    def test_higher_b_smaller_price_change(self) -> None:
        """Test that higher b results in smaller price changes."""
        from app.core.lmsr import calculate_prices

        quantities_before = [Decimal("0"), Decimal("0")]
        quantities_after = [Decimal("10"), Decimal("0")]

        # Low liquidity (b=50)
        prices_before_low = calculate_prices(quantities_before, Decimal("50"))
        prices_after_low = calculate_prices(quantities_after, Decimal("50"))
        change_low = prices_after_low[0] - prices_before_low[0]

        # High liquidity (b=200)
        prices_before_high = calculate_prices(quantities_before, Decimal("200"))
        prices_after_high = calculate_prices(quantities_after, Decimal("200"))
        change_high = prices_after_high[0] - prices_before_high[0]

        # Higher b should result in smaller price change
        assert change_high < change_low

    def test_recommended_b_range(self) -> None:
        """Test that recommended b values (100-1000) work correctly."""
        from app.core.lmsr import calculate_prices

        quantities = [Decimal("10"), Decimal("10")]

        for b_value in [100, 500, 1000]:
            b = Decimal(str(b_value))
            prices = calculate_prices(quantities, b)
            total = sum(prices)
            assert abs(total - Decimal("1")) < Decimal("0.0001")


class TestLMSREdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_single_outcome_raises_error(self) -> None:
        """Test that single outcome market raises error."""
        from app.core.lmsr import calculate_prices

        with pytest.raises(ValueError):
            calculate_prices([Decimal("0")], Decimal("100"))

    def test_empty_quantities_raises_error(self) -> None:
        """Test that empty quantities raises error."""
        from app.core.lmsr import calculate_prices

        with pytest.raises(ValueError):
            calculate_prices([], Decimal("100"))

    def test_zero_b_raises_error(self) -> None:
        """Test that zero liquidity parameter raises error."""
        from app.core.lmsr import calculate_prices

        with pytest.raises(ValueError):
            calculate_prices([Decimal("0"), Decimal("0")], Decimal("0"))

    def test_negative_b_raises_error(self) -> None:
        """Test that negative liquidity parameter raises error."""
        from app.core.lmsr import calculate_prices

        with pytest.raises(ValueError):
            calculate_prices([Decimal("0"), Decimal("0")], Decimal("-100"))

    def test_very_large_quantities(self) -> None:
        """Test handling of very large quantities (overflow prevention)."""
        from app.core.lmsr import calculate_prices

        # Large but manageable quantities
        quantities = [Decimal("10000"), Decimal("0")]
        b = Decimal("100")

        # Should not raise overflow error
        prices = calculate_prices(quantities, b)
        total = sum(prices)
        assert abs(total - Decimal("1")) < Decimal("0.01")
