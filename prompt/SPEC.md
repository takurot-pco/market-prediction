# 社内予測市場システム (Internal Prediction Market) 仕様書

## 1. 概要 (Overview)

### 1.1. 目的
Google Market Predictionをモデルとした、社内向けの予測市場システムを構築する。
社員の「集合知」を活用し、プロジェクトの成功確率、納期遵守の可能性、KPI達成の見込みなどを定量的に予測・可視化することを目的とする。

### 1.2. コンセプト
*   **集合知の活用**: 役職や部署を超えた多様な視点からの予測を集約する。
*   **ゲーミフィケーション**: 仮想通貨（ポイント）を用いた取引により、参加へのインセンティブを高める。
*   **透明性**: 組織内の不確実性を可視化し、早期のリスク検知や意思決定の質向上に寄与する。

---

## 2. システムアーキテクチャ (System Architecture)

### 2.1. 推奨技術スタック (AWS Base)
*   **Infrastructure**: AWS App Runner or ECS/Fargate（コンテナ実行基盤）
*   **Frontend**: React / Next.js / Vue.js (SPA) - CloudFront + S3
*   **Backend**: Python (FastAPI) - App Runner / ECS タスク
    *   *数値計算ライブラリが豊富なPythonが予測エンジンには有利*
*   **Database**: Amazon RDS for PostgreSQL
*   **Cache/Queue**: Amazon ElastiCache for Redis / Amazon SQS
*   **Auth**: Amazon Cognito（または社内IdPのOIDC/SAML連携）

### 2.2. モジュール構成
1.  **Auth Service**: 認証・認可
2.  **Market Service**: 質問管理・予測エンジン (LMSR)
3.  **Ledger Service**: ウォレット・取引台帳・決済
4.  **Analytics Service**: ダッシュボード・統計分析
5.  **Notification Service**: 通知・外部連携

---

## 3. 機能要件 (Functional Requirements)

### 3.1. 認証・ユーザー管理
*   **SSOログイン**: 社内Google/Microsoftアカウントでのログイン。
*   **ロール管理**:
    *   `Admin`: 全権限（システム設定、ユーザー管理）。
    *   `Moderator`: マーケット作成・承認、結果認定。
    *   `User`: 一般参加者（取引のみ）。
*   **プロフィール**: 部署、役職、過去の予測成績（的中率、ROI）。

### 3.2. マーケット（質問）管理
*   **質問作成**:
    *   タイトル（例: 「プロジェクトXはQ3中にローンチできるか？」）
    *   詳細説明、判定基準（何をもってYESとするか）
    *   カテゴリ（プロダクト、営業、人事、業界動向）
    *   判定日（Resolution Date）
*   **マーケットタイプ**:
    *   **Binary**: YES / NO （確率は0%〜100%）
    *   **Categorical**: 選択肢 A / B / C ... （例: 次期主力製品の名称）
    *   **Scalar**: 数値範囲 （例: 売上 10億未満 / 10-12億 / 12億以上）
*   **公開範囲設定**: 全社公開 / 特定部署のみ / 招待制。

### 3.3. 取引エンジン (Trading Engine)
*   **自動マーケットメーカー (AMM)**:
    *   **LMSR (Logarithmic Market Scoring Rule)** アルゴリズムを採用。
    *   流動性を常に提供し、いつでも売買可能にする。
    *   価格（確率）は保有量に応じて自動変動する。
*   **注文処理**:
    *   Buy (Long): 特定の結果のシェアを購入。
    *   Sell (Short): 保有シェアを売却。
*   **コスト計算**: 現在の価格に基づき、必要ポイントを即時算出。

### 3.4. ウォレット・ポイント管理
*   **仮想通貨**: 社内通貨（例: "Prediction Point"）。
*   **初期配布**: 新規登録時、四半期ごとに一定額を付与。
*   **ポートフォリオ**: 保有中のポジション一覧と時価評価額。
*   **ランキング**: 獲得ポイント数によるリーダーボード（個人・部署対抗）。

### 3.5. 解決・精算 (Resolution & Settlement)
*   **結果入力**: モデレーターが事実に基づき結果（YES/NO等）を確定。
*   **ペイアウト**:
    *   正解のシェア: 1シェアあたり1ポイント（または100ポイント）で償還。
    *   不正解のシェア: 価値0になる。
*   **異議申し立て**: 結果確定前のレビュー期間（オプション）。

### 3.6. ダッシュボード・分析
*   **トレンドグラフ**: 予測確率の時系列推移（「プロジェクトXの成功確率が急落している」等の検知）。
*   **ヒートマップ**: 注目度の高い（取引量の多い）マーケットの可視化。
*   **個人成績**: 自分の予測精度、Brier Score（予測スコア）の表示。

### 3.7. UI/UX・デザイン (UI/UX Design)
*   **デザイン原則**:
    *   **Trustworthy & Professional**: 金融商品のような信頼感のあるデザイン（青・グレー基調）。
    *   **Simplicity**: 専門用語を避け、直感的に「確率」と「損益」がわかるインターフェース。
*   **主要画面構成**:
    *   **マーケットカード**: 質問タイトル、現在の確率（%）、トレンド（↑↓）をカード形式で一覧表示。
    *   **取引画面**:
        *   「YESを買う」「NOを買う」のシンプルな2ボタン。
        *   スライダーで数量を指定し、即座に「必要ポイント」と「予想ペイアウト」を表示。
    *   **ポートフォリオ**: 自分の保有資産の推移を美しいラインチャートで表示。
*   **インタラクション**:
    *   **リアルタイム更新**: WebSocket等を用い、他者の取引による価格変動を即座に画面に反映。
    *   **モバイルファースト**: 社内スマホからのアクセスを想定し、レスポンシブ対応を徹底。

---

## 4. データモデル設計 (Data Model Draft)

### Users
*   `id`, `email`, `name`, `role`, `department`, `created_at`

### Markets
*   `id`, `title`, `description`, `market_type` (binary/scalar), `status` (open/closed/resolved), `resolution_date`, `created_by`

### Outcomes (選択肢)
*   `id`, `market_id`, `label` (YES/NO, Option A...), `current_probability`

### Positions (保有状況)
*   `id`, `user_id`, `market_id`, `outcome_id`, `quantity` (保有シェア数), `average_price`

### Transactions (取引履歴)
*   `id`, `user_id`, `market_id`, `outcome_id`, `type` (buy/sell), `quantity`, `cost`, `timestamp`

### Wallets
*   `user_id`, `balance` (利用可能ポイント), `invested_amount` (投資中ポイント)

---

## 5. API設計 (Key Endpoints)

*   `GET /api/v1/markets`: マーケット一覧取得（フィルタリング、ソート）
*   `GET /api/v1/markets/{id}`: マーケット詳細・現在価格取得
*   `POST /api/v1/markets/{id}/trade`: 注文実行
    *   Body: `{ "outcome_id": "yes", "amount": 100, "action": "buy" }`
*   `GET /api/v1/users/me/portfolio`: 自分のポートフォリオ取得
*   `GET /api/v1/leaderboard`: ランキング取得

---

## 6. インセンティブ・運用設計

*   **インセンティブ**:
    *   上位入賞者への表彰（Amazonギフト券、社内表彰、ランチ券など）。
    *   「予測マイスター」バッジの付与。
*   **運用ルール**:
    *   インサイダー取引の禁止規定（当事者は予測に参加できない、等）。
    *   「Bad News」を予測することへの心理的ハードルを下げる啓蒙（リスク検知こそ価値がある）。

---

## 7. 今後の拡張性 (Roadmap)

*   **LLM連携**: ニュースやSlackの会話から自動で予測市場を生成するAIエージェント。
*   **コメント機能**: なぜその予測をしたかの定性コメントを共有する掲示板。
*   **外部API連携**: Jira等のプロジェクト管理ツールと連携し、タスク完了予測を自動化。
