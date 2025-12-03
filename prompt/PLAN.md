# 実装計画 (Implementation Plan)

このドキュメントは、社内予測市場システムの実装ロードマップです。
各タスクはPull Request (PR) 1つ分程度の粒度を想定しています。

## 開発プロセスとCI/CD戦略

*   **ブランチ戦略**: GitHub Flow (mainブランチからfeatureブランチを作成し、PRでマージ)
*   **CI (GitHub Actions)**:
    *   PR作成時: Lint (Ruff/ESLint), Type Check (MyPy/TypeScript), Unit Tests (Pytest/Vitest)
    *   Mainマージ時: Build Docker Image, Push to Amazon ECR
*   **CD (GitHub Actions)**:
    *   Dev環境: Mainマージ時に自動デプロイ (AWS App Runner または ECS/Fargate)
    *   Staging/Prod: 手動承認後デプロイ（ECRイメージ昇格）
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
    *   Frontend: Next.js (App Router), TypeScript, Tailwind CSS, ESLint/Prettier設定
    *   `docker-compose.yml` で両方を起動可能にする
    *   Dockerfile (Backend/Frontend) を作成し、本番ビルド可能にする
*   **Acceptance Criteria**: `docker-compose up` で "Hello World" が表示される。
*   **Status**: ✅ 完了 (PR#1)

### Task 1.2: データベース設計とマイグレーション基盤
*   **Goal**: PostgreSQLを立ち上げ、Alembicによるマイグレーション環境を整える。
*   **Details**:
    *   `docker-compose` に PostgreSQL 追加
    *   Backend: SQLAlchemy (Async) + Alembic の設定
    *   Userテーブルの初期定義（最小限）
*   **Acceptance Criteria**: マイグレーションコマンドが成功し、DBにテーブルが作成される。
*   **Status**: ✅ 完了 (branch: feature/task-1.2-db-setup, Alembic初期マイグレーションでusersテーブル作成、docker-composeにPostgreSQL追加)

### Task 1.3: CIパイプラインの構築 ✅
*   **Goal**: PRを出した際に自動テストが走るようにする。
*   **Details**:
    *   GitHub Actions workflow (`ci.yml`) 作成
    *   Backend: `pytest`, `ruff check`
    *   Frontend: `npm run lint`, `npm run build`
*   **Acceptance Criteria**: 意図的にエラーを含むコードをpushしてCIが落ち、修正して通ることを確認。
*   **Status**: ✅ 完了 (PR#1)

---

## Phase 2: 認証とユーザー管理 (Auth & Users)

### Task 2.1: ユーザーモデルと認証基盤 (Backend)
*   **Goal**: ユーザー情報を管理し、JWTによる認証ガードを作成する。
*   **Details**:
    *   DBモデル: `User` (id, email, name, role, balance)
    *   Auth API: `POST /auth/login` (今回はMockログインまたは簡易的なPassword認証で実装し、Azure ADは後回しでも可。ただしInterfaceは整える)
    *   Dependency: `get_current_user` の実装
*   **Acceptance Criteria**: 保護されたAPIエンドポイントにアクセス制御がかかる。

### Task 2.2: 認証UIとユーザーコンテキスト (Frontend)
*   **Goal**: ログイン画面と、ログイン状態の保持。
*   **Details**:
    *   Login Page
    *   Auth Context / Hook (Zustand or Context API)
    *   Layout: ヘッダーにユーザー名と所持ポイントを表示
*   **Acceptance Criteria**: ログイン後、ヘッダーに自分の名前が表示される。

### Task 2.3: IDプロバイダー連携 (Cognito/社内IdP)
*   **Goal**: 社内SSOでログインできるようにする。
*   **Details**:
    *   Backend: Cognito Hosted UI または社内IdP (OIDC/SAML) のフロー実装
    *   Cognito User Pool / App Client の設定手順書作成
    *   Frontend: Cognito/IdP向けのログインボタン実装
    *   既存のMock認証との切り替え可能な設計 (環境変数で制御)
*   **Acceptance Criteria**: Cognitoまたは社内IdPのテナントでログインできる。

### Task 2.4: ロールベースアクセス制御 (RBAC)
*   **Goal**: Admin / Moderator / User のロールに応じたAPI権限を実装。
*   **Details**:
    *   Backend: `RoleChecker` Dependency の実装
    *   マーケット作成は Moderator以上、解決は Admin のみ等
    *   Frontend: ロールに応じたUI出し分け（管理メニューの表示/非表示）
*   **Acceptance Criteria**: 一般Userが管理APIを叩くと403エラーになる。

---

## Phase 3: マーケット管理と予測エンジン (Market Core)

### Task 3.1: LMSRロジックの実装とテスト (Backend)
*   **Goal**: 予測市場の核となる価格計算ロジックを実装する。
*   **Details**:
    *   `lmsr.py`: コスト関数 $C(q) = b \cdot \ln(\sum e^{q_i/b})$ の実装
    *   現在の数量から価格（確率）を算出する関数の実装
    *   **重点テスト**: 数値計算の精度、境界値テスト
*   **Acceptance Criteria**: PytestでLMSRの計算結果が正しいことを検証済み。

### Task 3.2: マーケット管理API (Backend)
*   **Goal**: マーケットの作成・一覧取得・詳細取得。
*   **Details**:
    *   DBモデル: `Market`, `Outcome`, `Category`
    *   API: `GET /markets`, `POST /markets`, `GET /markets/{id}`
    *   フィルタリング: カテゴリ、ステータス、公開範囲
    *   公開範囲制御: `visibility` (public / department / invited)
    *   Seedデータ投入スクリプト
*   **Acceptance Criteria**: API経由でマーケットを作成し、カテゴリでフィルタして取得できる。

### Task 3.3: マーケット一覧・詳細UI (Frontend)
*   **Goal**: ユーザーがマーケットを探し、詳細を見れるようにする。
*   **Details**:
    *   Market List Component (Card UI)
    *   Market Detail Page: タイトル、説明、現在の確率表示
*   **Acceptance Criteria**: DBにあるマーケットが表示され、クリックして詳細へ遷移できる。

---

## Phase 4: 取引機能 (Trading)

### Task 4.1: 取引データモデルとAPI (Backend)
*   **Goal**: 注文を受け付け、残高とポジションを更新する。
*   **Details**:
    *   DBモデル: `Wallet` (Userに統合も可), `Position`, `Transaction`
    *   API: `POST /markets/{id}/trade`
    *   **Transaction**: DBトランザクションを用いて、ポイント減算・ポジション加算・価格更新を原子的に実行する。
*   **Acceptance Criteria**: 注文APIを叩くと、Wallet残高が減り、Positionが増え、Marketの価格が変わる。

### Task 4.2: 取引UIの実装 (Frontend)
*   **Goal**: ユーザーが画面から売買できるようにする。
*   **Details**:
    *   Trade Form: Buy/Sell切り替え、数量入力スライダー
    *   見積もりAPI: `GET /markets/{id}/estimate?action=buy&outcome=yes&amount=10`
    *   見積もり表示: 入力数量に応じたコストと予想ペイアウトのリアルタイム計算
    *   購入/売却実行と完了トースト通知
    *   エラーハンドリング: 残高不足、ポジション不足時のUI表示
*   **Acceptance Criteria**: 画面から購入・売却操作ができ、ヘッダーのポイント残高が即座に更新される。

### Task 4.3: ポートフォリオ表示 (Frontend/Backend)
*   **Goal**: 自分の持ち株を確認できる。
*   **Details**:
    *   API: `GET /users/me/positions`
    *   UI: マイページまたはダッシュボードに保有ポジション一覧を表示
*   **Acceptance Criteria**: 購入したポジションが一覧に表示される。

---

## Phase 5: 解決と精算 (Resolution)

### Task 5.1: 結果入力と精算ロジック (Backend)
*   **Goal**: マーケットを終了し、正解者にポイントを配る。
*   **Details**:
    *   API: `POST /markets/{id}/resolve` (Admin only)
    *   Logic: 正解Outcomeを持つPositionに対し、1シェア=1ポイントでWalletに加算。不正解は0。
    *   Status更新: Marketを `RESOLVED` に。
*   **Acceptance Criteria**: 解決APIを実行すると、勝者の残高が増える。

### Task 5.2: 管理画面 (Frontend)
*   **Goal**: 管理者がマーケットを作成・解決できるUI。
*   **Details**:
    *   Admin Dashboard
    *   Create Market Form
    *   Resolve Market Modal
*   **Acceptance Criteria**: 管理者ユーザーでログインし、マーケットを解決できる。

---

## Phase 6: ダッシュボードとUI改善 (Polish)

### Task 6.1: チャート実装 (Frontend)
*   **Goal**: 価格推移をグラフで見る。
*   **Details**:
    *   Backend: 価格履歴を保存・取得する仕組み (Transaction履歴から集計も可)
    *   Frontend: Recharts 等を使ってラインチャート描画
*   **Acceptance Criteria**: マーケット詳細画面に確率の推移グラフが表示される。

### Task 6.2: ランキングと統計 (Backend/Frontend)
*   **Goal**: ゲーミフィケーション要素。
*   **Details**:
    *   API: `GET /leaderboard`
    *   UI: ランキングページ
*   **Acceptance Criteria**: ポイント保有量順にユーザーが表示される。

### Task 6.3: E2Eテストの導入
*   **Goal**: 品質の担保。
*   **Details**:
    *   Playwright セットアップ
    *   シナリオ: ログイン -> マーケット作成(Admin) -> 購入(User) -> 解決(Admin) -> 残高確認
*   **Acceptance Criteria**: CIでE2Eテストがパスする。

### Task 6.4: リアルタイム価格更新 (WebSocket)
*   **Goal**: 他ユーザーの取引による価格変動を即座に反映する。
*   **Details**:
    *   Backend: FastAPI WebSocket エンドポイント (`/ws/markets/{id}`)
    *   取引成立時に価格変動をブロードキャスト
    *   Frontend: WebSocket接続とリアルタイムUI更新
    *   Azure: Azure Web PubSub または SignalR Service の検討
*   **Acceptance Criteria**: 別タブで取引すると、もう一方のタブの価格表示が自動更新される。

### Task 6.5: モバイル対応・レスポンシブUI
*   **Goal**: スマートフォンからも快適に利用できるようにする。
*   **Details**:
    *   Tailwind CSS breakpoints を活用したレスポンシブ設計
    *   モバイル用ナビゲーション（ハンバーガーメニュー）
    *   タッチ操作に最適化したスライダー・ボタンサイズ
*   **Acceptance Criteria**: iPhone/Android実機で主要操作が問題なく行える。

---

## Phase 7: Azure本番環境構築 (Production Deployment)

### Task 7.1: Azureインフラ構築 (IaC)
*   **Goal**: 本番環境のAzureリソースをコードで管理する。
*   **Details**:
    *   Bicep または Terraform でインフラ定義
    *   リソース: Azure Container Apps, Azure Database for PostgreSQL, Azure Cache for Redis, Azure Container Registry
    *   環境分離: Dev / Staging / Prod
*   **Acceptance Criteria**: `az deployment` または `terraform apply` で環境が構築される。

### Task 7.2: CI/CDパイプライン完成
*   **Goal**: Main マージで自動デプロイされるようにする。
*   **Details**:
    *   GitHub Actions: Build -> Push to ACR -> Deploy to Azure Container Apps
    *   Secret管理: Azure Key Vault 連携
    *   Health Check エンドポイントの実装
*   **Acceptance Criteria**: PRマージ後、数分以内にDev環境に反映される。

### Task 7.3: 監視・ログ・アラート設定
*   **Goal**: 本番運用に必要な可観測性を確保する。
*   **Details**:
    *   Azure Application Insights の導入
    *   構造化ログ出力 (JSON)
    *   アラート: エラーレート上昇、レスポンス遅延
*   **Acceptance Criteria**: Application Insights でリクエストトレースが確認できる。

---

## Phase 8: 拡張機能 (Future Enhancements)

### Task 8.1: Categorical / Scalar マーケット対応
*   **Goal**: Binary (YES/NO) 以外のマーケットタイプをサポートする。
*   **Details**:
    *   Categorical: 3つ以上の選択肢（例: 次期CEO候補 A/B/C）
    *   Scalar: 数値範囲をバケット化（例: 売上 10億未満 / 10-12億 / 12億以上）
    *   LMSRロジックの多選択肢対応
    *   UI: 選択肢が増えた場合のカード・取引画面デザイン
*   **Acceptance Criteria**: 3選択肢のマーケットで取引ができる。

### Task 8.2: 通知機能 (Slack / Email)
*   **Goal**: 重要イベントをユーザーに通知する。
*   **Details**:
    *   新規マーケット公開通知
    *   フォロー中マーケットの締切リマインダー
    *   解決結果の通知
    *   Slack Webhook / SendGrid 連携
*   **Acceptance Criteria**: マーケット解決時にSlackに通知が飛ぶ。

### Task 8.3: コメント・ディスカッション機能
*   **Goal**: 予測の根拠を共有できるようにする。
*   **Details**:
    *   マーケットごとのコメントスレッド
    *   Markdown対応
    *   @メンション機能（将来）
*   **Acceptance Criteria**: マーケット詳細画面でコメントの投稿・表示ができる。
