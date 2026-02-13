"""FastAPI server for the AI Due Diligence commercial API.

Run with:
    uvicorn due_diligence.api.server:app --host 0.0.0.0 --port 8000
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

from due_diligence.api.database import (
    init_db,
    create_api_key,
    create_analysis,
    get_analysis,
    get_analyses_for_key,
    decrement_credits,
)
from due_diligence.api.models import (
    AnalyzeRequest,
    AnalysisStatus,
    AnalysisResult,
    AnalysisListItem,
    SubmitResponse,
    HealthResponse,
    ErrorResponse,
    CreditInfo,
)
from due_diligence.api.auth import require_api_key
from due_diligence.api.worker import AnalysisWorker


# ── App lifecycle ────────────────────────────────────────────────────

worker = AnalysisWorker(poll_interval=2.0, max_concurrent=2)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    worker.start()
    yield
    worker.stop()


# ── FastAPI app ──────────────────────────────────────────────────────

app = FastAPI(
    title="AI Due Diligence API",
    description=(
        "Automated investment due diligence powered by a 7-agent AI pipeline. "
        "Submit a startup or company for analysis and receive a professional "
        "investor memo, HTML report, and visual infographic."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Endpoints ────────────────────────────────────────────────────────


@app.get("/api/v1/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Check API health status."""
    return HealthResponse()


@app.get("/api/v1/credits", response_model=CreditInfo, tags=["Account"])
async def get_credits(key: dict = Depends(require_api_key)):
    """Check remaining analysis credits for your API key."""
    return CreditInfo(
        tier=key["tier"],
        credits_remaining=key["credits_remaining"],
        name=key["name"],
    )


@app.post(
    "/api/v1/analyze",
    response_model=SubmitResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={402: {"model": ErrorResponse}},
    tags=["Analysis"],
)
async def submit_analysis(
    req: AnalyzeRequest,
    request: Request,
    key: dict = Depends(require_api_key),
):
    """Submit a company for due diligence analysis.

    The analysis runs asynchronously through a 7-stage AI pipeline:
    1. Company Research (web search)
    2. Market Analysis (TAM/SAM/SOM)
    3. Financial Modeling (5-year projections)
    4. Risk Assessment (5 dimensions)
    5. Investor Memo (markdown)
    6. HTML Report (McKinsey-style)
    7. Visual Infographic

    Poll the returned `poll_url` to check progress.
    """
    if not decrement_credits(key["id"]):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="No analysis credits remaining. Upgrade your plan.",
        )

    analysis_id = create_analysis(key["id"], req.query)

    base_url = str(request.base_url).rstrip("/")
    poll_url = f"{base_url}/api/v1/analyses/{analysis_id}"

    return SubmitResponse(
        id=analysis_id,
        status="queued",
        message="Analysis queued. Poll the poll_url to track progress.",
        poll_url=poll_url,
    )


@app.get("/api/v1/analyses", response_model=list[AnalysisListItem], tags=["Analysis"])
async def list_analyses(key: dict = Depends(require_api_key)):
    """List your recent analyses."""
    rows = get_analyses_for_key(key["id"])
    return [AnalysisListItem(**r) for r in rows]


@app.get(
    "/api/v1/analyses/{analysis_id}",
    response_model=AnalysisStatus,
    responses={404: {"model": ErrorResponse}},
    tags=["Analysis"],
)
async def get_analysis_status(analysis_id: str, key: dict = Depends(require_api_key)):
    """Get the current status of an analysis.

    Use this to poll for completion. When status is 'completed',
    use the /report, /memo, or /infographic endpoints to download results.
    """
    analysis = get_analysis(analysis_id)
    if not analysis or analysis["api_key_id"] != key["id"]:
        raise HTTPException(status_code=404, detail="Analysis not found.")

    return AnalysisStatus(
        id=analysis["id"],
        query=analysis["query"],
        status=analysis["status"],
        current_stage=analysis["current_stage"],
        stage_name=analysis["stage_name"] or "",
        created_at=analysis["created_at"],
        started_at=analysis.get("started_at"),
        completed_at=analysis.get("completed_at"),
        elapsed_seconds=analysis.get("elapsed_seconds"),
        error=analysis.get("error"),
    )


@app.get(
    "/api/v1/analyses/{analysis_id}/results",
    response_model=AnalysisResult,
    responses={404: {"model": ErrorResponse}, 425: {"model": ErrorResponse}},
    tags=["Results"],
)
async def get_analysis_results(analysis_id: str, key: dict = Depends(require_api_key)):
    """Get full analysis results (memo, report, infographic) as JSON."""
    analysis = get_analysis(analysis_id)
    if not analysis or analysis["api_key_id"] != key["id"]:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    if analysis["status"] != "completed":
        raise HTTPException(status_code=425, detail=f"Analysis not complete. Status: {analysis['status']}")

    return AnalysisResult(
        id=analysis["id"],
        query=analysis["query"],
        status=analysis["status"],
        memo=analysis.get("result_memo"),
        report=analysis.get("result_report"),
        infographic=analysis.get("result_infographic"),
        summary=analysis.get("result_summary"),
        elapsed_seconds=analysis.get("elapsed_seconds"),
    )


@app.get(
    "/api/v1/analyses/{analysis_id}/memo",
    responses={404: {"model": ErrorResponse}, 425: {"model": ErrorResponse}},
    tags=["Results"],
)
async def get_memo(analysis_id: str, key: dict = Depends(require_api_key)):
    """Download the investor memo as markdown text."""
    analysis = get_analysis(analysis_id)
    if not analysis or analysis["api_key_id"] != key["id"]:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    if analysis["status"] != "completed":
        raise HTTPException(status_code=425, detail=f"Analysis not complete. Status: {analysis['status']}")

    return JSONResponse(
        content={"memo": analysis["result_memo"]},
        media_type="application/json",
    )


@app.get(
    "/api/v1/analyses/{analysis_id}/report",
    response_class=HTMLResponse,
    responses={404: {"model": ErrorResponse}, 425: {"model": ErrorResponse}},
    tags=["Results"],
)
async def get_report(analysis_id: str, key: dict = Depends(require_api_key)):
    """Download the HTML investment report. Returns rendered HTML."""
    analysis = get_analysis(analysis_id)
    if not analysis or analysis["api_key_id"] != key["id"]:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    if analysis["status"] != "completed":
        raise HTTPException(status_code=425, detail=f"Analysis not complete. Status: {analysis['status']}")

    return HTMLResponse(content=analysis["result_report"] or "<p>No report available</p>")


@app.get(
    "/api/v1/analyses/{analysis_id}/infographic",
    response_class=HTMLResponse,
    responses={404: {"model": ErrorResponse}, 425: {"model": ErrorResponse}},
    tags=["Results"],
)
async def get_infographic(analysis_id: str, key: dict = Depends(require_api_key)):
    """Download the HTML infographic. Returns rendered HTML."""
    analysis = get_analysis(analysis_id)
    if not analysis or analysis["api_key_id"] != key["id"]:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    if analysis["status"] != "completed":
        raise HTTPException(status_code=425, detail=f"Analysis not complete. Status: {analysis['status']}")

    return HTMLResponse(content=analysis["result_infographic"] or "<p>No infographic available</p>")


# ── Admin Endpoints ──────────────────────────────────────────────────

ADMIN_SECRET = os.getenv("ADMIN_SECRET", "")


@app.post("/admin/create-key", tags=["Admin"])
async def admin_create_key(
    request: Request,
    x_admin_secret: str | None = Header(None),
):
    """Create a new API key (admin only).

    Protected by the ADMIN_SECRET environment variable.
    Set ADMIN_SECRET env var and pass it as X-Admin-Secret header.
    """
    if not ADMIN_SECRET:
        raise HTTPException(status_code=404, detail="Not found")
    if x_admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Invalid admin secret")

    body = await request.json()
    name = body.get("name", "")
    email = body.get("email", "")
    tier = body.get("tier", "free")

    if not name:
        raise HTTPException(status_code=400, detail="'name' is required")
    if tier not in ("free", "pro", "enterprise"):
        raise HTTPException(status_code=400, detail="tier must be free, pro, or enterprise")

    result = create_api_key(name, email, tier)
    return {
        "id": result["id"],
        "api_key": result["api_key"],
        "name": result["name"],
        "tier": result["tier"],
        "credits_remaining": result["credits_remaining"],
    }
