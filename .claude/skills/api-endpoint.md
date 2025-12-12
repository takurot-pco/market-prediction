# FastAPI Endpoint Generator

## Overview
SPEC.md Section 5 に準拠した FastAPI エンドポイントの実装支援を行います。

## プロジェクト規約

### パス構造
```
/api/v1/{resource}
/api/v1/{resource}/{id}
/api/v1/{resource}/{id}/{action}
```

### ディレクトリ構成
```
backend/app/api/
├── __init__.py
├── deps.py          # 共通依存関係
├── v1/
│   ├── __init__.py
│   ├── router.py    # メインルーター
│   ├── auth.py
│   ├── users.py
│   ├── markets.py
│   ├── trading.py
│   └── categories.py
```

## 実装テンプレート

### 基本エンドポイント
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.market import MarketCreate, MarketResponse, MarketListResponse

router = APIRouter(prefix="/markets", tags=["markets"])


@router.get(
    "",
    response_model=MarketListResponse,
    summary="マーケット一覧取得",
    description="公開中のマーケット一覧を取得します。カテゴリやステータスでフィルタ可能。",
)
async def list_markets(
    category_id: UUID | None = None,
    status: str | None = None,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MarketListResponse:
    """マーケット一覧を取得"""
    # Implementation here
    pass


@router.get(
    "/{market_id}",
    response_model=MarketResponse,
    summary="マーケット詳細取得",
    responses={404: {"description": "Market not found"}},
)
async def get_market(
    market_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MarketResponse:
    """マーケット詳細と現在価格を取得"""
    market = await market_service.get_by_id(db, market_id)
    if not market:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "NOT_FOUND", "message": "Market not found"},
        )
    return market


@router.post(
    "",
    response_model=MarketResponse,
    status_code=status.HTTP_201_CREATED,
    summary="マーケット作成",
)
async def create_market(
    market_in: MarketCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MarketResponse:
    """新規マーケットを作成（Moderator以上）"""
    # Role check
    if current_user.role not in ["admin", "moderator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error_code": "FORBIDDEN", "message": "Insufficient permissions"},
        )
    return await market_service.create(db, market_in, current_user.id)
```

### 依存関係 (deps.py)
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt

from app.db.session import async_session
from app.models.user import User
from app.core.config import settings

security = HTTPBearer()


async def get_db() -> AsyncSession:
    """データベースセッションを取得"""
    async with async_session() as session:
        yield session


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """現在のユーザーを取得"""
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=["HS256"],
        )
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error_code": "UNAUTHORIZED", "message": "Invalid token"},
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error_code": "TOKEN_EXPIRED", "message": "Token expired or invalid"},
        )
    
    user = await user_service.get_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error_code": "UNAUTHORIZED", "message": "User not found"},
        )
    return user


def require_role(*roles: str):
    """ロールチェック用デコレータファクトリ"""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error_code": "FORBIDDEN", "message": f"Required role: {', '.join(roles)}"},
            )
        return current_user
    return role_checker
```

### Pydantic スキーマ
```python
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from enum import Enum


class MarketStatus(str, Enum):
    DRAFT = "draft"
    OPEN = "open"
    CLOSED = "closed"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"


class MarketCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    category_id: UUID
    market_type: str = "binary"
    liquidity_param: float = Field(default=100.0, ge=10, le=10000)
    start_at: datetime
    end_at: datetime
    resolution_date: datetime


class MarketResponse(BaseModel):
    id: UUID
    title: str
    description: str | None
    status: MarketStatus
    current_probabilities: dict[str, float]  # outcome_id -> probability
    created_at: datetime
    
    model_config = {"from_attributes": True}
```

## エラーレスポンス形式
```json
{
  "error_code": "INSUFFICIENT_BALANCE",
  "message": "Not enough balance to complete this trade",
  "details": {
    "required": 150.00,
    "available": 100.00
  }
}
```

## ルーター登録 (main.py)
```python
from app.api.v1 import router as api_v1_router

app.include_router(api_v1_router, prefix="/api/v1")
```

## 関連ドキュメント
- SPEC.md Section 5: API設計
- SPEC.md Section 8: エラーハンドリング
- PLAN.md Phase 2-5: 各機能実装タスク
