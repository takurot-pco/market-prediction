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

### 2.1. 技術スタック (Azure Base)
*   **Infrastructure**: Azure Container Apps（コンテナ実行基盤）
*   **Frontend**: Next.js 14 (App Router) + TypeScript + Tailwind CSS
*   **Backend**: Python 3.11+ (FastAPI) - 非同期処理対応
    *   *数値計算ライブラリが豊富なPythonが予測エンジンには有利*
*   **Database**: Azure Database for PostgreSQL (Flexible Server)
*   **Cache**: Azure Cache for Redis（セッション管理、リアルタイム更新）
*   **Container Registry**: Azure Container Registry (ACR)
*   **Auth**: Microsoft Entra ID (Azure AD) によるSSO認証
*   **Monitoring**: Azure Application Insights

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
*   **LMSRアルゴリズム詳細**:
    *   コスト関数: `C(q) = b * ln(Σ e^(q_i/b))`
        *   `q_i`: 各アウトカムの現在数量
        *   `b`: 流動性パラメータ（大きいほど価格変動が緩やか）
    *   価格（確率）計算: `p_i = e^(q_i/b) / Σ e^(q_j/b)`
    *   取引コスト: `Cost = C(q_new) - C(q_old)`
    *   推奨 `b` 値: 100〜1000（取引量に応じて調整）
*   **注文処理**:
    *   Buy (Long): 特定の結果のシェアを購入。
    *   Sell (Short): 保有シェアを売却（保有数量が上限）。
*   **コスト計算**: 現在の価格に基づき、必要ポイントを即時算出。
*   **取引制限**:
    *   最小取引単位: 1シェア
    *   最大取引単位: 残高または保有数量による制限
    *   価格境界: 確率0.1%〜99.9%（極端な価格を防止）

### 3.4. ウォレット・ポイント管理
*   **仮想通貨**: 社内通貨（例: "Prediction Point"）。
*   **初期配布**: 新規登録時、四半期ごとに一定額を付与。
*   **ポートフォリオ**: 保有中のポジション一覧と時価評価額。
*   **ランキング**: 獲得ポイント数によるリーダーボード（個人・部署対抗）。

### 3.5. マーケットライフサイクル (Market Lifecycle)
*   **状態遷移**:
    ```
    DRAFT → OPEN → CLOSED → RESOLVED
              ↓
           CANCELLED
    ```
    *   `DRAFT`: 作成中（Moderator/Adminのみ閲覧可）
    *   `OPEN`: 取引可能（開始日時〜終了日時）
    *   `CLOSED`: 取引終了、結果待ち
    *   `RESOLVED`: 結果確定、精算完了
    *   `CANCELLED`: キャンセル（全額返金）
*   **自動状態遷移**:
    *   開始日時到達で `DRAFT` → `OPEN`
    *   終了日時到達で `OPEN` → `CLOSED`

### 3.6. 解決・精算 (Resolution & Settlement)
*   **結果入力**: モデレーターが事実に基づき結果（YES/NO等）を確定。
*   **ペイアウト**:
    *   正解のシェア: 1シェアあたり1ポイント（または100ポイント）で償還。
    *   不正解のシェア: 価値0になる。
*   **異議申し立て**: 結果確定前のレビュー期間（オプション、24〜72時間）。
*   **キャンセル時処理**: 全ポジションを購入時コストで返金。

### 3.7. ダッシュボード・分析
*   **トレンドグラフ**: 予測確率の時系列推移（「プロジェクトXの成功確率が急落している」等の検知）。
*   **ヒートマップ**: 注目度の高い（取引量の多い）マーケットの可視化。
*   **個人成績**: 自分の予測精度、Brier Score（予測スコア）の表示。

### 3.8. UI/UX・デザイン (UI/UX Design)
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

## 4. データモデル設計 (Data Model)

### Users
| カラム | 型 | 説明 |
|--------|-----|------|
| `id` | UUID | 主キー |
| `email` | VARCHAR(320) | メールアドレス（UNIQUE） |
| `name` | VARCHAR(100) | 表示名 |
| `role` | ENUM | `admin`, `moderator`, `user` |
| `department` | VARCHAR(100) | 部署名 |
| `balance` | DECIMAL(12,2) | 利用可能ポイント残高 |
| `created_at` | TIMESTAMP | 作成日時 |
| `updated_at` | TIMESTAMP | 更新日時 |

### Categories
| カラム | 型 | 説明 |
|--------|-----|------|
| `id` | UUID | 主キー |
| `name` | VARCHAR(50) | カテゴリ名 |
| `description` | TEXT | 説明 |
| `sort_order` | INT | 表示順 |

### Markets
| カラム | 型 | 説明 |
|--------|-----|------|
| `id` | UUID | 主キー |
| `title` | VARCHAR(200) | 質問タイトル |
| `description` | TEXT | 詳細説明・判定基準 |
| `category_id` | UUID | カテゴリFK |
| `market_type` | ENUM | `binary`, `categorical`, `scalar` |
| `status` | ENUM | `draft`, `open`, `closed`, `resolved`, `cancelled` |
| `visibility` | ENUM | `public`, `department`, `invited` |
| `liquidity_param` | DECIMAL | LMSR流動性パラメータ (b) |
| `start_at` | TIMESTAMP | 取引開始日時 |
| `end_at` | TIMESTAMP | 取引終了日時 |
| `resolution_date` | DATE | 判定予定日 |
| `resolved_at` | TIMESTAMP | 実際の解決日時 |
| `resolved_outcome_id` | UUID | 正解アウトカムFK |
| `created_by` | UUID | 作成者FK |
| `created_at` | TIMESTAMP | 作成日時 |
| `updated_at` | TIMESTAMP | 更新日時 |

### Outcomes (選択肢)
| カラム | 型 | 説明 |
|--------|-----|------|
| `id` | UUID | 主キー |
| `market_id` | UUID | マーケットFK |
| `label` | VARCHAR(100) | ラベル (YES/NO, Option A...) |
| `quantity` | DECIMAL(12,2) | LMSR現在数量 |
| `sort_order` | INT | 表示順 |

### Positions (保有状況)
| カラム | 型 | 説明 |
|--------|-----|------|
| `id` | UUID | 主キー |
| `user_id` | UUID | ユーザーFK |
| `market_id` | UUID | マーケットFK |
| `outcome_id` | UUID | アウトカムFK |
| `quantity` | DECIMAL(12,2) | 保有シェア数 |
| `total_cost` | DECIMAL(12,2) | 累計購入コスト |
| `created_at` | TIMESTAMP | 作成日時 |
| `updated_at` | TIMESTAMP | 更新日時 |

### Transactions (取引履歴)
| カラム | 型 | 説明 |
|--------|-----|------|
| `id` | UUID | 主キー |
| `user_id` | UUID | ユーザーFK |
| `market_id` | UUID | マーケットFK |
| `outcome_id` | UUID | アウトカムFK |
| `type` | ENUM | `buy`, `sell`, `payout`, `refund` |
| `quantity` | DECIMAL(12,2) | 取引数量 |
| `cost` | DECIMAL(12,2) | 取引コスト（負の値は返却） |
| `balance_after` | DECIMAL(12,2) | 取引後残高 |
| `created_at` | TIMESTAMP | 取引日時 |

### PriceHistory (価格履歴)
| カラム | 型 | 説明 |
|--------|-----|------|
| `id` | UUID | 主キー |
| `market_id` | UUID | マーケットFK |
| `outcome_id` | UUID | アウトカムFK |
| `probability` | DECIMAL(5,4) | 確率 (0.0001〜0.9999) |
| `recorded_at` | TIMESTAMP | 記録日時 |

---

## 5. API設計 (API Design)

### 認証 (Authentication)
| Method | Endpoint | 説明 | 権限 |
|--------|----------|------|------|
| `GET` | `/api/v1/auth/login` | SSO認証開始（リダイレクト） | Public |
| `GET` | `/api/v1/auth/callback` | SSO認証コールバック | Public |
| `POST` | `/api/v1/auth/logout` | ログアウト | User |
| `GET` | `/api/v1/auth/me` | 現在のユーザー情報取得 | User |

### ユーザー (Users)
| Method | Endpoint | 説明 | 権限 |
|--------|----------|------|------|
| `GET` | `/api/v1/users/me` | 自分のプロフィール取得 | User |
| `PUT` | `/api/v1/users/me` | 自分のプロフィール更新 | User |
| `GET` | `/api/v1/users/me/positions` | 自分のポジション一覧 | User |
| `GET` | `/api/v1/users/me/transactions` | 自分の取引履歴 | User |
| `GET` | `/api/v1/users/{id}` | ユーザー情報取得 | Admin |
| `PUT` | `/api/v1/users/{id}/role` | ユーザーロール変更 | Admin |

### マーケット (Markets)
| Method | Endpoint | 説明 | 権限 |
|--------|----------|------|------|
| `GET` | `/api/v1/markets` | マーケット一覧取得 | User |
| `POST` | `/api/v1/markets` | マーケット作成 | Moderator |
| `GET` | `/api/v1/markets/{id}` | マーケット詳細・現在価格取得 | User |
| `PUT` | `/api/v1/markets/{id}` | マーケット情報更新 | Moderator |
| `DELETE` | `/api/v1/markets/{id}` | マーケット削除（DRAFT状態のみ） | Moderator |
| `POST` | `/api/v1/markets/{id}/publish` | マーケット公開 | Moderator |
| `POST` | `/api/v1/markets/{id}/resolve` | マーケット解決 | Admin |
| `POST` | `/api/v1/markets/{id}/cancel` | マーケットキャンセル | Admin |
| `GET` | `/api/v1/markets/{id}/history` | 価格履歴取得 | User |

### 取引 (Trading)
| Method | Endpoint | 説明 | 権限 |
|--------|----------|------|------|
| `GET` | `/api/v1/markets/{id}/estimate` | 取引見積もり計算 | User |
| `POST` | `/api/v1/markets/{id}/trade` | 注文実行 | User |

#### 取引見積もりリクエスト
```
GET /api/v1/markets/{id}/estimate?outcome_id=xxx&action=buy&quantity=10
```

#### 取引実行リクエスト
```json
POST /api/v1/markets/{id}/trade
{
  "outcome_id": "uuid",
  "action": "buy",
  "quantity": 10
}
```

### カテゴリ (Categories)
| Method | Endpoint | 説明 | 権限 |
|--------|----------|------|------|
| `GET` | `/api/v1/categories` | カテゴリ一覧取得 | User |
| `POST` | `/api/v1/categories` | カテゴリ作成 | Admin |

### ランキング・統計 (Leaderboard & Stats)
| Method | Endpoint | 説明 | 権限 |
|--------|----------|------|------|
| `GET` | `/api/v1/leaderboard` | ランキング取得 | User |
| `GET` | `/api/v1/stats/summary` | システム統計サマリー | Admin |

### WebSocket
| Endpoint | 説明 |
|----------|------|
| `/ws/markets/{id}` | マーケット価格のリアルタイム更新 |

---

## 6. インセンティブ・運用設計

*   **インセンティブ**:
    *   上位入賞者への表彰（Amazonギフト券、社内表彰、ランチ券など）。
    *   「予測マイスター」バッジの付与。
*   **運用ルール**:
    *   インサイダー取引の禁止規定（当事者は予測に参加できない、等）。
    *   「Bad News」を予測することへの心理的ハードルを下げる啓蒙（リスク検知こそ価値がある）。

---

## 7. 非機能要件 (Non-Functional Requirements)

### 7.1. パフォーマンス
*   **レスポンスタイム**: API応答 95パーセンタイル < 200ms
*   **スループット**: 同時接続 500ユーザー以上
*   **取引処理**: 秒間 100取引以上

### 7.2. 可用性
*   **稼働率目標**: 99.5%（月間ダウンタイム 3.6時間以内）
*   **メンテナンス窓**: 土曜深夜 2:00-5:00 JST
*   **バックアップ**: 日次自動バックアップ、7日間保持

### 7.3. セキュリティ
*   **認証**: Microsoft Entra ID (Azure AD) によるSSO必須
*   **認可**: ロールベースアクセス制御 (RBAC)
*   **通信**: HTTPS (TLS 1.3) 必須
*   **データ保護**: 個人情報の暗号化保存
*   **監査ログ**: 全取引・管理操作のログ記録

### 7.4. スケーラビリティ
*   **ユーザー数**: 初期 500名、将来 5,000名対応
*   **マーケット数**: 同時稼働 100マーケット以上
*   **水平スケーリング**: Azure Container Apps のオートスケール対応

---

## 8. エラーハンドリング (Error Handling)

### 8.1. 取引エラー
| エラーコード | 説明 | HTTPステータス |
|-------------|------|----------------|
| `INSUFFICIENT_BALANCE` | 残高不足 | 400 |
| `INSUFFICIENT_POSITION` | 保有数量不足（売却時） | 400 |
| `MARKET_NOT_OPEN` | マーケットが取引可能状態でない | 400 |
| `INVALID_QUANTITY` | 無効な数量指定 | 400 |
| `PRICE_BOUNDARY_EXCEEDED` | 価格境界（0.1%-99.9%）超過 | 400 |

### 8.2. 認証・認可エラー
| エラーコード | 説明 | HTTPステータス |
|-------------|------|----------------|
| `UNAUTHORIZED` | 認証が必要 | 401 |
| `FORBIDDEN` | 権限不足 | 403 |
| `TOKEN_EXPIRED` | トークン期限切れ | 401 |

### 8.3. 一般エラー
| エラーコード | 説明 | HTTPステータス |
|-------------|------|----------------|
| `NOT_FOUND` | リソースが見つからない | 404 |
| `VALIDATION_ERROR` | 入力値バリデーションエラー | 422 |
| `INTERNAL_ERROR` | 内部エラー | 500 |

---

## 9. 今後の拡張性 (Roadmap)

*   **LLM連携**: ニュースやSlackの会話から自動で予測市場を生成するAIエージェント。
*   **コメント機能**: なぜその予測をしたかの定性コメントを共有する掲示板。
*   **外部API連携**: Jira等のプロジェクト管理ツールと連携し、タスク完了予測を自動化。
