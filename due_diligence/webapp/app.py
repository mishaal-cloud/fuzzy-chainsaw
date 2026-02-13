"""Web application for the AI Due Diligence tool.

A simple web interface where users enter a company URL and get a full
investment analysis. No API keys needed for end users.

Run with:
    uvicorn due_diligence.webapp.app:app --host 0.0.0.0 --port 8000
"""

import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from due_diligence.webapp.jobs import JobStore, AnalysisWorkerPool


# ── Paths ────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"


# ── State ────────────────────────────────────────────────────────────

job_store = JobStore()
worker_pool = AnalysisWorkerPool(job_store, max_concurrent=3)


# ── Lifespan ─────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    worker_pool.start()
    yield
    worker_pool.stop()


# ── App ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="AI Due Diligence",
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# ── Pages ────────────────────────────────────────────────────────────


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/analysis/{job_id}", response_class=HTMLResponse)
async def analysis_page(request: Request, job_id: str):
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return templates.TemplateResponse("analysis.html", {
        "request": request,
        "job_id": job_id,
        "query": job["query"],
    })


# ── API ──────────────────────────────────────────────────────────────


@app.post("/api/analyze")
async def start_analysis(request: Request):
    body = await request.json()
    url = body.get("url", "").strip()
    if not url:
        return JSONResponse({"error": "URL is required"}, status_code=400)

    # Build the query from URL
    query = f"Analyze {url} for investment potential — conduct full due diligence"

    job_id = job_store.create(query)
    worker_pool.enqueue(job_id)

    return {"job_id": job_id, "redirect": f"/analysis/{job_id}"}


@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    job = job_store.get(job_id)
    if not job:
        return JSONResponse({"error": "Not found"}, status_code=404)
    return {
        "id": job["id"],
        "status": job["status"],
        "stage": job["stage"],
        "stage_name": job["stage_name"],
        "progress_pct": job["progress_pct"],
        "elapsed": job["elapsed"],
        "error": job.get("error"),
        "error_stage": job.get("error_stage"),
        "retryable": job.get("retryable", False),
        "retry_info": job.get("retry_info"),
    }


@app.post("/api/retry/{job_id}")
async def retry_analysis(job_id: str):
    """Retry a failed analysis."""
    job = job_store.get(job_id)
    if not job:
        return JSONResponse({"error": "Not found"}, status_code=404)
    if job["status"] != "failed":
        return JSONResponse({"error": "Only failed analyses can be retried"}, status_code=400)
    if not job_store.reset_for_retry(job_id):
        return JSONResponse({"error": "Could not reset job"}, status_code=500)
    worker_pool.enqueue(job_id)
    return {"ok": True, "job_id": job_id}


@app.get("/api/results/{job_id}")
async def get_results(job_id: str):
    job = job_store.get(job_id)
    if not job:
        return JSONResponse({"error": "Not found"}, status_code=404)
    if job["status"] != "completed":
        return JSONResponse({"error": "Not ready"}, status_code=425)
    return {
        "memo": job.get("memo", ""),
        "report": job.get("report", ""),
        "infographic": job.get("infographic", ""),
        "elapsed": job["elapsed"],
    }


@app.get("/api/results/{job_id}/report", response_class=HTMLResponse)
async def get_report_html(job_id: str):
    job = job_store.get(job_id)
    if not job or job["status"] != "completed":
        raise HTTPException(status_code=404)
    return HTMLResponse(content=job.get("report", ""))


@app.get("/api/results/{job_id}/infographic", response_class=HTMLResponse)
async def get_infographic_html(job_id: str):
    job = job_store.get(job_id)
    if not job or job["status"] != "completed":
        raise HTTPException(status_code=404)
    return HTMLResponse(content=job.get("infographic", ""))
