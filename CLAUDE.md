# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**International Logistics Quote Management System** — A full-stack enterprise web application for managing and querying freight quotes. Built as a graduation thesis project.

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy 2.0, PyMySQL → MySQL 8.0 (database: `price_test_v2`)
- **Frontend**: Vue 3, Vite, Pinia, Element Plus, Axios, ECharts, Leaflet
- **Data Extraction**: openpyxl/pandas + Zhipu ChatGLM-4 LLM fallback

## Commands

### Backend (FastAPI)
```bash
cd logistics-quote-system/backend

pip install -r requirements.txt

# One-time DB initialization (creates admin/admin123 and user/user123)
python init_db.py

# Dev server — API docs at http://localhost:8000/docs
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend (Vue 3 + Vite)
```bash
cd logistics-quote-system/frontend

npm install
npm run dev      # http://localhost:5173
npm run build
npm run preview
```

### Data Processing Scripts
```bash
# Integration test for the extraction pipeline
python test_new_architecture_with_llm.py

# Process Excel files to JSON
python scripts/excel_reader.py
```

### Database
```bash
mysql -u root -pJHL181116 -e "CREATE DATABASE IF NOT EXISTS price_test_v2 CHARACTER SET utf8mb4"
mysql -u root -pJHL181116 price_test_v2 < database/price_test_v2.sql
```

## Architecture

### Data Model Relationships
```
Route (1) → RouteAgent (N) → FeeItem (N)
                           → FeeTotal (N)
                           → Summary (1)
Route (1) → GoodsDetail/GoodsTotal (N)
```

Core tables: `routes`, `route_agents`, `fee_items`, `fee_total`, `goods_details`, `goods_total`, `summary`, `forex_rate`

v3 upgrade tables (March 2026): `agents`, `ports`, `country_lpi`, `agent_check_history`

### Backend Structure (`logistics-quote-system/backend/app/`)
- `main.py` — FastAPI entry point, global exception handler, CORS middleware
- `config.py` — DB credentials, JWT secret, CORS origins (hardcoded; use .env in production)
- `database.py` — SQLAlchemy engine and session management
- `api/v1/` — Route handlers: `auth.py`, `quotes.py`, `routes.py`, `recommend.py`, `analytics.py`, `ports.py`, `risk.py`, `agent_check.py`, `warnings.py`
- `models/` — ORM models: `route.py` (Route, RouteAgent), `fee.py`, `goods.py`, `user.py`
- `schemas/` — Pydantic request/response schemas
- `crud/` — DB access layer
- `core/security.py` — JWT auth (24h expiry), role-based access (admin/user)

Write operations (`POST/PUT/DELETE` on routes) require admin role. Read operations are open to authenticated users.

### Frontend Structure (`logistics-quote-system/frontend/src/`)
- `views/` — Page components: `Login.vue`, `Dashboard.vue`, `QuoteSearch.vue`, `RouteManage.vue`, `Analytics.vue`, `PortMap.vue`, `RiskProfile.vue`, `AgentCheck.vue`, `Recommend.vue`, `NewRoute/` (multi-step wizard)
- `api/` — Axios wrappers per domain (auth, quote, route, recommend, analytics, ports, risk, agentCheck)
- `stores/user.js` — Pinia store: JWT token + user info, login/logout
- `utils/request.js` — Axios instance with JWT Bearer interceptor
- `router/index.js` — Auth guard redirecting unauthenticated users to `/login`

The Vite dev server proxies `/api` requests to `http://localhost:8000`.

### Data Extraction Pipeline (`scripts/`)
Two-stage hybrid pipeline for importing Excel cost sheets:

1. **Rule-based** (fast, deterministic): `modules/horizontal_table_parser_v2.py` parses Excel tables; `modules/date_extractor.py` extracts dates from filenames; whitelists in `data/` validate agent names and locations.
2. **LLM fallback** (ambiguous data): `modules/llm_enhancer.py` calls Zhipu ChatGLM-4 when rules fail or data is marked "unknown".
3. **Assembly**: `DataAssembler` assigns IDs and links extracted entities.

Validation rules: route origin ≠ destination (neither can be "unknown"), at least 1 known location; agent names must be 1–20 chars, not "unknown" or "pending".

## Key Reference Docs
- `database/README.md` — Full DB schema with field-level specs
- `docs/CODE_GUIDE.md` — Detailed extraction pipeline architecture
- `docs/DEPLOYMENT.md` — Deployment instructions
- `logistics-quote-system/完整启动指南.md` — Complete startup guide (Chinese)
- `ROADMAP.md` — 6-phase development plan
