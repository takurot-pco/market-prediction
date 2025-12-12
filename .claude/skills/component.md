# React Component Generator

## Overview
Next.js 14 (App Router) + TypeScript + Tailwind CSS を使用したコンポーネント作成を支援します。

## プロジェクト規約

### ディレクトリ構成
```
frontend/
├── app/                    # App Router ページ
│   ├── layout.tsx          # ルートレイアウト
│   ├── page.tsx            # ホームページ
│   ├── globals.css         # グローバルスタイル
│   ├── (auth)/             # 認証グループ
│   │   ├── login/
│   │   └── logout/
│   ├── markets/
│   │   ├── page.tsx        # マーケット一覧
│   │   └── [id]/
│   │       └── page.tsx    # マーケット詳細
│   ├── portfolio/
│   └── admin/
├── components/             # 共有コンポーネント
│   ├── ui/                 # 基本UI部品
│   ├── markets/            # マーケット関連
│   ├── trading/            # 取引関連
│   └── layout/             # レイアウト
├── lib/                    # ユーティリティ
│   ├── api.ts              # APIクライアント
│   └── utils.ts            # ヘルパー関数
├── hooks/                  # カスタムフック
└── types/                  # 型定義
```

### デザインシステム
- **カラー**: 青・グレー基調（信頼感のあるデザイン）
- **フォント**: system-ui, sans-serif
- **スペーシング**: Tailwind のデフォルトスケール使用
- **モバイルファースト**: レスポンシブ対応必須

## コンポーネントテンプレート

### Server Component (デフォルト)
```tsx
// frontend/app/markets/page.tsx
import { MarketList } from "@/components/markets/MarketList";
import { getMarkets } from "@/lib/api";

export default async function MarketsPage() {
  const markets = await getMarkets();

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">マーケット一覧</h1>
      <MarketList markets={markets} />
    </div>
  );
}
```

### Client Component
```tsx
// frontend/components/trading/TradeForm.tsx
"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";

interface TradeFormProps {
  marketId: string;
  outcomes: Array<{
    id: string;
    label: string;
    probability: number;
  }>;
  userBalance: number;
}

export function TradeForm({ marketId, outcomes, userBalance }: TradeFormProps) {
  const router = useRouter();
  const [selectedOutcome, setSelectedOutcome] = useState<string | null>(null);
  const [quantity, setQuantity] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedOutcome) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/v1/markets/${marketId}/trade`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          outcome_id: selectedOutcome,
          action: "buy",
          quantity,
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.message || "取引に失敗しました");
      }

      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "エラーが発生しました");
    } finally {
      setIsLoading(false);
    }
  }, [marketId, selectedOutcome, quantity, router]);

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Outcome Selection */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700">
          予測を選択
        </label>
        <div className="grid grid-cols-2 gap-4">
          {outcomes.map((outcome) => (
            <button
              key={outcome.id}
              type="button"
              onClick={() => setSelectedOutcome(outcome.id)}
              className={`
                p-4 rounded-lg border-2 transition-all
                ${selectedOutcome === outcome.id
                  ? "border-blue-500 bg-blue-50"
                  : "border-gray-200 hover:border-gray-300"
                }
              `}
            >
              <div className="font-medium">{outcome.label}</div>
              <div className="text-2xl font-bold text-blue-600">
                {(outcome.probability * 100).toFixed(1)}%
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Quantity Slider */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700">
          数量: {quantity}
        </label>
        <input
          type="range"
          min={1}
          max={100}
          value={quantity}
          onChange={(e) => setQuantity(Number(e.target.value))}
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
        />
      </div>

      {/* Error Message */}
      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Submit Button */}
      <button
        type="submit"
        disabled={!selectedOutcome || isLoading}
        className={`
          w-full py-3 px-4 rounded-lg font-medium text-white transition-colors
          ${!selectedOutcome || isLoading
            ? "bg-gray-300 cursor-not-allowed"
            : "bg-blue-600 hover:bg-blue-700"
          }
        `}
      >
        {isLoading ? "処理中..." : "購入する"}
      </button>
    </form>
  );
}
```

### マーケットカードコンポーネント
```tsx
// frontend/components/markets/MarketCard.tsx
import Link from "next/link";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

interface MarketCardProps {
  market: {
    id: string;
    title: string;
    status: "open" | "closed" | "resolved";
    probability: number;
    trend: "up" | "down" | "stable";
    endAt: string;
  };
}

export function MarketCard({ market }: MarketCardProps) {
  const TrendIcon = {
    up: TrendingUp,
    down: TrendingDown,
    stable: Minus,
  }[market.trend];

  const trendColor = {
    up: "text-green-500",
    down: "text-red-500",
    stable: "text-gray-400",
  }[market.trend];

  const statusBadge = {
    open: "bg-green-100 text-green-800",
    closed: "bg-yellow-100 text-yellow-800",
    resolved: "bg-gray-100 text-gray-800",
  }[market.status];

  return (
    <Link href={`/markets/${market.id}`}>
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <h3 className="font-medium text-gray-900 line-clamp-2">
            {market.title}
          </h3>
          <span className={`px-2 py-1 text-xs font-medium rounded-full ${statusBadge}`}>
            {market.status.toUpperCase()}
          </span>
        </div>

        {/* Probability */}
        <div className="flex items-end gap-2 mb-4">
          <span className="text-4xl font-bold text-blue-600">
            {(market.probability * 100).toFixed(0)}%
          </span>
          <TrendIcon className={`w-5 h-5 ${trendColor}`} />
        </div>

        {/* Footer */}
        <div className="text-sm text-gray-500">
          終了: {new Date(market.endAt).toLocaleDateString("ja-JP")}
        </div>
      </div>
    </Link>
  );
}
```

### レイアウトコンポーネント
```tsx
// frontend/components/layout/Header.tsx
"use client";

import Link from "next/link";
import { useAuth } from "@/hooks/useAuth";

export function Header() {
  const { user, logout } = useAuth();

  return (
    <header className="bg-white border-b border-gray-200">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="font-bold text-xl text-blue-600">
            Prediction Market
          </Link>

          {/* Navigation */}
          <nav className="hidden md:flex items-center gap-6">
            <Link href="/markets" className="text-gray-600 hover:text-gray-900">
              マーケット
            </Link>
            <Link href="/portfolio" className="text-gray-600 hover:text-gray-900">
              ポートフォリオ
            </Link>
            <Link href="/leaderboard" className="text-gray-600 hover:text-gray-900">
              ランキング
            </Link>
          </nav>

          {/* User Info */}
          {user && (
            <div className="flex items-center gap-4">
              <div className="text-right">
                <div className="text-sm font-medium text-gray-900">
                  {user.name}
                </div>
                <div className="text-sm text-blue-600 font-medium">
                  {user.balance.toLocaleString()} P
                </div>
              </div>
              <button
                onClick={logout}
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                ログアウト
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
```

## カスタムフック

### useAuth
```tsx
// frontend/hooks/useAuth.ts
"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from "react";

interface User {
  id: string;
  name: string;
  email: string;
  balance: number;
  role: "admin" | "moderator" | "user";
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: () => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // 初期認証チェック
    fetch("/api/v1/auth/me")
      .then((res) => res.ok ? res.json() : null)
      .then(setUser)
      .finally(() => setIsLoading(false));
  }, []);

  const login = () => {
    window.location.href = "/api/v1/auth/login";
  };

  const logout = async () => {
    await fetch("/api/v1/auth/logout", { method: "POST" });
    setUser(null);
    window.location.href = "/";
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
```

## UI部品

### Button
```tsx
// frontend/components/ui/Button.tsx
import { ButtonHTMLAttributes, forwardRef } from "react";
import { clsx } from "clsx";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "danger";
  size?: "sm" | "md" | "lg";
  isLoading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "primary", size = "md", isLoading, className, children, disabled, ...props }, ref) => {
    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={clsx(
          "inline-flex items-center justify-center font-medium rounded-lg transition-colors",
          {
            "bg-blue-600 text-white hover:bg-blue-700": variant === "primary",
            "bg-gray-100 text-gray-700 hover:bg-gray-200": variant === "secondary",
            "bg-red-600 text-white hover:bg-red-700": variant === "danger",
            "px-3 py-1.5 text-sm": size === "sm",
            "px-4 py-2 text-base": size === "md",
            "px-6 py-3 text-lg": size === "lg",
            "opacity-50 cursor-not-allowed": disabled || isLoading,
          },
          className
        )}
        {...props}
      >
        {isLoading ? (
          <span className="animate-spin mr-2">⏳</span>
        ) : null}
        {children}
      </button>
    );
  }
);

Button.displayName = "Button";
```

## ローディング・エラー状態

### Loading
```tsx
// frontend/app/markets/loading.tsx
export default function Loading() {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="animate-pulse space-y-4">
        <div className="h-8 bg-gray-200 rounded w-1/4"></div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-48 bg-gray-200 rounded-xl"></div>
          ))}
        </div>
      </div>
    </div>
  );
}
```

### Error
```tsx
// frontend/app/markets/error.tsx
"use client";

export default function Error({
  error,
  reset,
}: {
  error: Error;
  reset: () => void;
}) {
  return (
    <div className="container mx-auto px-4 py-8 text-center">
      <h2 className="text-2xl font-bold text-gray-900 mb-4">
        エラーが発生しました
      </h2>
      <p className="text-gray-600 mb-6">{error.message}</p>
      <button
        onClick={reset}
        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
      >
        もう一度試す
      </button>
    </div>
  );
}
```

## 関連ドキュメント
- SPEC.md Section 3.8: UI/UXデザイン
- PLAN.md Task 3.6, 4.4, 5.2: フロントエンドタスク
