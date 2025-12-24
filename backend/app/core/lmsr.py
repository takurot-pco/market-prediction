"""
LMSR (Logarithmic Market Scoring Rule) Algorithm Implementation.
SPEC Section 3.3 compliant.

This module provides the core trading engine for the prediction market,
implementing the LMSR automated market maker algorithm.

Key formulas:
- Cost function: C(q) = b * ln(Σ e^(q_i/b))
- Price (probability): p_i = e^(q_i/b) / Σ e^(q_j/b)
- Trade cost: cost = C(q_new) - C(q_old)
"""
from __future__ import annotations

import math
from collections.abc import Sequence
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

# Price boundaries (SPEC Section 3.3)
# Prevent extreme prices that would make trading impractical
MIN_PRICE = Decimal("0.001")  # 0.1%
MAX_PRICE = Decimal("0.999")  # 99.9%

# Precision for Decimal calculations
PRECISION = Decimal("0.0001")


def _validate_inputs(quantities: Sequence[Decimal], b: Decimal) -> None:
    """Validate LMSR function inputs.

    Args:
        quantities: List of outcome quantities
        b: Liquidity parameter

    Raises:
        ValueError: If inputs are invalid
    """
    if len(quantities) < 2:
        raise ValueError("Market must have at least 2 outcomes")

    if b <= Decimal("0"):
        raise ValueError("Liquidity parameter b must be positive")


def _exp_scaled(q: Decimal, b: Decimal) -> Decimal:
    """Calculate e^(q/b) with overflow protection.

    Uses a scaling technique to prevent overflow for large q/b values.

    Args:
        q: Quantity value
        b: Liquidity parameter

    Returns:
        e^(q/b) as Decimal, or a bounded value if overflow would occur
    """
    try:
        exponent = float(q / b)
        # Clamp exponent to prevent overflow
        # math.exp overflows around 709
        if exponent > 700:
            exponent = 700
        elif exponent < -700:
            return Decimal("0")
        return Decimal(str(math.exp(exponent)))
    except (OverflowError, InvalidOperation):
        # Return max representable value for extreme cases
        return Decimal("1e308") if q > 0 else Decimal("0")


def cost_function(quantities: Sequence[Decimal], b: Decimal) -> Decimal:
    """Calculate the LMSR cost function.

    Formula: C(q) = b * ln(Σ e^(q_i/b))

    Args:
        quantities: List of outcome quantities (q_i for each outcome)
        b: Liquidity parameter (larger b = more liquidity, smaller price impact)

    Returns:
        The cost function value as Decimal

    Raises:
        ValueError: If inputs are invalid

    Example:
        >>> quantities = [Decimal("0"), Decimal("0")]
        >>> b = Decimal("100")
        >>> cost = cost_function(quantities, b)  # ~69.31 (100 * ln(2))
    """
    _validate_inputs(quantities, b)

    # Calculate sum of e^(q_i/b) for all outcomes
    # Use numerical stability technique: factor out max exponent
    max_q = max(quantities)
    scaled_sum = sum(
        _exp_scaled(q - max_q, b)
        for q in quantities
    )

    # C(q) = b * ln(Σ e^(q_i/b))
    # = b * (max_q/b + ln(Σ e^((q_i - max_q)/b)))
    # = max_q + b * ln(scaled_sum)
    log_sum = Decimal(str(math.log(float(scaled_sum))))
    cost = max_q + b * log_sum

    return cost.quantize(PRECISION, rounding=ROUND_HALF_UP)


def calculate_prices(
    quantities: Sequence[Decimal],
    b: Decimal,
    apply_bounds: bool = True,
) -> list[Decimal]:
    """Calculate prices (probabilities) for each outcome.

    Formula: p_i = e^(q_i/b) / Σ e^(q_j/b)

    Args:
        quantities: List of outcome quantities
        b: Liquidity parameter
        apply_bounds: Whether to apply MIN_PRICE/MAX_PRICE bounds

    Returns:
        List of prices (probabilities) for each outcome, summing to 1.0

    Raises:
        ValueError: If inputs are invalid

    Example:
        >>> quantities = [Decimal("0"), Decimal("0")]
        >>> b = Decimal("100")
        >>> prices = calculate_prices(quantities, b)  # [0.5, 0.5]
    """
    _validate_inputs(quantities, b)

    # Use log-sum-exp trick for numerical stability
    max_q = max(quantities)
    exp_values = [_exp_scaled(q - max_q, b) for q in quantities]
    total = sum(exp_values)

    # Calculate raw probabilities
    raw_prices = [exp_val / total for exp_val in exp_values]

    if not apply_bounds:
        return [p.quantize(PRECISION, rounding=ROUND_HALF_UP) for p in raw_prices]

    # Apply price bounds and renormalize
    bounded_prices = []
    for price in raw_prices:
        if price < MIN_PRICE:
            bounded_prices.append(MIN_PRICE)
        elif price > MAX_PRICE:
            bounded_prices.append(MAX_PRICE)
        else:
            bounded_prices.append(price)

    # Renormalize to ensure sum = 1.0 after bounding
    bounded_total = sum(bounded_prices)
    normalized_prices = [p / bounded_total for p in bounded_prices]

    return [p.quantize(PRECISION, rounding=ROUND_HALF_UP) for p in normalized_prices]


def calculate_trade_cost(
    quantities: Sequence[Decimal],
    outcome_index: int,
    quantity_delta: Decimal,
    b: Decimal,
) -> Decimal:
    """Calculate the cost of a trade.

    Formula: cost = C(q_new) - C(q_old)

    Args:
        quantities: Current quantities for all outcomes
        outcome_index: Index of the outcome being traded
        quantity_delta: Change in quantity (positive for buy, negative for sell)
        b: Liquidity parameter

    Returns:
        The cost of the trade (positive = user pays, negative = user receives)

    Raises:
        ValueError: If inputs are invalid or outcome_index is out of range

    Example:
        >>> quantities = [Decimal("0"), Decimal("0")]
        >>> cost = calculate_trade_cost(quantities, 0, Decimal("10"), Decimal("100"))
    """
    _validate_inputs(quantities, b)

    if outcome_index < 0 or outcome_index >= len(quantities):
        raise ValueError(f"outcome_index {outcome_index} out of range")

    if quantity_delta == Decimal("0"):
        return Decimal("0")

    # Calculate cost before trade
    cost_before = cost_function(quantities, b)

    # Calculate new quantities after trade
    new_quantities = list(quantities)
    new_quantities[outcome_index] = quantities[outcome_index] + quantity_delta

    # Calculate cost after trade
    cost_after = cost_function(new_quantities, b)

    # Trade cost = new cost - old cost
    trade_cost = cost_after - cost_before

    return trade_cost.quantize(PRECISION, rounding=ROUND_HALF_UP)


def is_trade_allowed(
    quantities: Sequence[Decimal],
    outcome_index: int,
    quantity_delta: Decimal,
    b: Decimal,
) -> tuple[bool, str | None]:
    """Check if a trade is allowed based on price boundaries.

    A trade is rejected if it would push any price outside the
    MIN_PRICE to MAX_PRICE range.

    Args:
        quantities: Current quantities for all outcomes
        outcome_index: Index of the outcome being traded
        quantity_delta: Proposed change in quantity
        b: Liquidity parameter

    Returns:
        Tuple of (is_allowed, rejection_reason)
        - is_allowed: True if trade is allowed
        - rejection_reason: None if allowed, or error message if rejected

    Example:
        >>> quantities = [Decimal("500"), Decimal("0")]
        >>> allowed, reason = is_trade_allowed(quantities, 0, Decimal("1000"), Decimal("100"))
    """
    try:
        _validate_inputs(quantities, b)
    except ValueError as e:
        return False, str(e)

    if outcome_index < 0 or outcome_index >= len(quantities):
        return False, f"outcome_index {outcome_index} out of range"

    # Calculate new quantities after trade
    new_quantities = list(quantities)
    new_quantities[outcome_index] = quantities[outcome_index] + quantity_delta

    # Check if any new quantity would be negative (can't have negative shares overall)
    # Note: Individual positions can be negative (shorts), but market state can't be
    # This check may need adjustment based on business rules

    # Calculate prices after trade without bounds
    try:
        new_prices = calculate_prices(new_quantities, b, apply_bounds=False)
    except (ValueError, OverflowError) as e:
        return False, f"Price calculation error: {e}"

    # Check if any price would exceed boundaries
    for i, price in enumerate(new_prices):
        if price < MIN_PRICE:
            return False, f"Trade would push outcome {i} price below minimum ({MIN_PRICE})"
        if price > MAX_PRICE:
            return False, f"Trade would push outcome {i} price above maximum ({MAX_PRICE})"

    return True, None


def estimate_shares_for_cost(
    quantities: Sequence[Decimal],
    outcome_index: int,
    target_cost: Decimal,
    b: Decimal,
    max_iterations: int = 50,
) -> Decimal:
    """Estimate how many shares can be bought for a given cost.

    Uses binary search to find the quantity that results in approximately
    the target cost.

    Args:
        quantities: Current quantities for all outcomes
        outcome_index: Index of the outcome to buy
        target_cost: Maximum cost willing to pay
        b: Liquidity parameter
        max_iterations: Maximum iterations for binary search

    Returns:
        Estimated number of shares that can be bought

    Raises:
        ValueError: If inputs are invalid
    """
    _validate_inputs(quantities, b)

    if target_cost <= Decimal("0"):
        return Decimal("0")

    # Binary search for quantity
    low = Decimal("0")
    high = target_cost * Decimal("10")  # Upper bound estimate

    for _ in range(max_iterations):
        mid = (low + high) / Decimal("2")
        cost = calculate_trade_cost(quantities, outcome_index, mid, b)

        if abs(cost - target_cost) < PRECISION:
            return mid.quantize(PRECISION, rounding=ROUND_HALF_UP)

        if cost < target_cost:
            low = mid
        else:
            high = mid

    return low.quantize(PRECISION, rounding=ROUND_HALF_UP)
