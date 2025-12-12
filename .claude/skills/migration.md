# Alembic Migration Helper

## Overview
Alembic を使用したデータベースマイグレーションの作成・管理を支援します。

## 基本コマンド

### マイグレーション作成
```bash
cd backend

# 自動生成（モデル変更を検出）
poetry run alembic revision --autogenerate -m "description_of_changes"

# 空のマイグレーション作成（手動編集用）
poetry run alembic revision -m "description_of_changes"
```

### マイグレーション実行
```bash
# 最新まで適用
poetry run alembic upgrade head

# 1つ進める
poetry run alembic upgrade +1

# 特定のリビジョンまで
poetry run alembic upgrade <revision_id>
```

### ロールバック
```bash
# 1つ戻す
poetry run alembic downgrade -1

# 特定のリビジョンまで戻す
poetry run alembic downgrade <revision_id>

# 全て戻す（危険！）
poetry run alembic downgrade base
```

### 状態確認
```bash
# 現在のリビジョン
poetry run alembic current

# 履歴一覧
poetry run alembic history

# 適用されていないマイグレーション
poetry run alembic heads
```

## マイグレーションファイル構成

```
backend/alembic/
├── alembic.ini          # Alembic設定（プロジェクトルートに配置）
├── env.py               # 環境設定（async対応）
├── script.py.mako       # マイグレーションテンプレート
└── versions/
    ├── 20241203_000001_create_users_table.py
    ├── 20241204_000001_add_department_to_users.py
    └── ...
```

## 命名規則

### ファイル名
```
YYYYMMDD_NNNNNN_description.py
```
- `YYYYMMDD`: 日付
- `NNNNNN`: 連番（同日に複数作成する場合）
- `description`: スネークケースの説明

### revision ID
Alembic が自動生成するハッシュを使用

## マイグレーションテンプレート

```python
"""Add department and balance to users

Revision ID: abc123def456
Revises: previous_revision_id
Create Date: 2024-12-04 10:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'abc123def456'
down_revision: Union[str, None] = 'previous_revision_id'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### Add columns ###
    op.add_column('users', sa.Column('department', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('balance', sa.Numeric(12, 2), nullable=False, server_default='1000.00'))
    
    # ### Remove server_default after initial migration ###
    op.alter_column('users', 'balance', server_default=None)


def downgrade() -> None:
    op.drop_column('users', 'balance')
    op.drop_column('users', 'department')
```

## ENUM型の扱い

### 作成
```python
def upgrade() -> None:
    # ENUM型を作成
    user_role = postgresql.ENUM('admin', 'moderator', 'user', name='user_role')
    user_role.create(op.get_bind())
    
    # カラムに適用
    op.add_column('users', sa.Column(
        'role',
        sa.Enum('admin', 'moderator', 'user', name='user_role'),
        nullable=False,
        server_default='user'
    ))
```

### 削除
```python
def downgrade() -> None:
    op.drop_column('users', 'role')
    
    # ENUM型を削除
    user_role = postgresql.ENUM('admin', 'moderator', 'user', name='user_role')
    user_role.drop(op.get_bind())
```

### ENUM値の追加
```python
def upgrade() -> None:
    # PostgreSQL で ENUM に値を追加
    op.execute("ALTER TYPE market_status ADD VALUE 'suspended'")
```

## UUID主キーへの変更

```python
from sqlalchemy.dialects.postgresql import UUID

def upgrade() -> None:
    # 既存のIntegerカラムをUUIDに変更
    op.execute("ALTER TABLE users ALTER COLUMN id TYPE UUID USING gen_random_uuid()")
    
    # または新しいテーブル作成
    op.create_table(
        'users',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(320), nullable=False, unique=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
```

## インデックス管理

```python
def upgrade() -> None:
    # インデックス作成
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_markets_status', 'markets', ['status'])
    
    # 複合インデックス
    op.create_index('ix_positions_user_market', 'positions', ['user_id', 'market_id'])


def downgrade() -> None:
    op.drop_index('ix_positions_user_market')
    op.drop_index('ix_markets_status')
    op.drop_index('ix_users_email')
```

## 外部キー制約

```python
def upgrade() -> None:
    op.create_foreign_key(
        'fk_markets_category',
        'markets', 'categories',
        ['category_id'], ['id'],
        ondelete='RESTRICT'
    )
    
    op.create_foreign_key(
        'fk_positions_market',
        'positions', 'markets',
        ['market_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    op.drop_constraint('fk_positions_market', 'positions', type_='foreignkey')
    op.drop_constraint('fk_markets_category', 'markets', type_='foreignkey')
```

## データマイグレーション

```python
from sqlalchemy.sql import table, column
from sqlalchemy import String

def upgrade() -> None:
    # テーブル参照を作成
    users = table('users', column('role', String))
    
    # データを更新
    op.execute(users.update().where(users.c.role == None).values(role='user'))


def downgrade() -> None:
    pass  # データマイグレーションは通常ロールバックしない
```

## 注意事項

### 自動生成の確認ポイント
1. **テーブル名**: 正しいテーブルが対象か
2. **カラム型**: 期待する型になっているか
3. **Nullable**: NOT NULL制約が正しいか
4. **デフォルト値**: server_defaultが設定されているか
5. **インデックス**: 必要なインデックスが含まれているか
6. **ENUM型**: 正しく作成/削除されているか

### ベストプラクティス
- マイグレーションは小さく保つ（1つの変更に1つのファイル）
- downgrade() を必ず実装する
- 本番適用前にステージングでテスト
- データ量が多い場合はバッチ処理を検討

## 関連ドキュメント
- SPEC.md Section 4: データモデル設計
- PLAN.md Task 1.2: データベースマイグレーション基盤
