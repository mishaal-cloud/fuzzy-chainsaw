"""Web application for the AI Due Diligence tool.

A simple web interface where users enter a company URL and get a full
investment analysis. No API keys needed for end users.

Run with:
    uvicorn due_diligence.webapp.app:app --host 0.0.0.0 --port 8000
"""

import os
import re
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


@app.get("/api/results/{job_id}/memo", response_class=HTMLResponse)
async def get_memo_html(job_id: str):
    """Serve the investor memo as a styled HTML page."""
    job = job_store.get(job_id)
    if not job or job["status"] != "completed":
        raise HTTPException(status_code=404)
    memo_md = job.get("memo", "")
    return HTMLResponse(content=_render_memo_html(memo_md))


def _md_to_html(md: str) -> str:
    """Convert markdown text to HTML body content."""
    if not md:
        return "<p>No memo available.</p>"
    html = md
    # Code blocks (fenced)
    html = re.sub(
        r"```[\w]*\n(.*?)```",
        r"<pre><code>\1</code></pre>",
        html,
        flags=re.DOTALL,
    )
    # Headings
    html = re.sub(r"^#### (.+)$", r"<h4>\1</h4>", html, flags=re.MULTILINE)
    html = re.sub(r"^### (.+)$", r"<h3>\1</h3>", html, flags=re.MULTILINE)
    html = re.sub(r"^## (.+)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)
    html = re.sub(r"^# (.+)$", r"<h1>\1</h1>", html, flags=re.MULTILINE)
    # Horizontal rules
    html = re.sub(r"^---+$", "<hr>", html, flags=re.MULTILINE)
    # Bold and italic
    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
    html = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html)
    # Unordered list items
    html = re.sub(r"^- (.+)$", r"<li>\1</li>", html, flags=re.MULTILINE)
    # Ordered list items
    html = re.sub(r"^\d+\. (.+)$", r"<li>\1</li>", html, flags=re.MULTILINE)
    # Wrap consecutive <li> blocks in <ul>
    html = re.sub(
        r"((?:<li>.*?</li>\n?)+)",
        r"<ul>\1</ul>",
        html,
    )
    # Paragraphs: split on double newlines
    parts = re.split(r"\n{2,}", html)
    processed = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        # Don't wrap block-level elements in <p>
        if re.match(r"<(h[1-4]|ul|ol|pre|hr|blockquote)", part):
            processed.append(part)
        else:
            processed.append(f"<p>{part}</p>")
    html = "\n".join(processed)
    # Convert remaining single newlines to <br> inside paragraphs
    html = re.sub(r"(?<=<p>)(.*?)(?=</p>)", lambda m: m.group(0).replace("\n", "<br>"), html, flags=re.DOTALL)
    return html


def _render_memo_html(md: str) -> str:
    """Wrap converted markdown in a self-contained styled HTML page."""
    body = _md_to_html(md)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Investor Memo</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                 "Helvetica Neue", Arial, sans-serif;
    line-height: 1.7;
    color: #1a202c;
    background: #ffffff;
    max-width: 800px;
    margin: 0 auto;
    padding: 2.5rem 2rem;
  }}
  h1 {{
    font-size: 1.75rem;
    color: #1a365d;
    border-bottom: 2px solid #1a365d;
    padding-bottom: 0.5rem;
    margin-top: 2rem;
  }}
  h2 {{
    font-size: 1.35rem;
    color: #1a365d;
    border-bottom: 1px solid #cbd5e0;
    padding-bottom: 0.35rem;
    margin-top: 1.75rem;
  }}
  h3 {{
    font-size: 1.1rem;
    color: #2d3748;
    margin-top: 1.5rem;
  }}
  h4 {{
    font-size: 1rem;
    color: #4a5568;
    margin-top: 1.25rem;
  }}
  p {{
    margin: 0.75rem 0;
  }}
  ul, ol {{
    padding-left: 1.5rem;
    margin: 0.75rem 0;
  }}
  li {{
    margin: 0.35rem 0;
  }}
  strong {{
    color: #1a202c;
  }}
  hr {{
    border: none;
    border-top: 1px solid #e2e8f0;
    margin: 1.5rem 0;
  }}
  pre {{
    background: #f7fafc;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 1rem;
    overflow-x: auto;
    font-size: 0.875rem;
  }}
  code {{
    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
  }}
  @media print {{
    body {{ padding: 0; max-width: 100%; }}
  }}
</style>
</head>
<body>
{body}
</body>
</html>"""
