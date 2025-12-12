# LMSR Calculation Helper

## Overview
予測市場の核となる LMSR (Logarithmic Market Scoring Rule) アルゴリズムの実装支援を行います。

## LMSR 数式

### コスト関数
```
C(q) = b * ln(Σ e^(q_i/b))
```
- `q_i`: 各アウトカムの現在数量
- `b`: 流動性パラメータ（推奨値: 100〜1000）

### 確率（価格）計算
```
p_i = e^(q_i/b) / Σ e^(q_j/b)
```

### 取引コスト計算
```
cost = C(q_new) - C(q_old)
```

## 実装ガイドライン

### 精度管理
- **Decimal型を使用**: 浮動小数点誤差を避けるため `decimal.Decimal` を使用
- **精度設定**: `DECIMAL(12,2)` for quantities, `DECIMAL(5,4)` for probabilities

### エッジケース処理
- **価格境界**: 0.1% ≤ probability ≤ 99.9% を強制
- **オーバーフロー防止**: 大きな指数計算時は log-sum-exp trick を使用
- **ゼロ除算防止**: 分母がゼロにならないよう検証

### Python 実装例
```python
from decimal import Decimal
import math

class LMSR:
    def __init__(self, b: Decimal):
        self.b = b
        self.MIN_PROB = Decimal("0.001")  # 0.1%
        self.MAX_PROB = Decimal("0.999")  # 99.9%
    
    def cost(self, quantities: list[Decimal]) -> Decimal:
        """コスト関数 C(q) = b * ln(Σ e^(q_i/b))"""
        b_float = float(self.b)
        exp_sum = sum(math.exp(float(q) / b_float) for q in quantities)
        return self.b * Decimal(str(math.log(exp_sum)))
    
    def probability(self, quantities: list[Decimal], index: int) -> Decimal:
        """確率計算 p_i = e^(q_i/b) / Σ e^(q_j/b)"""
        b_float = float(self.b)
        exp_values = [math.exp(float(q) / b_float) for q in quantities]
        prob = Decimal(str(exp_values[index] / sum(exp_values)))
        return max(self.MIN_PROB, min(self.MAX_PROB, prob))
    
    def trade_cost(
        self, 
        quantities: list[Decimal], 
        outcome_index: int, 
        delta: Decimal
    ) -> Decimal:
        """取引コスト = C(q_new) - C(q_old)"""
        old_cost = self.cost(quantities)
        new_quantities = quantities.copy()
        new_quantities[outcome_index] += delta
        new_cost = self.cost(new_quantities)
        return new_cost - old_cost
```

### テストケース
```python
import pytest
from decimal import Decimal

def test_lmsr_binary_market():
    """Binary market (YES/NO) のテスト"""
    lmsr = LMSR(b=Decimal("100"))
    quantities = [Decimal("0"), Decimal("0")]
    
    # 初期確率は50-50
    assert lmsr.probability(quantities, 0) == Decimal("0.5")
    assert lmsr.probability(quantities, 1) == Decimal("0.5")

def test_lmsr_price_boundaries():
    """価格境界のテスト"""
    lmsr = LMSR(b=Decimal("100"))
    # 極端に偏った数量でも境界内に収まる
    quantities = [Decimal("1000"), Decimal("0")]
    prob = lmsr.probability(quantities, 0)
    assert prob <= Decimal("0.999")
```

## ファイル配置
- 実装: `backend/app/core/lmsr.py`
- テスト: `backend/tests/test_lmsr.py`

## 関連ドキュメント
- SPEC.md Section 3.3: 取引エンジン仕様
- PLAN.md Task 3.2: LMSRロジック実装
