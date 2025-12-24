# 実装計画 (Implementation Plan)

このドキュメントは、社内予測市場システムの実装ロードマップです。
各タスクはPull Request (PR) 1つ分程度の粒度を想定しています。

## 開発プロセスとCI/CD戦略

*   **ブランチ戦略**: GitHub Flow (mainブランチからfeatureブランチを作成し、PRでマージ)
*   **CI (GitHub Actions)**:
    *   PR作成時: Lint (Ruff/ESLint), Type Check (MyPy/TypeScript), Unit Tests (Pytest/Vitest)
    *   Mainマージ時: Build Docker Image, Push to Azure Container Registry (ACR)
*   **CD (GitHub Actions)**:
    *   Dev環境: Mainマージ時に自動デプロイ (Azure Container Apps)
    *   Staging/Prod: 手動承認後デプロイ（ACRイメージ昇格）
*   **テスト戦略**:
    *   **Unit Test**: ロジック（特にLMSR計算、精算ロジック）を重点的にカバー。
    *   **Integration Test**: APIエンドポイントの正常系・異常系をDB接続ありでテスト。
    *   **E2E Test**: クリティカルパス（ログイン→マーケット閲覧→購入）を検証。

---

## Phase 1: プロジェクト初期化と基盤構築 (Foundation)

### Task 1.1: リポジトリ構成とボイラープレート作成 ✅
*   **Goal**: Frontend (Next.js) と Backend (FastAPI) の空プロジェクトを作成し、ローカルで起動できるようにする。
*   **Details**:
    *   Monorepo構成 (`/frontend`, `/backend`, `/infra`)
    *   Backend: FastAPI, Poetry, Ruff設定
    *   Frontend: Next.js 14 (App Router), TypeScript, Tailwind CSS, ESLint設定
    *   `docker-compose.yml` で両方を起動可能にする
    *   Dockerfile (Backend/Frontend) を作成し、本番ビルド可能にする
*   **Acceptance Criteria**: `docker-compose up` で "Hello World" が表示される。
*   **Status**: ✅ 完了 (PR#1)

### Task 1.2: データベース設計とマイグレーション基盤 ✅
*   **Goal**: PostgreSQLを立ち上げ、Alembicによるマイグレーション環境を整える。
*   **Details**:
    *   `docker-compose` に PostgreSQL 追加
    *   Backend: SQLAlchemy (Async) + Alembic の設定
    *   Userテーブルの初期定義（最小限）
*   **Acceptance Criteria**: マイグレーションコマンドが成功し、DBにテーブルが作成される。
*   **Status**: ✅ 完了 (PR#2)

### Task 1.2.1: Userモデルの拡張（SPEC準拠）✅
*   **Goal**: 現在のUserモデルをSPEC.mdのデータモデル設計に準拠させる。
*   **Details**:
    *   `id`: Integer → UUID に変更
    *   `department`: VARCHAR(100) 追加
    *   `balance`: DECIMAL(12,2) 追加（初期値: 1000.00）
    *   `updated_at`: TIMESTAMP 追加
    *   既存マイグレーションの修正または新規マイグレーション作成
*   **Acceptance Criteria**: Userテーブルが SPEC.md Section 4 の定義と一致する。
*   **Status**: ✅ 完了 (PR#4)

### Task 1.3: CIパイプラインの構築 ✅
*   **Goal**: PRを出した際に自動テストが走るようにする。
*   **Details**:
    *   GitHub Actions workflow (`ci.yml`) 作成
    *   Backend: `pytest`, `ruff check`, `mypy`
    *   Frontend: `npm run lint`, `npm run build`
*   **Acceptance Criteria**: 意図的にエラーを含むコードをpushしてCIが落ち、修正して通ることを確認。
*   **Status**: ✅ 完了 (PR#1)

### Task 1.4: 共通エラーハンドリング基盤 (Backend) ✅
*   **Goal**: SPEC Section 8 に定義されたエラーコードを統一的に返却する基盤を作成。
*   **Details**:
    *   `app/core/exceptions.py`: カスタム例外クラス定義
        *   `InsufficientBalanceError`, `InsufficientPositionError`, `MarketNotOpenError` 等
    *   `app/core/error_handlers.py`: FastAPI例外ハンドラー
    *   エラーレスポンススキーマ: `{ "error_code": "...", "message": "...", "details": {...} }`
*   **Acceptance Criteria**: 各エラーがSPEC定義のHTTPステータスとエラーコードで返却される。
*   **Status**: ✅ 完了 (PR#5)

---

## Phase 2: 認証とユーザー管理 (Auth & Users)

### Task 2.1: ユーザーモデルと認証基盤 (Backend) ✅
*   **Goal**: ユーザー情報を管理し、JWTによる認証ガードを作成する。
*   **Details**:
    *   Auth API (SPEC Section 5 準拠):
        *   `GET /api/v1/auth/login` - SSO認証開始（開発環境はMock対応）
        *   `GET /api/v1/auth/callback` - 認証コールバック
        *   `POST /api/v1/auth/logout` - ログアウト
        *   `GET /api/v1/auth/me` - 現在のユーザー情報取得
    *   Dependency: `get_current_user` の実装
    *   JWT トークン生成・検証ロジック
*   **Acceptance Criteria**: 保護されたAPIエンドポイントにアクセス制御がかかる。
*   **Status**: ✅ 完了 (PR#6)

### Task 2.2: 認証UIとユーザーコンテキスト (Frontend) ✅
*   **Goal**: ログイン画面と、ログイン状態の保持。
*   **Details**:
    *   Login Page
    *   Auth Context / Hook (Zustand or Context API)
    *   Layout: ヘッダーにユーザー名と所持ポイントを表示
    *   ログアウト機能
*   **Acceptance Criteria**: ログイン後、ヘッダーに自分の名前とポイント残高が表示される。
*   **Status**: ✅ 完了 (PR#7)

### Task 2.3: Microsoft Entra ID (Azure AD) 連携 ⏳
*   **Goal**: 社内SSOでログインできるようにする。
*   **Details**:
    *   Backend: MSAL (Microsoft Authentication Library) を使用したOIDCフロー実装
    *   Azure AD App Registration の設定手順書作成
    *   Frontend: Microsoft ログインボタン実装
    *   既存のMock認証との切り替え可能な設計 (環境変数 `AUTH_PROVIDER` で制御)
*   **Acceptance Criteria**: Azure ADテナントでログインできる。
*   **Recommended Timing**: Phase 7 (本番環境構築) の直前。開発中はMock認証で十分。
*   **Status**: 未着手

### Task 2.4: ロールベースアクセス制御 (RBAC) ✅
*   **Goal**: Admin / Moderator / User のロールに応じたAPI権限を実装。
*   **Details**:
    *   Backend: `RoleChecker` Dependency の実装
    *   権限マトリクス (SPEC Section 5 準拠):
        *   `User`: 取引、閲覧
        *   `Moderator`: マーケット作成・編集・公開
        *   `Admin`: マーケット解決・キャンセル、ユーザー管理
    *   Frontend: ロールに応じたUI出し分け（管理メニューの表示/非表示）
*   **Acceptance Criteria**: 一般Userが管理APIを叩くと403 `FORBIDDEN` エラーになる。
*   **Status**: ✅ 完了 (PR#8)

### Task 2.5: ユーザー管理API (Backend) ⏳
*   **Goal**: ユーザー情報の取得・更新API。
*   **Details**:
    *   API (SPEC Section 5 準拠):
        *   `GET /api/v1/users/me` - 自分のプロフィール取得
        *   `PUT /api/v1/users/me` - 自分のプロフィール更新
        *   `GET /api/v1/users/{id}` - ユーザー情報取得 (Admin)
        *   `PUT /api/v1/users/{id}/role` - ユーザーロール変更 (Admin)
*   **Acceptance Criteria**: プロフィール更新が永続化される。
*   **Recommended Timing**: Phase 5 (管理画面) の前。管理画面でユーザー管理機能を使用するため。
*   **Status**: 未着手

---

## Phase 3: マーケット管理と予測エンジン (Market Core)

### Task 3.1: カテゴリ管理 (Backend)
*   **Goal**: マーケットのカテゴリを管理できるようにする。
*   **Details**:
    *   DBモデル: `Category` (SPEC Section 4 準拠)
    *   API:
        *   `GET /api/v1/categories` - カテゴリ一覧取得
        *   `POST /api/v1/categories` - カテゴリ作成 (Admin)
    *   初期カテゴリのSeedデータ（プロダクト、営業、人事、業界動向）
*   **Acceptance Criteria**: カテゴリの作成・一覧取得ができる。
*   **Status**: ✅ 完了

### Task 3.2: LMSRロジックの実装とテスト (Backend)
*   **Goal**: 予測市場の核となる価格計算ロジックを実装する。
*   **Details**:
    *   `app/core/lmsr.py`: LMSR アルゴリズム実装 (SPEC Section 3.3 準拠)
        *   コスト関数: `C(q) = b * ln(Σ e^(q_i/b))`
        *   価格（確率）計算: `p_i = e^(q_i/b) / Σ e^(q_j/b)`
        *   取引コスト計算: `cost = C(q_new) - C(q_old)`
    *   価格境界チェック: 0.1% ≤ probability ≤ 99.9%
    *   **重点テスト**:
        *   数値計算の精度（浮動小数点誤差対策）
        *   境界値テスト（極端な数量での挙動）
        *   Binary/Categorical両対応の確認
*   **Acceptance Criteria**: PytestでLMSRの計算結果が正しいことを検証済み。
*   **Status**: 未着手

### Task 3.3: マーケット・アウトカムモデル (Backend)
*   **Goal**: マーケットとアウトカムのデータモデルを作成。
*   **Details**:
    *   DBモデル (SPEC Section 4 準拠):
        *   `Market`: 全フィールド実装（status, visibility, liquidity_param, start_at, end_at 等）
        *   `Outcome`: quantity（LMSR状態）を含む
    *   Alembicマイグレーション作成
    *   ENUM型の定義: `MarketType`, `MarketStatus`, `Visibility`
*   **Acceptance Criteria**: マイグレーションが成功し、全カラムが作成される。
*   **Status**: 未着手

### Task 3.4: マーケット管理API (Backend)
*   **Goal**: マーケットのCRUD操作。
*   **Details**:
    *   API (SPEC Section 5 準拠):
        *   `GET /api/v1/markets` - 一覧取得（フィルタ: category, status, visibility）
        *   `POST /api/v1/markets` - 作成 (Moderator)
        *   `GET /api/v1/markets/{id}` - 詳細・現在価格取得
        *   `PUT /api/v1/markets/{id}` - 更新 (Moderator)
        *   `DELETE /api/v1/markets/{id}` - 削除（DRAFTのみ、Moderator）
        *   `POST /api/v1/markets/{id}/publish` - 公開 (Moderator)
    *   Binaryマーケット作成時、YES/NO アウトカムを自動生成
    *   Seedデータ投入スクリプト
*   **Acceptance Criteria**: API経由でマーケットを作成し、カテゴリでフィルタして取得できる。
*   **Status**: 未着手

### Task 3.5: マーケットライフサイクル管理 (Backend)
*   **Goal**: マーケットの状態遷移を管理する（SPEC Section 3.5 準拠）。
*   **Details**:
    *   状態遷移ロジック: `DRAFT → OPEN → CLOSED → RESOLVED / CANCELLED`
    *   バリデーション: 不正な状態遷移を防止
    *   自動状態遷移（バックグラウンドタスク または API呼び出し時チェック）:
        *   `start_at` 到達で `DRAFT → OPEN`
        *   `end_at` 到達で `OPEN → CLOSED`
    *   状態に応じた取引可否チェック
*   **Acceptance Criteria**: 終了日時を過ぎたマーケットで取引しようとすると `MARKET_NOT_OPEN` エラー。
*   **Status**: 未着手

### Task 3.6: マーケット一覧・詳細UI (Frontend)
*   **Goal**: ユーザーがマーケットを探し、詳細を見れるようにする。
*   **Details**:
    *   Market List Component (Card UI): タイトル、確率、トレンド表示
    *   フィルター・ソート機能（カテゴリ、ステータス）
    *   Market Detail Page: タイトル、説明、判定基準、現在の確率表示
    *   ステータスバッジ表示（OPEN/CLOSED/RESOLVED）
*   **Acceptance Criteria**: DBにあるマーケットが表示され、クリックして詳細へ遷移できる。
*   **Status**: 未着手

---

## Phase 4: 取引機能 (Trading)

### Task 4.1: ポジション・トランザクションモデル (Backend)
*   **Goal**: 取引に必要なデータモデルを作成。
*   **Details**:
    *   DBモデル (SPEC Section 4 準拠):
        *   `Position`: user_id, market_id, outcome_id, quantity, total_cost
        *   `Transaction`: type (buy/sell/payout/refund), quantity, cost, balance_after
    *   Alembicマイグレーション作成
    *   ENUM型: `TransactionType`
*   **Acceptance Criteria**: マイグレーションが成功する。
*   **Status**: 未着手

### Task 4.2: 取引見積もりAPI (Backend)
*   **Goal**: 取引前にコストを確認できるようにする。
*   **Details**:
    *   API: `GET /api/v1/markets/{id}/estimate`
        *   Query: `outcome_id`, `action` (buy/sell), `quantity`
        *   Response: `{ "cost": 12.34, "new_probability": 0.65, "potential_payout": 10.0 }`
    *   LMSRロジックを使用したコスト計算
    *   残高・ポジション検証（エラーは返さず、`executable: false` で返却）
*   **Acceptance Criteria**: 見積もりAPIでコストと予想確率が正しく返却される。
*   **Status**: 未着手

### Task 4.3: 取引実行API (Backend)
*   **Goal**: 注文を受け付け、残高とポジションを更新する。
*   **Details**:
    *   API: `POST /api/v1/markets/{id}/trade`
        *   Body: `{ "outcome_id": "...", "action": "buy", "quantity": 10 }`
    *   **DBトランザクション内で原子的に実行**:
        1. マーケット状態チェック（OPEN以外は `MARKET_NOT_OPEN`）
        2. 残高/ポジションチェック（不足時は `INSUFFICIENT_BALANCE` / `INSUFFICIENT_POSITION`）
        3. LMSRでコスト計算
        4. User.balance 更新
        5. Position 更新（なければ作成）
        6. Outcome.quantity 更新
        7. Transaction レコード作成
    *   楽観的ロック または SELECT FOR UPDATE で競合防止
*   **Acceptance Criteria**: 注文APIを叩くと、残高が減り、Positionが増え、価格が変わる。
*   **Status**: 未着手

### Task 4.4: 取引UIの実装 (Frontend)
*   **Goal**: ユーザーが画面から売買できるようにする。
*   **Details**:
    *   Trade Form: Buy/Sell切り替え、数量入力スライダー
    *   見積もり表示: 入力数量に応じたコストと予想ペイアウトのリアルタイム計算
    *   購入/売却実行と完了トースト通知
    *   エラーハンドリング: 残高不足、ポジション不足時のUI表示
    *   確認ダイアログ（大きな取引時）
*   **Acceptance Criteria**: 画面から購入・売却操作ができ、ヘッダーのポイント残高が即座に更新される。
*   **Status**: 未着手

### Task 4.5: ポートフォリオ表示 (Frontend/Backend)
*   **Goal**: 自分の持ち株を確認できる。
*   **Details**:
    *   API:
        *   `GET /api/v1/users/me/positions` - ポジション一覧
        *   `GET /api/v1/users/me/transactions` - 取引履歴
    *   UI: マイページに保有ポジション一覧と時価評価額を表示
    *   損益計算: `(current_probability - average_cost) * quantity`
*   **Acceptance Criteria**: 購入したポジションが一覧に表示され、損益が計算される。
*   **Status**: 未着手

---

## Phase 5: 解決と精算 (Resolution)

### Task 5.1: 結果入力と精算ロジック (Backend)
*   **Goal**: マーケットを終了し、正解者にポイントを配る。
*   **Details**:
    *   API:
        *   `POST /api/v1/markets/{id}/resolve` (Admin)
            *   Body: `{ "outcome_id": "winning_outcome_uuid" }`
        *   `POST /api/v1/markets/{id}/cancel` (Admin)
    *   **Resolve処理** (DBトランザクション内):
        1. Market.status を `RESOLVED` に更新
        2. Market.resolved_outcome_id, resolved_at を設定
        3. 勝者Positionに対し、1シェア=1ポイントで User.balance に加算
        4. Transaction (type=payout) レコード作成
    *   **Cancel処理**:
        1. Market.status を `CANCELLED` に更新
        2. 全Positionの total_cost を User.balance に返金
        3. Transaction (type=refund) レコード作成
*   **Acceptance Criteria**: 解決APIを実行すると、勝者の残高が増える。キャンセル時は全額返金。
*   **Status**: 未着手

### Task 5.2: 管理画面 (Frontend)
*   **Goal**: 管理者がマーケットを作成・解決できるUI。
*   **Details**:
    *   Admin Dashboard: 管理対象マーケット一覧
    *   Create Market Form: タイプ選択、カテゴリ、日時設定
    *   Resolve Market Modal: 正解アウトカム選択、確認ダイアログ
    *   Cancel Market Modal: キャンセル理由入力
    *   ロールに応じたアクセス制御
*   **Acceptance Criteria**: 管理者ユーザーでログインし、マーケットを作成・解決できる。
*   **Status**: 未着手

---

## Phase 6: ダッシュボードとUI改善 (Polish)

### Task 6.1: 価格履歴保存と取得 (Backend)
*   **Goal**: 価格推移をグラフ表示するためのデータ基盤。
*   **Details**:
    *   DBモデル: `PriceHistory` (SPEC Section 4 準拠)
    *   取引成立時に自動記録（全アウトカムの確率をスナップショット）
    *   API: `GET /api/v1/markets/{id}/history`
        *   Query: `from`, `to`, `interval` (1h/1d)
    *   古いデータの集約・削除ポリシー
*   **Acceptance Criteria**: 取引後に価格履歴が記録され、APIで取得できる。
*   **Status**: 未着手

### Task 6.2: チャート実装 (Frontend)
*   **Goal**: 価格推移をグラフで見る。
*   **Details**:
    *   Recharts を使ってラインチャート描画
    *   時間範囲選択（1日/1週間/全期間）
    *   ツールチップで詳細表示
    *   複数アウトカムの確率を色分け表示
*   **Acceptance Criteria**: マーケット詳細画面に確率の推移グラフが表示される。
*   **Status**: 未着手

### Task 6.3: ランキングと統計 (Backend/Frontend)
*   **Goal**: ゲーミフィケーション要素。
*   **Details**:
    *   API:
        *   `GET /api/v1/leaderboard` - ランキング取得（ポイント残高順）
        *   `GET /api/v1/stats/summary` - システム統計 (Admin)
    *   UI: ランキングページ（個人ランキング、部署別ランキング）
    *   統計表示: 総取引数、アクティブマーケット数、参加者数
*   **Acceptance Criteria**: ポイント保有量順にユーザーが表示される。
*   **Status**: 未着手

### Task 6.4: E2Eテストの導入
*   **Goal**: 品質の担保。
*   **Details**:
    *   Playwright セットアップ
    *   シナリオ:
        1. ログイン
        2. マーケット作成 (Moderator)
        3. 購入 (User)
        4. 解決 (Admin)
        5. 残高確認
*   **Acceptance Criteria**: CIでE2Eテストがパスする。
*   **Status**: 未着手

### Task 6.5: リアルタイム価格更新 (WebSocket)
*   **Goal**: 他ユーザーの取引による価格変動を即座に反映する。
*   **Details**:
    *   Backend: FastAPI WebSocket エンドポイント (`/ws/markets/{id}`)
    *   取引成立時に価格変動をブロードキャスト
    *   Frontend: WebSocket接続とリアルタイムUI更新
    *   接続管理: 認証、再接続ロジック
*   **Acceptance Criteria**: 別タブで取引すると、もう一方のタブの価格表示が自動更新される。
*   **Status**: 未着手

### Task 6.6: モバイル対応・レスポンシブUI
*   **Goal**: スマートフォンからも快適に利用できるようにする。
*   **Details**:
    *   Tailwind CSS breakpoints を活用したレスポンシブ設計
    *   モバイル用ナビゲーション（ハンバーガーメニュー）
    *   タッチ操作に最適化したスライダー・ボタンサイズ
*   **Acceptance Criteria**: iPhone/Android実機で主要操作が問題なく行える。
*   **Status**: 未着手

---

## Phase 7: Azure本番環境構築 (Production Deployment)

### Task 7.1: Azureインフラ構築 (IaC)
*   **Goal**: 本番環境のAzureリソースをコードで管理する。
*   **Details**:
    *   Bicep または Terraform でインフラ定義
    *   リソース (SPEC Section 2.1 準拠):
        *   Azure Container Apps
        *   Azure Database for PostgreSQL (Flexible Server)
        *   Azure Cache for Redis
        *   Azure Container Registry
    *   環境分離: Dev / Staging / Prod
    *   ネットワーク: VNet, Private Endpoint
*   **Acceptance Criteria**: `az deployment` または `terraform apply` で環境が構築される。
*   **Status**: 未着手

### Task 7.2: CI/CDパイプライン完成
*   **Goal**: Main マージで自動デプロイされるようにする。
*   **Details**:
    *   GitHub Actions: Build -> Push to ACR -> Deploy to Azure Container Apps
    *   Secret管理: Azure Key Vault 連携
    *   Health Check エンドポイント (`/health`) の活用
    *   Blue-Green または Rolling デプロイ戦略
*   **Acceptance Criteria**: PRマージ後、数分以内にDev環境に反映される。
*   **Status**: 未着手

### Task 7.3: 監視・ログ・アラート設定
*   **Goal**: 本番運用に必要な可観測性を確保する（SPEC Section 7 準拠）。
*   **Details**:
    *   Azure Application Insights の導入
    *   構造化ログ出力 (JSON)
    *   アラート設定:
        *   エラーレート上昇（5xx > 1%）
        *   レスポンス遅延（P95 > 500ms）
        *   コンテナ異常終了
    *   ダッシュボード作成
*   **Acceptance Criteria**: Application Insights でリクエストトレースが確認できる。
*   **Status**: 未着手

### Task 7.4: セキュリティ設定
*   **Goal**: 本番環境のセキュリティを確保する（SPEC Section 7.3 準拠）。
*   **Details**:
    *   HTTPS強制（TLS 1.3）
    *   CORS設定の本番用調整
    *   Rate Limiting の導入
    *   監査ログの有効化（全取引・管理操作）
    *   脆弱性スキャン（Trivy等）のCI組み込み
*   **Acceptance Criteria**: セキュリティチェックリストを全て満たす。
*   **Status**: 未着手

---

## Phase 8: 拡張機能 (Future Enhancements)

### Task 8.1: Categorical / Scalar マーケット対応
*   **Goal**: Binary (YES/NO) 以外のマーケットタイプをサポートする。
*   **Details**:
    *   Categorical: 3つ以上の選択肢（例: 次期CEO候補 A/B/C）
    *   Scalar: 数値範囲をバケット化（例: 売上 10億未満 / 10-12億 / 12億以上）
    *   LMSRロジックの多選択肢対応（既に設計済み）
    *   UI: 選択肢が増えた場合のカード・取引画面デザイン
*   **Acceptance Criteria**: 3選択肢のマーケットで取引ができる。
*   **Status**: 未着手

### Task 8.2: 通知機能 (Slack / Email)
*   **Goal**: 重要イベントをユーザーに通知する。
*   **Details**:
    *   新規マーケット公開通知
    *   フォロー中マーケットの締切リマインダー
    *   解決結果の通知
    *   Slack Webhook / SendGrid 連携
*   **Acceptance Criteria**: マーケット解決時にSlackに通知が飛ぶ。
*   **Status**: 未着手

### Task 8.3: コメント・ディスカッション機能
*   **Goal**: 予測の根拠を共有できるようにする。
*   **Details**:
    *   マーケットごとのコメントスレッド
    *   Markdown対応
    *   @メンション機能（将来）
*   **Acceptance Criteria**: マーケット詳細画面でコメントの投稿・表示ができる。
*   **Status**: 未着手

### Task 8.4: 個人成績・Brier Score
*   **Goal**: ユーザーの予測精度を可視化する（SPEC Section 3.7 準拠）。
*   **Details**:
    *   Brier Score 計算ロジック実装
    *   的中率、ROI の計算
    *   プロフィールページに成績表示
*   **Acceptance Criteria**: ユーザープロフィールに予測成績が表示される。
*   **Status**: 未着手

---

## 凡例

| ステータス | 意味 |
|-----------|------|
| ✅ | 完了 |
| 🔧 | 要修正（既存実装がSPECと乖離） |
| 🚧 | 進行中 |
| ⏳ | 後回し（Recommended Timing参照） |
| 未着手 | 未着手 |
