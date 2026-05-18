from fastapi import FastAPI, APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from datetime import datetime, timezone

from apex_parser import extract_zip, parse_project
from apex_generator import generate_sql


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI(title="React to Oracle APEX Generator")
api_router = APIRouter(prefix="/api")


@api_router.get("/")
async def root():
    return {"message": "React to Oracle APEX Generator API"}


@api_router.get("/apex/versions")
async def apex_versions():
    return {"versions": ["22.2", "23.1", "23.2", "24.1", "24.2", "26.1"]}


def _run_build(project_root: Path) -> dict:
    """Optionally run npm install + npm run build. Returns status info."""
    log = {"installed": False, "built": False, "stdout": "", "stderr": ""}
    try:
        proc = subprocess.run(
            ["npm", "install", "--no-audit", "--no-fund", "--prefer-offline", "--silent"],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=240,
        )
        log["installed"] = proc.returncode == 0
        log["stdout"] += (proc.stdout or "")[-2000:]
        log["stderr"] += (proc.stderr or "")[-2000:]
        if proc.returncode == 0:
            proc = subprocess.run(
                ["npm", "run", "build"],
                cwd=str(project_root),
                capture_output=True,
                text=True,
                timeout=240,
            )
            log["built"] = proc.returncode == 0
            log["stdout"] += "\n--- build ---\n" + (proc.stdout or "")[-2000:]
            log["stderr"] += "\n--- build ---\n" + (proc.stderr or "")[-2000:]
    except subprocess.TimeoutExpired:
        log["stderr"] += "\nTIMEOUT during npm install/build"
    except FileNotFoundError:
        log["stderr"] += "\nnpm not available in environment"
    except Exception as e:
        log["stderr"] += f"\nException: {e}"
    return log


@api_router.post("/apex/generate")
async def apex_generate(
    file: UploadFile = File(...),
    workspace: str = Form("WKSP_DEFAULT"),
    app_id: int = Form(100),
    apex_version: str = Form("24.2"),
    run_build: bool = Form(False),
):
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip files are accepted")

    session_id = str(uuid.uuid4())
    work_dir = Path(tempfile.gettempdir()) / "apex_gen" / session_id
    work_dir.mkdir(parents=True, exist_ok=True)
    zip_path = work_dir / file.filename

    try:
        # Save uploaded file
        size = 0
        with open(zip_path, "wb") as f:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > 100 * 1024 * 1024:
                    raise HTTPException(status_code=413, detail="File too large (max 100MB)")
                f.write(chunk)

        # Extract
        extract_dir = work_dir / "project"
        try:
            project_root = extract_zip(zip_path, extract_dir)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to extract ZIP: {e}")

        # Optional build
        build_log = None
        if run_build:
            build_log = _run_build(project_root)

        # Parse
        parsed = parse_project(project_root)
        if not parsed["components"]:
            # Still return a minimal SQL with at least one demo component
            parsed["components"] = [
                {"name": "Home", "file": "src/App.jsx", "type": "form",
                 "fields": ["name", "email"], "classnames": [], "has_chart": False}
            ]

        result = generate_sql(parsed, workspace, app_id, apex_version)

        # Persist run metadata
        await db.apex_runs.insert_one({
            "id": session_id,
            "workspace": workspace,
            "app_id": app_id,
            "apex_version": apex_version,
            "filename": file.filename,
            "components": result["pages"],
            "component_count": result["component_count"],
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

        return JSONResponse({
            "session_id": session_id,
            "filename": file.filename,
            "workspace": workspace,
            "app_id": app_id,
            "apex_version": apex_version,
            "component_count": result["component_count"],
            "pages": result["pages"],
            "sql": result["sql"],
            "build_log": build_log,
        })
    finally:
        # Cleanup
        try:
            shutil.rmtree(work_dir, ignore_errors=True)
        except Exception:
            pass


@api_router.get("/apex/runs")
async def list_runs():
    rows = await db.apex_runs.find({}, {"_id": 0, "sql": 0}).sort("created_at", -1).to_list(50)
    return {"runs": rows}


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
