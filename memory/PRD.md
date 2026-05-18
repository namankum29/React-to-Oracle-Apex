# React → Oracle APEX Generator — PRD

## Original Problem Statement
Build a modern enterprise-level web app that converts React projects (ZIP upload) into executable Oracle APEX SQL scripts (pages, forms, reports, dashboards, regions, items, buttons, processes, CSS static file). Dark-themed glassmorphism developer-tool UI.

## Architecture
- **Frontend**: React 19 (CRA) + TailwindCSS + Framer Motion + Lucide React + Sonner toasts
- **Backend**: FastAPI (Python) — user opted for FastAPI over Node.js Express
- **DB**: MongoDB (runs metadata only)
- **Parser**: Python regex-based scanner for .jsx/.tsx files
- **Generator**: Python module emitting `apex_application` PL/SQL helper calls + `wwv_flow_imp_shared.create_app_static_file` for CSS

## User Personas
- APEX developers migrating React/Vite/CRA frontends to Oracle APEX
- Enterprise teams modernizing/lifting legacy apps into APEX low-code

## Core Requirements (static)
- ZIP upload (.zip only, ≤100MB)
- Workspace + App ID + APEX Version (22.2 / 23.1 / 23.2 / 24.1 / 24.2 / 26.1)
- Optional npm install + build toggle
- Detect Forms (useState/emptyForm/controlled inputs) → APEX Form pages
- Detect Reports (`<table>` / `.map()`) → NATIVE_IR regions
- Detect Dashboards (recharts/stat cards) → NATIVE_JET_CHART + stat cards
- Convert CSS classNames → p_region_css_classes / p_page_css_classes
- Generate `react_theme.css` static application file
- Use floatingLabel template option for APEX ≥22.2
- Copy SQL / Download .sql
- Sidebar: Generate SQL · APEX Pages · Export

## Implemented (2026-02-18)
- ✅ Full backend pipeline: extract → parse → generate → return SQL + page summary
- ✅ Endpoints: `GET /api/apex/versions`, `POST /api/apex/generate`, `GET /api/apex/runs`
- ✅ Form/report/dashboard heuristic detection with field extraction
- ✅ Version-aware SQL (floatingLabel template, item types)
- ✅ Optional npm install + build subprocess (with timeout)
- ✅ Frontend: Sidebar, header, upload card (drag-drop), config card, output panel, pages panel, export panel
- ✅ Syntax-highlighted SQL output (keywords/strings/numbers/apex_*)
- ✅ Copy / Download / Toast notifications
- ✅ MongoDB run history persistence (excludes _id and sql blob)
- ✅ Pytest suite at `/app/backend/tests/test_apex_generator.py` (5/5 passing)
- ✅ Testing subagent end-to-end pass: backend 100%, frontend 100%

## Backlog (P1/P2)
- **P1**: Async subprocess for npm build to avoid blocking event loop
- **P1**: Display build logs in UI when run_build=true
- **P2**: Persist generated SQL on server for download via signed URL (large projects)
- **P2**: Multi-file project comparison / diff with existing APEX exports
- **P2**: Detect routing (React Router) → APEX page navigation hierarchy
- **P2**: Auth-aware code generation (if React uses login → APEX authentication scheme)
- **P2**: Drag-and-drop reorder for generated pages
- **P2**: Direct REST push to APEX SQL Workshop via APEX REST API

## Next Tasks
- Move npm build to background worker
- Add streaming logs panel during build
