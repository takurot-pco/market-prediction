# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Internal prediction market system (Google Market Prediction inspired) where employees trade virtual currency to predict project outcomes, deadlines, and KPIs. Uses LMSR (Logarithmic Market Scoring Rule) algorithm for automated market making.

## Development Commands

### Backend (FastAPI + Python)

```bash
cd backend

# Install dependencies
poetry install

# Run development server
poetry run uvicorn app.main:app --reload

# Run tests with coverage
poetry run pytest

# Run single test file
poetry run pytest tests/test_main.py

# Run linter
poetry run ruff check app tests

# Auto-fix lint issues
poetry run ruff check --fix app tests

# Type checking
poetry run mypy app

# Run database migrations
poetry run alembic upgrade head

# Create new migration
poetry run alembic revision --autogenerate -m "description"
```

### Frontend (Next.js + TypeScript)

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Run linter
npm run lint
```

### Docker (Full Stack)

```bash
# Start all services (backend, frontend, PostgreSQL)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Architecture

### Monorepo Structure

- `/backend` - FastAPI Python backend with async SQLAlchemy
- `/frontend` - Next.js 14 (App Router) with TypeScript and Tailwind CSS
- `/infra` - Infrastructure as Code (Bicep/Terraform for Azure)
- `/prompt` - Specification and implementation plan documents

### Backend Module Layout

- `app/main.py` - FastAPI application entry point
- `app/core/` - Configuration and core utilities (settings from pydantic-settings)
- `app/db/` - Database session management (async SQLAlchemy)
- `app/models/` - SQLAlchemy ORM models
- `app/api/` - API endpoints (to be implemented)
- `app/services/` - Business logic layer (to be implemented)

### Database

- PostgreSQL 16 with async driver (asyncpg)
- Alembic for migrations (`backend/alembic/`)
- Current model: `User` with id, email, name, role, created_at

### Configuration

Backend configuration via environment variables or `.env` file:
- `DATABASE_URL` - PostgreSQL connection string (async format: `postgresql+asyncpg://...`)

## Testing

Backend tests use pytest-asyncio with aiosqlite for in-memory testing. Tests are located in `backend/tests/`.

## CI/CD

GitHub Actions workflow (`.github/workflows/ci.yml`) runs on PRs to main:
- Backend: ruff lint, mypy type check, pytest
- Frontend: ESLint, Next.js build

## Custom Skills

Project-specific implementation guides are available in `.claude/skills/`:

| Skill | File | Description |
|-------|------|-------------|
| LMSR計算 | `lmsr.md` | 予測市場のLMSRアルゴリズム実装 |
| APIエンドポイント | `api-endpoint.md` | FastAPI エンドポイント生成テンプレート |
| DBモデル | `db-model.md` | SQLAlchemy モデル定義パターン |
| マイグレーション | `migration.md` | Alembic マイグレーション作成ガイド |
| テスト | `test.md` | pytest-asyncio テストコード生成 |
| コンポーネント | `component.md` | React/Next.js コンポーネント作成 |
| エラー処理 | `error-handling.md` | SPEC準拠のエラーハンドリング |
| APIクライアント | `api-client.md` | TypeScript APIクライアント生成 |

## Key Patterns

- All IDs are UUIDs
- Use `Decimal` for financial calculations (balance, cost, quantity)
- Backend follows async SQLAlchemy + FastAPI patterns
- Frontend uses Next.js 14 App Router with TypeScript
- Follow SPEC.md Section 4 for data models
- Follow SPEC.md Section 5 for API design
- Follow SPEC.md Section 8 for error codes

## Implementation Status

See `prompt/PLAN.md` for detailed task tracking. Current status:
- Phase 1 (Foundation): Complete - project setup, DB migrations, CI pipeline
- Phase 2 (Auth & Users): In progress
