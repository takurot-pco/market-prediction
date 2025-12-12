# TypeScript API Client Generator

## Overview
フロントエンドからバックエンドAPIを呼び出すための型安全なAPIクライアントの実装支援を行います。

## ディレクトリ構成

```
frontend/
├── lib/
│   ├── api/
│   │   ├── client.ts       # ベースクライアント
│   │   ├── auth.ts         # 認証API
│   │   ├── markets.ts      # マーケットAPI
│   │   ├── trading.ts      # 取引API
│   │   └── users.ts        # ユーザーAPI
│   └── types/
│       ├── api.ts          # API共通型
│       ├── market.ts       # マーケット型
│       ├── user.ts         # ユーザー型
│       └── trading.ts      # 取引型
```

## 型定義

### 共通型
```typescript
// frontend/lib/types/api.ts

export interface ApiResponse<T> {
  data: T;
  status: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}

export interface ApiError {
  error_code: string;
  message: string;
  details: Record<string, unknown>;
}
```

### マーケット型
```typescript
// frontend/lib/types/market.ts

export type MarketStatus = "draft" | "open" | "closed" | "resolved" | "cancelled";
export type MarketType = "binary" | "categorical" | "scalar";
export type Visibility = "public" | "department" | "invited";

export interface Outcome {
  id: string;
  label: string;
  probability: number;
  quantity: number;
}

export interface Market {
  id: string;
  title: string;
  description: string | null;
  categoryId: string;
  marketType: MarketType;
  status: MarketStatus;
  visibility: Visibility;
  liquidityParam: number;
  startAt: string;
  endAt: string;
  resolutionDate: string;
  resolvedAt: string | null;
  resolvedOutcomeId: string | null;
  createdBy: string;
  createdAt: string;
  updatedAt: string;
  outcomes: Outcome[];
  currentProbabilities: Record<string, number>;
}

export interface MarketCreate {
  title: string;
  description?: string;
  categoryId: string;
  marketType?: MarketType;
  liquidityParam?: number;
  startAt: string;
  endAt: string;
  resolutionDate: string;
  visibility?: Visibility;
  outcomes?: Array<{ label: string }>;
}

export interface MarketListParams {
  categoryId?: string;
  status?: MarketStatus;
  visibility?: Visibility;
  page?: number;
  pageSize?: number;
}
```

### ユーザー型
```typescript
// frontend/lib/types/user.ts

export type UserRole = "admin" | "moderator" | "user";

export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  department: string | null;
  balance: number;
  createdAt: string;
  updatedAt: string;
}

export interface Position {
  id: string;
  marketId: string;
  marketTitle: string;
  outcomeId: string;
  outcomeLabel: string;
  quantity: number;
  totalCost: number;
  currentValue: number;
  profitLoss: number;
}

export interface Transaction {
  id: string;
  marketId: string;
  marketTitle: string;
  outcomeId: string;
  outcomeLabel: string;
  type: "buy" | "sell" | "payout" | "refund";
  quantity: number;
  cost: number;
  balanceAfter: number;
  createdAt: string;
}
```

### 取引型
```typescript
// frontend/lib/types/trading.ts

export interface TradeEstimate {
  cost: number;
  newProbability: number;
  potentialPayout: number;
  executable: boolean;
  reason?: string;
}

export interface TradeRequest {
  outcomeId: string;
  action: "buy" | "sell";
  quantity: number;
}

export interface TradeResult {
  transactionId: string;
  quantity: number;
  cost: number;
  newBalance: number;
  newProbability: number;
}
```

## ベースクライアント

```typescript
// frontend/lib/api/client.ts

import { ApiError } from "@/lib/types/api";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "";

export class ApiRequestError extends Error {
  constructor(
    public readonly errorCode: string,
    message: string,
    public readonly details: Record<string, unknown> = {},
    public readonly status: number = 400,
  ) {
    super(message);
    this.name = "ApiRequestError";
  }
}

interface RequestOptions extends RequestInit {
  params?: Record<string, string | number | boolean | undefined>;
}

async function getAuthToken(): Promise<string | null> {
  // Cookie または localStorage からトークンを取得
  if (typeof window !== "undefined") {
    return localStorage.getItem("auth_token");
  }
  return null;
}

function buildUrl(path: string, params?: Record<string, string | number | boolean | undefined>): string {
  const url = new URL(`${API_BASE_URL}${path}`, window.location.origin);
  
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        url.searchParams.set(key, String(value));
      }
    });
  }
  
  return url.toString();
}

export async function apiClient<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { params, ...fetchOptions } = options;
  const url = buildUrl(path, params);
  
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...options.headers,
  };
  
  // 認証トークンを追加
  const token = await getAuthToken();
  if (token) {
    (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
  }
  
  const response = await fetch(url, {
    ...fetchOptions,
    headers,
  });
  
  if (!response.ok) {
    let error: ApiError;
    try {
      error = await response.json();
    } catch {
      error = {
        error_code: "UNKNOWN_ERROR",
        message: response.statusText,
        details: {},
      };
    }
    
    throw new ApiRequestError(
      error.error_code,
      error.message,
      error.details,
      response.status,
    );
  }
  
  // 204 No Content の場合
  if (response.status === 204) {
    return undefined as T;
  }
  
  return response.json();
}

// HTTPメソッドヘルパー
export const api = {
  get: <T>(path: string, params?: Record<string, string | number | boolean | undefined>) =>
    apiClient<T>(path, { method: "GET", params }),
  
  post: <T>(path: string, data?: unknown) =>
    apiClient<T>(path, {
      method: "POST",
      body: data ? JSON.stringify(data) : undefined,
    }),
  
  put: <T>(path: string, data?: unknown) =>
    apiClient<T>(path, {
      method: "PUT",
      body: data ? JSON.stringify(data) : undefined,
    }),
  
  delete: <T>(path: string) =>
    apiClient<T>(path, { method: "DELETE" }),
};
```

## APIモジュール

### 認証API
```typescript
// frontend/lib/api/auth.ts

import { api } from "./client";
import { User } from "@/lib/types/user";

export const authApi = {
  /**
   * 現在のユーザー情報を取得
   */
  async me(): Promise<User> {
    return api.get<User>("/api/v1/auth/me");
  },
  
  /**
   * ログアウト
   */
  async logout(): Promise<void> {
    await api.post("/api/v1/auth/logout");
    localStorage.removeItem("auth_token");
  },
  
  /**
   * SSOログインURLを取得
   */
  getLoginUrl(): string {
    return `${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/login`;
  },
};
```

### マーケットAPI
```typescript
// frontend/lib/api/markets.ts

import { api } from "./client";
import { PaginatedResponse } from "@/lib/types/api";
import {
  Market,
  MarketCreate,
  MarketListParams,
} from "@/lib/types/market";

export const marketsApi = {
  /**
   * マーケット一覧を取得
   */
  async list(params?: MarketListParams): Promise<PaginatedResponse<Market>> {
    return api.get<PaginatedResponse<Market>>("/api/v1/markets", {
      category_id: params?.categoryId,
      status: params?.status,
      visibility: params?.visibility,
      page: params?.page,
      page_size: params?.pageSize,
    });
  },
  
  /**
   * マーケット詳細を取得
   */
  async get(id: string): Promise<Market> {
    return api.get<Market>(`/api/v1/markets/${id}`);
  },
  
  /**
   * マーケットを作成
   */
  async create(data: MarketCreate): Promise<Market> {
    return api.post<Market>("/api/v1/markets", {
      title: data.title,
      description: data.description,
      category_id: data.categoryId,
      market_type: data.marketType,
      liquidity_param: data.liquidityParam,
      start_at: data.startAt,
      end_at: data.endAt,
      resolution_date: data.resolutionDate,
      visibility: data.visibility,
      outcomes: data.outcomes,
    });
  },
  
  /**
   * マーケットを更新
   */
  async update(id: string, data: Partial<MarketCreate>): Promise<Market> {
    return api.put<Market>(`/api/v1/markets/${id}`, data);
  },
  
  /**
   * マーケットを削除（DRAFTのみ）
   */
  async delete(id: string): Promise<void> {
    return api.delete(`/api/v1/markets/${id}`);
  },
  
  /**
   * マーケットを公開
   */
  async publish(id: string): Promise<Market> {
    return api.post<Market>(`/api/v1/markets/${id}/publish`);
  },
  
  /**
   * マーケットを解決
   */
  async resolve(id: string, outcomeId: string): Promise<Market> {
    return api.post<Market>(`/api/v1/markets/${id}/resolve`, {
      outcome_id: outcomeId,
    });
  },
  
  /**
   * マーケットをキャンセル
   */
  async cancel(id: string): Promise<Market> {
    return api.post<Market>(`/api/v1/markets/${id}/cancel`);
  },
  
  /**
   * 価格履歴を取得
   */
  async getHistory(
    id: string,
    params?: { from?: string; to?: string; interval?: "1h" | "1d" },
  ): Promise<Array<{ outcomeId: string; probability: number; recordedAt: string }>> {
    return api.get(`/api/v1/markets/${id}/history`, params);
  },
};
```

### 取引API
```typescript
// frontend/lib/api/trading.ts

import { api } from "./client";
import { TradeEstimate, TradeRequest, TradeResult } from "@/lib/types/trading";

export const tradingApi = {
  /**
   * 取引見積もりを取得
   */
  async estimate(
    marketId: string,
    outcomeId: string,
    action: "buy" | "sell",
    quantity: number,
  ): Promise<TradeEstimate> {
    return api.get<TradeEstimate>(`/api/v1/markets/${marketId}/estimate`, {
      outcome_id: outcomeId,
      action,
      quantity,
    });
  },
  
  /**
   * 取引を実行
   */
  async execute(marketId: string, request: TradeRequest): Promise<TradeResult> {
    return api.post<TradeResult>(`/api/v1/markets/${marketId}/trade`, {
      outcome_id: request.outcomeId,
      action: request.action,
      quantity: request.quantity,
    });
  },
};
```

### ユーザーAPI
```typescript
// frontend/lib/api/users.ts

import { api } from "./client";
import { PaginatedResponse } from "@/lib/types/api";
import { User, Position, Transaction } from "@/lib/types/user";

export const usersApi = {
  /**
   * 自分のプロフィールを取得
   */
  async getProfile(): Promise<User> {
    return api.get<User>("/api/v1/users/me");
  },
  
  /**
   * 自分のプロフィールを更新
   */
  async updateProfile(data: { name?: string; department?: string }): Promise<User> {
    return api.put<User>("/api/v1/users/me", data);
  },
  
  /**
   * 自分のポジション一覧を取得
   */
  async getPositions(): Promise<Position[]> {
    return api.get<Position[]>("/api/v1/users/me/positions");
  },
  
  /**
   * 自分の取引履歴を取得
   */
  async getTransactions(params?: {
    page?: number;
    pageSize?: number;
  }): Promise<PaginatedResponse<Transaction>> {
    return api.get<PaginatedResponse<Transaction>>(
      "/api/v1/users/me/transactions",
      { page: params?.page, page_size: params?.pageSize },
    );
  },
  
  /**
   * ユーザー情報を取得（Admin）
   */
  async getUser(id: string): Promise<User> {
    return api.get<User>(`/api/v1/users/${id}`);
  },
  
  /**
   * ユーザーロールを変更（Admin）
   */
  async updateRole(id: string, role: "admin" | "moderator" | "user"): Promise<User> {
    return api.put<User>(`/api/v1/users/${id}/role`, { role });
  },
};
```

## React Hooksでの使用

```typescript
// frontend/hooks/useMarkets.ts
"use client";

import { useState, useEffect, useCallback } from "react";
import { marketsApi } from "@/lib/api/markets";
import { Market, MarketListParams } from "@/lib/types/market";
import { ApiRequestError } from "@/lib/api/client";

export function useMarkets(params?: MarketListParams) {
  const [markets, setMarkets] = useState<Market[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const fetchMarkets = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await marketsApi.list(params);
      setMarkets(response.items);
      setTotal(response.total);
    } catch (err) {
      if (err instanceof ApiRequestError) {
        setError(err.message);
      } else {
        setError("Failed to fetch markets");
      }
    } finally {
      setIsLoading(false);
    }
  }, [params]);
  
  useEffect(() => {
    fetchMarkets();
  }, [fetchMarkets]);
  
  return { markets, total, isLoading, error, refetch: fetchMarkets };
}
```

```typescript
// frontend/hooks/useTrade.ts
"use client";

import { useState, useCallback } from "react";
import { tradingApi } from "@/lib/api/trading";
import { TradeEstimate, TradeResult } from "@/lib/types/trading";
import { ApiRequestError } from "@/lib/api/client";

export function useTrade(marketId: string) {
  const [estimate, setEstimate] = useState<TradeEstimate | null>(null);
  const [isEstimating, setIsEstimating] = useState(false);
  const [isTrading, setIsTrading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const getEstimate = useCallback(
    async (outcomeId: string, action: "buy" | "sell", quantity: number) => {
      setIsEstimating(true);
      setError(null);
      
      try {
        const result = await tradingApi.estimate(marketId, outcomeId, action, quantity);
        setEstimate(result);
        return result;
      } catch (err) {
        if (err instanceof ApiRequestError) {
          setError(err.message);
        }
        return null;
      } finally {
        setIsEstimating(false);
      }
    },
    [marketId],
  );
  
  const executeTrade = useCallback(
    async (outcomeId: string, action: "buy" | "sell", quantity: number): Promise<TradeResult | null> => {
      setIsTrading(true);
      setError(null);
      
      try {
        const result = await tradingApi.execute(marketId, { outcomeId, action, quantity });
        return result;
      } catch (err) {
        if (err instanceof ApiRequestError) {
          setError(err.message);
        }
        return null;
      } finally {
        setIsTrading(false);
      }
    },
    [marketId],
  );
  
  return {
    estimate,
    isEstimating,
    isTrading,
    error,
    getEstimate,
    executeTrade,
  };
}
```

## 関連ドキュメント
- SPEC.md Section 5: API設計
- SPEC.md Section 8: エラーハンドリング
- skills/component.md: Reactコンポーネント実装
