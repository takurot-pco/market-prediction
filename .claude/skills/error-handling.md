# Error Handling

## Overview
SPEC.md Section 8 に準拠したエラーハンドリングの実装支援を行います。

## エラーコード一覧

### 取引エラー (400 Bad Request)
| エラーコード | 説明 |
|-------------|------|
| `INSUFFICIENT_BALANCE` | 残高不足 |
| `INSUFFICIENT_POSITION` | 保有数量不足（売却時） |
| `MARKET_NOT_OPEN` | マーケットが取引可能状態でない |
| `INVALID_QUANTITY` | 無効な数量指定 |
| `PRICE_BOUNDARY_EXCEEDED` | 価格境界（0.1%-99.9%）超過 |

### 認証・認可エラー
| エラーコード | HTTPステータス | 説明 |
|-------------|---------------|------|
| `UNAUTHORIZED` | 401 | 認証が必要 |
| `TOKEN_EXPIRED` | 401 | トークン期限切れ |
| `FORBIDDEN` | 403 | 権限不足 |

### 一般エラー
| エラーコード | HTTPステータス | 説明 |
|-------------|---------------|------|
| `NOT_FOUND` | 404 | リソースが見つからない |
| `VALIDATION_ERROR` | 422 | 入力値バリデーションエラー |
| `INTERNAL_ERROR` | 500 | 内部エラー |

## レスポンス形式

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

## 実装

### カスタム例外クラス

```python
# backend/app/core/exceptions.py
from typing import Any


class AppException(Exception):
    """アプリケーション基底例外"""
    
    def __init__(
        self,
        error_code: str,
        message: str,
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


# === 取引エラー ===

class InsufficientBalanceError(AppException):
    """残高不足"""
    
    def __init__(self, required: float, available: float):
        super().__init__(
            error_code="INSUFFICIENT_BALANCE",
            message="Not enough balance to complete this trade",
            status_code=400,
            details={"required": required, "available": available},
        )


class InsufficientPositionError(AppException):
    """保有数量不足"""
    
    def __init__(self, requested: float, available: float):
        super().__init__(
            error_code="INSUFFICIENT_POSITION",
            message="Not enough position to sell",
            status_code=400,
            details={"requested": requested, "available": available},
        )


class MarketNotOpenError(AppException):
    """マーケットが取引可能でない"""
    
    def __init__(self, market_id: str, current_status: str):
        super().__init__(
            error_code="MARKET_NOT_OPEN",
            message=f"Market is not open for trading. Current status: {current_status}",
            status_code=400,
            details={"market_id": market_id, "status": current_status},
        )


class InvalidQuantityError(AppException):
    """無効な数量"""
    
    def __init__(self, quantity: float, reason: str):
        super().__init__(
            error_code="INVALID_QUANTITY",
            message=f"Invalid quantity: {reason}",
            status_code=400,
            details={"quantity": quantity, "reason": reason},
        )


class PriceBoundaryExceededError(AppException):
    """価格境界超過"""
    
    def __init__(self, probability: float):
        super().__init__(
            error_code="PRICE_BOUNDARY_EXCEEDED",
            message="Trade would push probability outside allowed bounds (0.1% - 99.9%)",
            status_code=400,
            details={"resulting_probability": probability},
        )


# === 認証エラー ===

class UnauthorizedError(AppException):
    """認証エラー"""
    
    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            error_code="UNAUTHORIZED",
            message=message,
            status_code=401,
        )


class TokenExpiredError(AppException):
    """トークン期限切れ"""
    
    def __init__(self):
        super().__init__(
            error_code="TOKEN_EXPIRED",
            message="Token has expired",
            status_code=401,
        )


class ForbiddenError(AppException):
    """権限不足"""
    
    def __init__(self, required_role: str | None = None):
        message = "You don't have permission to perform this action"
        details = {}
        if required_role:
            message = f"Required role: {required_role}"
            details["required_role"] = required_role
        super().__init__(
            error_code="FORBIDDEN",
            message=message,
            status_code=403,
            details=details,
        )


# === 一般エラー ===

class NotFoundError(AppException):
    """リソース不存在"""
    
    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            error_code="NOT_FOUND",
            message=f"{resource} not found",
            status_code=404,
            details={"resource": resource, "id": resource_id},
        )


class ValidationError(AppException):
    """バリデーションエラー"""
    
    def __init__(self, errors: list[dict]):
        super().__init__(
            error_code="VALIDATION_ERROR",
            message="Validation failed",
            status_code=422,
            details={"errors": errors},
        )
```

### 例外ハンドラー

```python
# backend/app/core/error_handlers.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.exceptions import AppException


def setup_error_handlers(app: FastAPI) -> None:
    """エラーハンドラーを設定"""
    
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        """カスタム例外ハンドラー"""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error_code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
            },
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Pydantic バリデーションエラー"""
        errors = []
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            })
        return JSONResponse(
            status_code=422,
            content={
                "error_code": "VALIDATION_ERROR",
                "message": "Validation failed",
                "details": {"errors": errors},
            },
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """予期しないエラー"""
        # ログ出力
        import logging
        logging.error(f"Unexpected error: {exc}", exc_info=True)
        
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": {},
            },
        )
```

### main.pyへの統合

```python
# backend/app/main.py
from fastapi import FastAPI
from app.core.error_handlers import setup_error_handlers

app = FastAPI(
    title="Market Prediction API",
    description="Internal Prediction Market System API",
    version="0.1.0"
)

# エラーハンドラー設定
setup_error_handlers(app)
```

## 使用例

### サービス層での例外発生

```python
# backend/app/services/trading.py
from decimal import Decimal
from app.core.exceptions import (
    InsufficientBalanceError,
    InsufficientPositionError,
    MarketNotOpenError,
)
from app.models.market import MarketStatus


async def execute_trade(
    db: AsyncSession,
    user: User,
    market: Market,
    outcome_id: UUID,
    action: str,
    quantity: Decimal,
) -> Transaction:
    """取引を実行"""
    
    # マーケット状態チェック
    if market.status != MarketStatus.OPEN:
        raise MarketNotOpenError(
            market_id=str(market.id),
            current_status=market.status.value,
        )
    
    # コスト計算
    cost = calculate_trade_cost(market, outcome_id, quantity)
    
    if action == "buy":
        # 残高チェック
        if user.balance < cost:
            raise InsufficientBalanceError(
                required=float(cost),
                available=float(user.balance),
            )
    
    elif action == "sell":
        # ポジションチェック
        position = await get_position(db, user.id, market.id, outcome_id)
        if not position or position.quantity < quantity:
            raise InsufficientPositionError(
                requested=float(quantity),
                available=float(position.quantity if position else 0),
            )
    
    # 取引実行...
```

### API層での例外発生

```python
# backend/app/api/v1/markets.py
from app.core.exceptions import NotFoundError, ForbiddenError


@router.get("/{market_id}")
async def get_market(
    market_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MarketResponse:
    """マーケット詳細を取得"""
    market = await market_service.get_by_id(db, market_id)
    
    if not market:
        raise NotFoundError("Market", str(market_id))
    
    # 可視性チェック
    if market.visibility == Visibility.DEPARTMENT:
        if current_user.department != market.creator.department:
            raise ForbiddenError()
    
    return market
```

## フロントエンドでのエラー処理

```typescript
// frontend/lib/api.ts
interface ApiError {
  error_code: string;
  message: string;
  details: Record<string, unknown>;
}

export async function apiRequest<T>(
  url: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error: ApiError = await response.json();
    throw new ApiRequestError(error);
  }

  return response.json();
}

export class ApiRequestError extends Error {
  constructor(public readonly error: ApiError) {
    super(error.message);
    this.name = "ApiRequestError";
  }

  get errorCode(): string {
    return this.error.error_code;
  }

  get details(): Record<string, unknown> {
    return this.error.details;
  }
}

// 使用例
try {
  await apiRequest("/api/v1/markets/123/trade", {
    method: "POST",
    body: JSON.stringify({ outcome_id: "abc", action: "buy", quantity: 10 }),
  });
} catch (err) {
  if (err instanceof ApiRequestError) {
    switch (err.errorCode) {
      case "INSUFFICIENT_BALANCE":
        alert(`残高不足です。必要: ${err.details.required}P, 残高: ${err.details.available}P`);
        break;
      case "MARKET_NOT_OPEN":
        alert("このマーケットは現在取引できません");
        break;
      default:
        alert(err.message);
    }
  }
}
```

## 関連ドキュメント
- SPEC.md Section 8: エラーハンドリング
- PLAN.md Task 1.4: 共通エラーハンドリング基盤
