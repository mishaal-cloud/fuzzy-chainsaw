"""In-memory job store and worker pool for the web app."""

import time
import uuid
import threading
import traceback
from typing import Any

from due_diligence.agents.company_research import create_company_research_agent, build_prompt as company_prompt
from due_diligence.agents.market_analysis import create_market_analysis_agent, build_prompt as market_prompt
from due_diligence.agents.financial_modeling import create_financial_modeling_agent, build_prompt as financial_prompt
from due_diligence.agents.risk_assessment import create_risk_assessment_agent, build_prompt as risk_prompt
from due_diligence.agents.investor_memo import create_investor_memo_agent, build_prompt as memo_prompt
from due_diligence.agents.report_generator import create_report_generator_agent, build_prompt as report_prompt
from due_diligence.agents.infographic import create_infographic_agent, build_prompt as infographic_prompt


STAGES = [
    (1, "Company Research", "Researching company background, team, funding, and traction..."),
    (2, "Market Analysis", "Analyzing market size, competition, and industry trends..."),
    (3, "Financial Modeling", "Building revenue projections and unit economics..."),
    (4, "Risk Assessment", "Evaluating market, execution, financial, and regulatory risks..."),
    (5, "Investor Memo", "Writing professional investment thesis..."),
    (6, "Report Generation", "Creating detailed HTML investment report..."),
    (7, "Infographic", "Designing visual summary infographic..."),
]


class JobStore:
    """Thread-safe in-memory job store."""

    def __init__(self):
        self._jobs: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()

    def create(self, query: str) -> str:
        job_id = uuid.uuid4().hex[:12]
        with self._lock:
            self._jobs[job_id] = {
                "id": job_id,
                "query": query,
                "status": "queued",
                "stage": 0,
                "stage_name": "Queued",
                "stage_detail": "Waiting to start...",
                "progress_pct": 0,
                "elapsed": 0,
                "error": None,
                "memo": None,
                "report": None,
                "infographic": None,
                "created_at": time.time(),
            }
        return job_id

    def get(self, job_id: str) -> dict | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                if job["status"] == "running":
                    job["elapsed"] = round(time.time() - job.get("started_at", job["created_at"]), 1)
                return dict(job)
        return None

    def update(self, job_id: str, **kwargs):
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id].update(kwargs)


def _run_pipeline(job_id: str, store: JobStore):
    """Run the full analysis pipeline, updating the store along the way."""
    job = store.get(job_id)
    if not job:
        return

    query = job["query"]
    state: dict[str, str] = {}
    start = time.time()
    store.update(job_id, status="running", started_at=start)

    try:
        # Stage 1: Company Research
        store.update(job_id, stage=1, stage_name="Company Research",
                     stage_detail=STAGES[0][2], progress_pct=5)
        agent = create_company_research_agent()
        state["company_research"] = agent.run(company_prompt(query), state)
        store.update(job_id, progress_pct=15)

        # Stage 2: Market Analysis
        store.update(job_id, stage=2, stage_name="Market Analysis",
                     stage_detail=STAGES[1][2], progress_pct=18)
        agent = create_market_analysis_agent()
        state["market_analysis"] = agent.run(
            market_prompt(query, state["company_research"]), state
        )
        store.update(job_id, progress_pct=32)

        # Stage 3: Financial Modeling
        store.update(job_id, stage=3, stage_name="Financial Modeling",
                     stage_detail=STAGES[2][2], progress_pct=35)
        agent = create_financial_modeling_agent()
        state["financial_modeling"] = agent.run(
            financial_prompt(query, state["company_research"], state["market_analysis"]), state
        )
        store.update(job_id, progress_pct=48)

        # Stage 4: Risk Assessment
        store.update(job_id, stage=4, stage_name="Risk Assessment",
                     stage_detail=STAGES[3][2], progress_pct=50)
        agent = create_risk_assessment_agent()
        state["risk_assessment"] = agent.run(
            risk_prompt(query, state["company_research"], state["market_analysis"],
                       state["financial_modeling"]), state
        )
        store.update(job_id, progress_pct=65)

        # Stage 5: Investor Memo
        store.update(job_id, stage=5, stage_name="Investor Memo",
                     stage_detail=STAGES[4][2], progress_pct=68)
        agent = create_investor_memo_agent()
        state["investor_memo"] = agent.run(
            memo_prompt(query, state["company_research"], state["market_analysis"],
                       state["financial_modeling"], state["risk_assessment"]), state
        )
        store.update(job_id, progress_pct=78)

        # Stage 6: HTML Report
        store.update(job_id, stage=6, stage_name="Report Generation",
                     stage_detail=STAGES[5][2], progress_pct=80)
        agent = create_report_generator_agent()
        state["report"] = agent.run(
            report_prompt(query, state["company_research"], state["market_analysis"],
                         state["financial_modeling"], state["risk_assessment"],
                         state["investor_memo"]), state
        )
        store.update(job_id, progress_pct=90)

        # Stage 7: Infographic
        store.update(job_id, stage=7, stage_name="Infographic",
                     stage_detail=STAGES[6][2], progress_pct=92)
        agent = create_infographic_agent()
        state["infographic"] = agent.run(
            infographic_prompt(query, state["company_research"], state["market_analysis"],
                              state["financial_modeling"], state["risk_assessment"],
                              state["investor_memo"]), state
        )

        elapsed = round(time.time() - start, 1)
        store.update(
            job_id,
            status="completed",
            stage=7,
            stage_name="Complete",
            stage_detail="Analysis complete!",
            progress_pct=100,
            elapsed=elapsed,
            memo=state.get("investor_memo", ""),
            report=state.get("report", ""),
            infographic=state.get("infographic", ""),
        )

    except Exception as e:
        elapsed = round(time.time() - start, 1)
        store.update(
            job_id,
            status="failed",
            error=f"{type(e).__name__}: {e}",
            elapsed=elapsed,
        )


class AnalysisWorkerPool:
    """Pool of background threads that process analyses."""

    def __init__(self, store: JobStore, max_concurrent: int = 3):
        self.store = store
        self.max_concurrent = max_concurrent
        self._queue: list[str] = []
        self._lock = threading.Lock()
        self._active: set[str] = set()
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def enqueue(self, job_id: str):
        with self._lock:
            self._queue.append(job_id)

    def _loop(self):
        while self._running:
            with self._lock:
                active_count = len(self._active)
                if self._queue and active_count < self.max_concurrent:
                    job_id = self._queue.pop(0)
                    self._active.add(job_id)
                else:
                    job_id = None

            if job_id:
                t = threading.Thread(target=self._run, args=(job_id,), daemon=True)
                t.start()

            time.sleep(0.5)

    def _run(self, job_id: str):
        try:
            _run_pipeline(job_id, self.store)
        finally:
            with self._lock:
                self._active.discard(job_id)
