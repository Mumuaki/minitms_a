# MiniTMS on Windows: Local Run and Packaging

## 1. One-click local run

From `D:\MiniTMS`:

```powershell
.\start.ps1
```

What it does:
- ensures UTF-8 console mode
- creates `backend/.env` from `backend/.env.example` if missing
- runs `alembic upgrade head` (unless `-SkipMigrations`)
- opens backend and frontend in separate PowerShell windows

URLs:
- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`

Stop everything:

```powershell
.\stop.ps1
```

## 2. First-time setup (once per machine)

1. Install Python 3.11+, Node.js 18+, PostgreSQL.
2. In `D:\MiniTMS`:

```powershell
.\venv\Scripts\activate
pip install -r requirements.txt
cd .\frontend
npm install
```

3. Configure database and secrets in `backend/.env`.

## 3. Can this repo be built into a single desktop EXE now?

Not directly. Current project is a web stack:
- backend: FastAPI
- frontend: Vite/React

Current production-like packaging is service/container based, not native single EXE desktop shell.

## 4. Practical PC distribution options

1. Recommended now: deliver as local stack with `start.ps1`/`stop.ps1`.
2. Next step for true desktop app: add Electron or Tauri shell for `frontend`, bundle backend as managed local service process.
3. If needed, create an installer (`MSI`/`EXE`) after shell integration is added.
