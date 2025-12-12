# SQLAlchemy Model Generator

## Overview
SPEC.md Section 4 に準拠した async SQLAlchemy モデルの実装支援を行います。

## プロジェクト規約

### ディレクトリ構成
```
backend/app/models/
├── __init__.py     # 全モデルをエクスポート
├── base.py         # Base クラス定義
├── user.py
├── category.py
├── market.py
├── outcome.py
├── position.py
├── transaction.py
└── price_history.py
```

### 共通設定
- **主キー**: UUID (uuid4で自動生成)
- **タイムスタンプ**: `created_at`, `updated_at` を全テーブルに
- **ENUM型**: PostgreSQL ENUM として定義
- **外部キー**: 明示的な `ForeignKey` と `relationship`

## Base クラス定義

```python
# backend/app/models/base.py
from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """全モデルの基底クラス"""
    pass


class TimestampMixin:
    """タイムスタンプ用Mixin"""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class UUIDMixin:
    """UUID主キー用Mixin"""
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
```

## モデル実装例

### User モデル
```python
# backend/app/models/user.py
from decimal import Decimal
from sqlalchemy import String, Numeric, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.models.base import Base, UUIDMixin, TimestampMixin


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MODERATOR = "moderator"
    USER = "user"


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"
    
    email: Mapped[str] = mapped_column(
        String(320), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole, name="user_role"),
        default=UserRole.USER,
        nullable=False,
    )
    department: Mapped[str | None] = mapped_column(String(100))
    balance: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("1000.00"), nullable=False
    )
    
    # Relationships
    positions: Mapped[list["Position"]] = relationship(
        back_populates="user", lazy="selectin"
    )
    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="user", lazy="selectin"
    )
```

### Market モデル
```python
# backend/app/models/market.py
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID
from sqlalchemy import String, Text, Numeric, Date, DateTime, ForeignKey
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.models.base import Base, UUIDMixin, TimestampMixin


class MarketType(str, enum.Enum):
    BINARY = "binary"
    CATEGORICAL = "categorical"
    SCALAR = "scalar"


class MarketStatus(str, enum.Enum):
    DRAFT = "draft"
    OPEN = "open"
    CLOSED = "closed"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"


class Visibility(str, enum.Enum):
    PUBLIC = "public"
    DEPARTMENT = "department"
    INVITED = "invited"


class Market(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "markets"
    
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    category_id: Mapped[UUID] = mapped_column(
        ForeignKey("categories.id"), nullable=False
    )
    market_type: Mapped[MarketType] = mapped_column(
        SQLEnum(MarketType, name="market_type"),
        default=MarketType.BINARY,
        nullable=False,
    )
    status: Mapped[MarketStatus] = mapped_column(
        SQLEnum(MarketStatus, name="market_status"),
        default=MarketStatus.DRAFT,
        nullable=False,
        index=True,
    )
    visibility: Mapped[Visibility] = mapped_column(
        SQLEnum(Visibility, name="visibility"),
        default=Visibility.PUBLIC,
        nullable=False,
    )
    liquidity_param: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("100.00"), nullable=False
    )
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolution_date: Mapped[date] = mapped_column(Date, nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolved_outcome_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("outcomes.id")
    )
    created_by: Mapped[UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    
    # Relationships
    category: Mapped["Category"] = relationship(back_populates="markets")
    outcomes: Mapped[list["Outcome"]] = relationship(
        back_populates="market", lazy="selectin"
    )
    creator: Mapped["User"] = relationship(foreign_keys=[created_by])
```

### Outcome モデル
```python
# backend/app/models/outcome.py
from decimal import Decimal
from uuid import UUID
from sqlalchemy import String, Numeric, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin


class Outcome(Base, UUIDMixin):
    __tablename__ = "outcomes"
    
    market_id: Mapped[UUID] = mapped_column(
        ForeignKey("markets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    market: Mapped["Market"] = relationship(back_populates="outcomes")
```

### Position モデル
```python
# backend/app/models/position.py
from decimal import Decimal
from uuid import UUID
from sqlalchemy import Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin, TimestampMixin


class Position(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "positions"
    __table_args__ = (
        UniqueConstraint("user_id", "market_id", "outcome_id", name="uq_position"),
    )
    
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    market_id: Mapped[UUID] = mapped_column(
        ForeignKey("markets.id"), nullable=False, index=True
    )
    outcome_id: Mapped[UUID] = mapped_column(
        ForeignKey("outcomes.id"), nullable=False
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    total_cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="positions")
    market: Mapped["Market"] = relationship()
    outcome: Mapped["Outcome"] = relationship()
```

### Transaction モデル
```python
# backend/app/models/transaction.py
from decimal import Decimal
from uuid import UUID
from sqlalchemy import Numeric, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.models.base import Base, UUIDMixin, TimestampMixin


class TransactionType(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"
    PAYOUT = "payout"
    REFUND = "refund"


class Transaction(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "transactions"
    
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    market_id: Mapped[UUID] = mapped_column(
        ForeignKey("markets.id"), nullable=False, index=True
    )
    outcome_id: Mapped[UUID] = mapped_column(
        ForeignKey("outcomes.id"), nullable=False
    )
    type: Mapped[TransactionType] = mapped_column(
        SQLEnum(TransactionType, name="transaction_type"),
        nullable=False,
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    balance_after: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="transactions")
    market: Mapped["Market"] = relationship()
    outcome: Mapped["Outcome"] = relationship()
```

## モデル登録 (__init__.py)
```python
# backend/app/models/__init__.py
from app.models.base import Base
from app.models.user import User, UserRole
from app.models.category import Category
from app.models.market import Market, MarketType, MarketStatus, Visibility
from app.models.outcome import Outcome
from app.models.position import Position
from app.models.transaction import Transaction, TransactionType
from app.models.price_history import PriceHistory

__all__ = [
    "Base",
    "User",
    "UserRole",
    "Category",
    "Market",
    "MarketType",
    "MarketStatus",
    "Visibility",
    "Outcome",
    "Position",
    "Transaction",
    "TransactionType",
    "PriceHistory",
]
```

## 型アノテーション注意点
- `Mapped[str | None]` で Nullable カラムを表現
- `Mapped[list["Model"]]` で1対多リレーションを表現
- 循環参照は文字列 `"Model"` で解決

## 関連ドキュメント
- SPEC.md Section 4: データモデル設計
- PLAN.md Task 1.2, 3.3, 4.1: モデル関連タスク
