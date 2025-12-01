# 社内予測市場システム (Internal Prediction Market)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Google Market Predictionをモデルとした、社内向けの予測市場システム。
社員の「集合知」を活用し、プロジェクトの成功確率、納期遵守の可能性、KPI達成の見込みなどを定量的に予測・可視化します。

## 📋 概要

このシステムは、仮想通貨（ポイント）を用いた取引により、組織内の不確実性を可視化し、早期のリスク検知や意思決定の質向上に寄与することを目的としています。

### 主な特徴

- 🎯 **集合知の活用**: 役職や部署を超えた多様な視点からの予測を集約
- 🎮 **ゲーミフィケーション**: 仮想通貨による取引で参加インセンティブを創出
- 📊 **透明性**: リアルタイムでの確率変動と予測トレンドの可視化
- 🔒 **セキュリティ**: Microsoft Entra ID (Azure AD) による SSO 認証
- 📱 **モバイル対応**: レスポンシブデザインでスマホからも快適に利用可能

## 🏗️ 技術スタック

### インフラ (Azure)
- **Azure Container Apps**: コンテナホスティング
- **Azure Database for PostgreSQL**: メインデータベース
- **Azure Cache for Redis**: キャッシュ・セッション管理
- **Azure Container Registry**: コンテナイメージ管理
- **Microsoft Entra ID**: 認証・認可

### Backend
- **Python 3.11+**
- **FastAPI**: 高速な非同期APIフレームワーク
- **SQLAlchemy (Async)**: ORMとデータベース管理
- **Alembic**: データベースマイグレーション
- **LMSR**: 予測市場の価格計算アルゴリズム

### Frontend
- **Next.js 14** (App Router)
- **TypeScript**: 型安全な開発
- **Tailwind CSS**: ユーティリティファーストCSS
- **Recharts**: データ可視化ライブラリ

### 開発ツール
- **Poetry**: Python依存関係管理
- **Ruff**: 高速Linter & Formatter
- **Pytest**: テストフレームワーク
- **Playwright**: E2Eテスト
- **GitHub Actions**: CI/CD

## 📂 プロジェクト構成

```
market-prediction/
├── backend/          # FastAPI バックエンド
│   ├── app/
│   │   ├── api/      # APIエンドポイント
│   │   ├── core/     # 設定・認証・LMSR
│   │   ├── models/   # SQLAlchemyモデル
│   │   └── services/ # ビジネスロジック
│   ├── tests/        # テストコード
│   └── pyproject.toml
├── frontend/         # Next.js フロントエンド
│   ├── src/
│   │   ├── app/      # App Router pages
│   │   ├── components/
│   │   └── lib/      # ユーティリティ
│   └── package.json
├── infra/            # IaC (Bicep/Terraform)
├── prompt/           # 仕様書・実装計画
│   ├── SPEC.md       # 機能仕様書
│   └── PLAN.md       # 実装計画
└── docker-compose.yml
```

## 🚀 クイックスタート

### 前提条件

- Docker & Docker Compose
- Node.js 20+
- Python 3.11+
- Poetry

### ローカル開発環境のセットアップ

```bash
# リポジトリのクローン
git clone https://github.com/takurot-pco/market-prediction.git
cd market-prediction

# Docker Compose で起動
docker-compose up -d

# Backend: http://localhost:8000
# Frontend: http://localhost:3000
# PostgreSQL: localhost:5432
```

### Backend のセットアップ (個別実行)

```bash
cd backend

# 依存関係のインストール
poetry install

# データベースマイグレーション
poetry run alembic upgrade head

# 開発サーバー起動
poetry run uvicorn app.main:app --reload
```

### Frontend のセットアップ (個別実行)

```bash
cd frontend

# 依存関係のインストール
npm install

# 開発サーバー起動
npm run dev
```

## 📖 ドキュメント

- **[機能仕様書 (SPEC.md)](./prompt/SPEC.md)**: システムの全体像・要件定義
- **[実装計画 (PLAN.md)](./prompt/PLAN.md)**: フェーズ別のタスク管理

## 🧪 テスト

```bash
# Backend テスト
cd backend
poetry run pytest

# Frontend テスト
cd frontend
npm run test

# E2E テスト
npm run test:e2e
```

## 📦 デプロイ

本番環境へのデプロイは GitHub Actions によって自動化されています。

```bash
# Mainブランチへのマージで自動的にDevにデプロイ
git push origin main
```

詳細は [PLAN.md - Phase 7](./prompt/PLAN.md#phase-7-azure本番環境構築-production-deployment) を参照してください。

## 🛠️ 開発ロードマップ

### Phase 1: 基盤構築 ✅ (予定)
- プロジェクトセットアップ
- データベース設計
- CI/CD パイプライン

### Phase 2: 認証・ユーザー管理 🚧 (進行中)
- JWT認証
- Azure AD連携
- RBAC実装

### Phase 3-8: 機能実装 📅 (予定)
詳細は [PLAN.md](./prompt/PLAN.md) をご覧ください。

## 🤝 コントリビューション

このプロジェクトは社内向けシステムのため、外部からのコントリビューションは現在受け付けておりません。

## 📄 ライセンス

MIT License - 詳細は [LICENSE](LICENSE) ファイルを参照してください。

## 📞 サポート

質問や問題がある場合は、GitHub Issues または社内Slackチャンネル (#prediction-market) でお問い合わせください。

---

**Built with ❤️ by the Engineering Team**
