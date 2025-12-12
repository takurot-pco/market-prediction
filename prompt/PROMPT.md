# 開発タスク実行プロンプト

## 概要

PLAN.mdに従ってTDD（テスト駆動開発）で実装を進め、PR作成までを行う。
実装時はSPEC.mdのデータモデル（Section 4）、API設計（Section 5）、エラーコード（Section 8）を参照する。

## 実行手順

### 1. 次の未実装タスクを特定

@prompt/PLAN.md を確認し、次に実装すべきタスク（`未着手` または `🔧 要対応` マーク）を特定する。

**ステータス凡例**:
| マーク | 意味 |
|--------|------|
| ✅ | 完了 |
| 🔧 | 要修正（既存実装がSPECと乖離） |
| 🚧 | 進行中 |
| 未着手 | 未着手 |

### 2. ブランチ作成

```bash
git checkout main
git pull origin main
git checkout -b feature/task-X.X-機能名
# 例: feature/task-1.2.1-user-model-extension
```

### 3. TDDで実装

#### Backend (Python/FastAPI)

1. **テストを先に書く**: `backend/tests/` にテストファイルを作成
   ```bash
   cd backend
   # 例: tests/test_lmsr.py, tests/test_markets.py
   ```

2. **テストが失敗することを確認**:
   ```bash
   poetry run pytest tests/test_新機能.py -v
   ```

3. **実装コードを書く**: テストがパスする最小限のコードを実装
   - モデル: `app/models/`
   - API: `app/api/`
   - ビジネスロジック: `app/services/` または `app/core/`

4. **リファクタリング**: コード品質を改善（テストがパスし続けることを確認）

#### Frontend (Next.js/TypeScript)

1. **コンポーネント/機能を実装**: `frontend/app/` または `frontend/components/`
2. **型定義**: `frontend/types/` に型を定義
3. **APIクライアント**: `frontend/lib/api/` にAPI呼び出しを実装

### 4. ローカルでの検証

#### Backend
```bash
cd backend
poetry run ruff check app tests          # Lint
poetry run ruff check --fix app tests    # Auto-fix
poetry run mypy app                      # Type check
poetry run pytest                        # 全テスト実行（カバレッジ付き）
poetry run pytest tests/test_xxx.py -v   # 単一テスト
```

#### Frontend
```bash
cd frontend
npm run lint                # ESLint
npm run build               # ビルド確認
```

#### Docker (統合確認)
```bash
docker-compose up -d
# Backend: http://localhost:8000
# Frontend: http://localhost:3000
```

### 5. PLAN.mdのステータス更新

実装完了後、@prompt/PLAN.md の該当タスクを更新:
- `未着手` → `🚧 進行中`（作業開始時）
- `🚧 進行中` → `✅ 完了 (PR#X)`（マージ後）
- `🔧 要対応` → `✅ 完了 (PR#X)`（修正完了後）

### 6. コミット・プッシュ

```bash
git add .
git commit -m "$(cat <<'EOF'
feat(機能名): 実装内容の要約

- 変更点1
- 変更点2

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
git push -u origin feature/task-X.X-機能名
```

**コミットプレフィックス**:
- `feat`: 新機能
- `fix`: バグ修正
- `refactor`: リファクタリング
- `test`: テスト追加・修正
- `docs`: ドキュメント
- `chore`: その他（依存関係更新等）

### 7. PR作成（GitHub CLI）

```bash
gh pr create --title "feat(機能名): Task X.X 実装内容" --body "$(cat <<'EOF'
## Summary
- 実装した機能の概要

## Changes
- 変更点1
- 変更点2

## Test plan
- [ ] pytest 通過
- [ ] ruff check 通過
- [ ] mypy 通過（Backend）
- [ ] npm run lint 通過（Frontend）
- [ ] npm run build 通過（Frontend）

## References
- SPEC.md Section X.X
- PLAN.md Task X.X

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

### 8. CI確認と対処

```bash
# PR一覧からチェック状況を確認
gh pr checks

# 詳細なCI結果を確認
gh run list --limit 5
gh run view <run-id> --log-failed
```

**CIエラー対処の原則**:
- 根本原因を特定し、本質的な修正を行う
- その場しのぎの回避策（テストスキップ、lint無効化等）は禁止
- アーキテクチャに関わる修正が必要な場合は、ユーザーに確認を取る

### 9. マージ後の処理

PRがマージされたら:
1. PLAN.mdの該当タスクを `✅ 完了 (PR#X)` に更新
2. mainブランチに戻る: `git checkout main && git pull`
3. 次のタスクへ進む

## SPEC.md 参照ガイド

| 実装内容 | 参照セクション |
|---------|---------------|
| データモデル | Section 4 |
| API設計 | Section 5 |
| エラーコード | Section 8 |
| LMSRアルゴリズム | Section 3.3 |
| マーケットライフサイクル | Section 3.5 |
| 非機能要件 | Section 7 |

## 注意事項

- **TDDを厳守**: テストを先に書いてから実装する（特にBackend）
- **SPEC.md準拠**: データモデル、API、エラーコードはSPEC.mdに従う
- **PLAN.md準拠**: 作業内容・ファイル構成はPLAN.mdに記載された内容に従う
- **勝手な拡張禁止**: PLAN.mdに記載されていない機能追加やリファクタリングは行わない
- **アーキテクチャ変更禁止**: 全体設計に影響する変更は事前確認が必要
- **UUIDを使用**: 全てのIDはUUID形式（SPEC Section 4準拠）
- **Decimalを使用**: 金額・数量計算はDecimal型（浮動小数点誤差防止）
