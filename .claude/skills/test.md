# Test Generator

## Overview
pytest-asyncio を使用したバックエンドテストコードの作成を支援します。

## プロジェクト構成

```
backend/tests/
├── __init__.py
├── conftest.py          # 共通フィクスチャ
├── test_main.py         # API基本テスト
├── test_lmsr.py         # LMSRロジックテスト
├── test_migrations.py   # マイグレーションテスト
├── test_auth.py         # 認証テスト
├── test_markets.py      # マーケットAPIテスト
├── test_trading.py      # 取引APIテスト
└── factories/           # テストデータファクトリ
    ├── __init__.py
    └── user.py
```

## 基本コマンド

```bash
cd backend

# 全テスト実行
poetry run pytest

# カバレッジ付き
poetry run pytest --cov=app --cov-report=html

# 特定ファイル
poetry run pytest tests/test_lmsr.py

# 特定テスト
poetry run pytest tests/test_lmsr.py::test_binary_market_probability

# 詳細出力
poetry run pytest -v

# 失敗時に停止
poetry run pytest -x

# 並列実行
poetry run pytest -n auto
```

## conftest.py (共通フィクスチャ)

```python
# backend/tests/conftest.py
import asyncio
from typing import AsyncGenerator, Generator
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.models.user import User, UserRole


# テスト用インメモリDB
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """イベントループをセッション単位で共有"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """テスト用DBセッション"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """テスト用HTTPクライアント"""
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """テスト用ユーザー"""
    user = User(
        id=uuid4(),
        email="test@example.com",
        name="Test User",
        role=UserRole.USER,
        department="Engineering",
        balance=Decimal("1000.00"),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """テスト用管理者"""
    user = User(
        id=uuid4(),
        email="admin@example.com",
        name="Admin User",
        role=UserRole.ADMIN,
        balance=Decimal("10000.00"),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """認証ヘッダー（JWTトークン付き）"""
    from app.core.security import create_access_token
    token = create_access_token(subject=str(test_user.id))
    return {"Authorization": f"Bearer {token}"}
```

## テストパターン

### APIエンドポイントテスト
```python
# backend/tests/test_markets.py
import pytest
from httpx import AsyncClient
from uuid import uuid4

from app.models.market import MarketStatus


@pytest.mark.asyncio
async def test_list_markets_empty(client: AsyncClient, auth_headers: dict):
    """マーケット一覧（空）"""
    response = await client.get("/api/v1/markets", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_list_markets_with_filter(client: AsyncClient, auth_headers: dict, test_market):
    """マーケット一覧（フィルタあり）"""
    response = await client.get(
        "/api/v1/markets",
        params={"status": "open"},
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["status"] == "open"


@pytest.mark.asyncio
async def test_create_market_success(client: AsyncClient, moderator_headers: dict):
    """マーケット作成成功"""
    payload = {
        "title": "Test Market",
        "description": "Test description",
        "category_id": str(uuid4()),
        "market_type": "binary",
        "start_at": "2024-12-01T00:00:00Z",
        "end_at": "2024-12-31T23:59:59Z",
        "resolution_date": "2025-01-01",
    }
    
    response = await client.post(
        "/api/v1/markets",
        json=payload,
        headers=moderator_headers,
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Market"
    assert data["status"] == "draft"


@pytest.mark.asyncio
async def test_create_market_forbidden(client: AsyncClient, auth_headers: dict):
    """マーケット作成（権限不足）"""
    payload = {"title": "Test Market"}
    
    response = await client.post(
        "/api/v1/markets",
        json=payload,
        headers=auth_headers,
    )
    
    assert response.status_code == 403
    assert response.json()["error_code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_get_market_not_found(client: AsyncClient, auth_headers: dict):
    """マーケット取得（存在しない）"""
    response = await client.get(
        f"/api/v1/markets/{uuid4()}",
        headers=auth_headers,
    )
    
    assert response.status_code == 404
    assert response.json()["error_code"] == "NOT_FOUND"
```

### LMSRロジックテスト
```python
# backend/tests/test_lmsr.py
import pytest
from decimal import Decimal
import math

from app.core.lmsr import LMSR


class TestLMSRCostFunction:
    """コスト関数のテスト"""
    
    def test_cost_equal_quantities(self):
        """同量の場合のコスト"""
        lmsr = LMSR(b=Decimal("100"))
        quantities = [Decimal("0"), Decimal("0")]
        
        cost = lmsr.cost(quantities)
        # C(0,0) = 100 * ln(e^0 + e^0) = 100 * ln(2)
        expected = Decimal("100") * Decimal(str(math.log(2)))
        
        assert abs(cost - expected) < Decimal("0.01")
    
    def test_cost_increases_with_quantity(self):
        """数量増加でコスト増加"""
        lmsr = LMSR(b=Decimal("100"))
        
        cost1 = lmsr.cost([Decimal("0"), Decimal("0")])
        cost2 = lmsr.cost([Decimal("10"), Decimal("0")])
        cost3 = lmsr.cost([Decimal("20"), Decimal("0")])
        
        assert cost2 > cost1
        assert cost3 > cost2


class TestLMSRProbability:
    """確率計算のテスト"""
    
    def test_probability_equal_quantities(self):
        """同量の場合は50-50"""
        lmsr = LMSR(b=Decimal("100"))
        quantities = [Decimal("0"), Decimal("0")]
        
        p0 = lmsr.probability(quantities, 0)
        p1 = lmsr.probability(quantities, 1)
        
        assert abs(p0 - Decimal("0.5")) < Decimal("0.001")
        assert abs(p1 - Decimal("0.5")) < Decimal("0.001")
    
    def test_probability_sum_to_one(self):
        """確率の合計は1"""
        lmsr = LMSR(b=Decimal("100"))
        quantities = [Decimal("50"), Decimal("30"), Decimal("20")]
        
        total = sum(lmsr.probability(quantities, i) for i in range(3))
        
        assert abs(total - Decimal("1")) < Decimal("0.001")
    
    def test_probability_boundaries(self):
        """確率の境界チェック"""
        lmsr = LMSR(b=Decimal("100"))
        # 極端に偏った数量
        quantities = [Decimal("1000"), Decimal("0")]
        
        p0 = lmsr.probability(quantities, 0)
        p1 = lmsr.probability(quantities, 1)
        
        assert p0 <= Decimal("0.999")
        assert p1 >= Decimal("0.001")


class TestLMSRTradeCost:
    """取引コストのテスト"""
    
    def test_buy_cost_positive(self):
        """購入コストは正"""
        lmsr = LMSR(b=Decimal("100"))
        quantities = [Decimal("0"), Decimal("0")]
        
        cost = lmsr.trade_cost(quantities, 0, Decimal("10"))
        
        assert cost > Decimal("0")
    
    def test_sell_cost_negative(self):
        """売却コストは負（返金）"""
        lmsr = LMSR(b=Decimal("100"))
        quantities = [Decimal("10"), Decimal("0")]
        
        cost = lmsr.trade_cost(quantities, 0, Decimal("-5"))
        
        assert cost < Decimal("0")
    
    def test_cost_symmetry(self):
        """買って売ると元に戻る（手数料なしの場合）"""
        lmsr = LMSR(b=Decimal("100"))
        quantities = [Decimal("0"), Decimal("0")]
        
        buy_cost = lmsr.trade_cost(quantities, 0, Decimal("10"))
        new_quantities = [Decimal("10"), Decimal("0")]
        sell_cost = lmsr.trade_cost(new_quantities, 0, Decimal("-10"))
        
        # 買い + 売り ≈ 0
        assert abs(buy_cost + sell_cost) < Decimal("0.01")
```

### 取引処理テスト
```python
# backend/tests/test_trading.py
import pytest
from decimal import Decimal
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_trade_buy_success(
    client: AsyncClient,
    auth_headers: dict,
    test_market,
    test_user,
):
    """購入成功"""
    response = await client.post(
        f"/api/v1/markets/{test_market.id}/trade",
        json={
            "outcome_id": str(test_market.outcomes[0].id),
            "action": "buy",
            "quantity": 10,
        },
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["quantity"] == 10
    assert data["cost"] > 0


@pytest.mark.asyncio
async def test_trade_insufficient_balance(
    client: AsyncClient,
    auth_headers: dict,
    test_market,
    test_user,
    db_session,
):
    """残高不足"""
    # 残高を減らす
    test_user.balance = Decimal("1.00")
    await db_session.commit()
    
    response = await client.post(
        f"/api/v1/markets/{test_market.id}/trade",
        json={
            "outcome_id": str(test_market.outcomes[0].id),
            "action": "buy",
            "quantity": 1000,
        },
        headers=auth_headers,
    )
    
    assert response.status_code == 400
    assert response.json()["error_code"] == "INSUFFICIENT_BALANCE"


@pytest.mark.asyncio
async def test_trade_market_not_open(
    client: AsyncClient,
    auth_headers: dict,
    closed_market,
):
    """マーケットがOPENでない"""
    response = await client.post(
        f"/api/v1/markets/{closed_market.id}/trade",
        json={
            "outcome_id": str(closed_market.outcomes[0].id),
            "action": "buy",
            "quantity": 10,
        },
        headers=auth_headers,
    )
    
    assert response.status_code == 400
    assert response.json()["error_code"] == "MARKET_NOT_OPEN"
```

### パラメータ化テスト
```python
@pytest.mark.parametrize("quantity,expected_cost_range", [
    (1, (0.4, 0.6)),
    (10, (4, 6)),
    (100, (40, 60)),
])
def test_trade_cost_scales(lmsr, quantity, expected_cost_range):
    """取引量に応じたコストスケール"""
    quantities = [Decimal("0"), Decimal("0")]
    cost = lmsr.trade_cost(quantities, 0, Decimal(str(quantity)))
    
    assert expected_cost_range[0] < float(cost) < expected_cost_range[1]
```

## テストカバレッジ

```bash
# HTMLレポート生成
poetry run pytest --cov=app --cov-report=html

# 最低カバレッジを設定
poetry run pytest --cov=app --cov-fail-under=80
```

## 関連ドキュメント
- PLAN.md: 開発プロセスとCI/CD戦略（テスト戦略）
- SPEC.md Section 8: エラーコード一覧
