"""In-memory job store and worker pool for the web app."""

import time
import uuid
import threading
import traceback
import logging
from typing import Any

import anthropic

from due_diligence.agents.company_research import create_company_research_agent, build_prompt as company_prompt
from due_diligence.agents.market_analysis import create_market_analysis_agent, build_prompt as market_prompt
from due_diligence.agents.financial_modeling import create_financial_modeling_agent, build_prompt as financial_prompt
from due_diligence.agents.risk_assessment import create_risk_assessment_agent, build_prompt as risk_prompt
from due_diligence.agents.investor_memo import create_investor_memo_agent, build_prompt as memo_prompt
from due_diligence.agents.report_generator import create_report_generator_agent, build_prompt as report_prompt
from due_diligence.agents.infographic import create_infographic_agent, build_prompt as infographic_prompt
from due_diligence.tools.data_availability import parse_data_availability
from due_diligence.tools.consistency_checker import check_stage_consistency, ConsistencyReport
from due_diligence.tools.evaluation_framework import build_framework_block, build_stage_instructions

logger = logging.getLogger(__name__)

STAGES = [
    (1, "Company Research", "Researching company background, team, funding, and traction..."),
    (2, "Market Analysis", "Analyzing market size, competition, and industry trends..."),
    (3, "Financial Modeling", "Building revenue projections and unit economics..."),
    (4, "Risk Assessment", "Evaluating market, execution, financial, technology, and regulatory risks..."),
    (5, "Investor Memo", "Writing professional investment thesis..."),
    (6, "Report Generation", "Creating detailed HTML investment report..."),
    (7, "Infographic", "Designing visual summary infographic..."),
]


def _friendly_error(exc: Exception) -> str:
    """Convert raw API exceptions into user-friendly messages."""
    if isinstance(exc, anthropic.APIStatusError) and exc.status_code == 529:
        return (
            "The AI service is temporarily overloaded. "
            "This usually resolves within a few minutes — please retry."
        )
    if isinstance(exc, anthropic.RateLimitError):
        return (
            "Rate limit reached. The analysis will be retried automatically, "
            "but if this persists please try again in a few minutes."
        )
    if isinstance(exc, anthropic.AuthenticationError):
        return "API authentication failed. Please check the server's API key configuration."
    if isinstance(exc, anthropic.APIConnectionError):
        return "Could not connect to the AI service. Please check network connectivity and retry."
    # Generic fallback — include the exception type but not the raw JSON blob
    return f"An unexpected error occurred ({type(exc).__name__}). Please retry or contact support."


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
                "error_stage": None,
                "retry_info": None,
                "retryable": False,
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

    def reset_for_retry(self, job_id: str) -> bool:
        """Reset a failed job so it can be re-queued."""
        with self._lock:
            job = self._jobs.get(job_id)
            if not job or job["status"] != "failed":
                return False
            job.update({
                "status": "queued",
                "stage": 0,
                "stage_name": "Queued",
                "stage_detail": "Retrying analysis...",
                "progress_pct": 0,
                "error": None,
                "error_stage": None,
                "retry_info": None,
                "retryable": False,
                "memo": None,
                "report": None,
                "infographic": None,
            })
            return True


def _make_retry_callback(job_id: str, store: JobStore):
    """Create a callback that updates the job store with retry status."""
    def on_retry(reason: str, attempt: int, max_attempts: int, wait: float):
        store.update(
            job_id,
            retry_info=f"{reason} — retrying in {wait:.0f}s ({attempt + 1}/{max_attempts})",
        )
    return on_retry


def _run_pipeline(job_id: str, store: JobStore):
    """Run the full analysis pipeline, updating the store along the way."""
    job = store.get(job_id)
    if not job:
        return

    query = job["query"]
    state: dict[str, str] = {}
    start = time.time()
    store.update(job_id, status="running", started_at=start)

    retry_cb = _make_retry_callback(job_id, store)

    def _create_agent(factory):
        agent = factory()
        agent.on_retry = retry_cb
        return agent

    current_stage = 0
    try:
        # Stage 1: Company Research
        current_stage = 1
        store.update(job_id, stage=1, stage_name="Company Research",
                     stage_detail=STAGES[0][2], progress_pct=5, retry_info=None)
        agent = _create_agent(create_company_research_agent)
        state["company_research"] = agent.run(company_prompt(query), state)
        store.update(job_id, progress_pct=14, retry_info=None)

        # ── Data Availability Triage ──────────────────────────
        store.update(job_id, stage_detail="Analyzing data availability...")
        data_profile = parse_data_availability(state["company_research"])
        dp_block = data_profile.to_prompt_block()
        consistency = ConsistencyReport()
        cc_block = ""
        logger.info(f"Job {job_id}: data tier={data_profile.tier}, score={data_profile.score:.2f}")

        # ── Evaluation Framework ──────────────────────────
        company_type = data_profile.company_type
        fw_block = build_framework_block(company_type)
        logger.info(f"Job {job_id}: evaluation framework={company_type}")
        store.update(job_id, progress_pct=15, retry_info=None)

        # Stage 2: Market Analysis
        current_stage = 2
        store.update(job_id, stage=2, stage_name="Market Analysis",
                     stage_detail=STAGES[1][2], progress_pct=18, retry_info=None)
        agent = _create_agent(create_market_analysis_agent)
        eval_block = fw_block + "\n" + build_stage_instructions(company_type, "market_analysis")
        state["market_analysis"] = agent.run(
            market_prompt(query, state["company_research"],
                         data_profile_block=dp_block, consistency_block=cc_block,
                         evaluation_block=eval_block), state
        )
        consistency = check_stage_consistency("Market Analysis", state["market_analysis"], data_profile, consistency)
        cc_block = consistency.to_prompt_block()
        store.update(job_id, progress_pct=32, retry_info=None)

        # Stage 3: Financial Modeling
        current_stage = 3
        store.update(job_id, stage=3, stage_name="Financial Modeling",
                     stage_detail=STAGES[2][2], progress_pct=35, retry_info=None)
        agent = _create_agent(create_financial_modeling_agent)
        eval_block = fw_block + "\n" + build_stage_instructions(company_type, "financial_modeling")
        state["financial_modeling"] = agent.run(
            financial_prompt(query, state["company_research"], state["market_analysis"],
                            data_profile_block=dp_block, consistency_block=cc_block,
                            evaluation_block=eval_block), state
        )
        consistency = check_stage_consistency("Financial Modeling", state["financial_modeling"], data_profile, consistency)
        cc_block = consistency.to_prompt_block()
        store.update(job_id, progress_pct=48, retry_info=None)

        # Stage 4: Risk Assessment
        current_stage = 4
        store.update(job_id, stage=4, stage_name="Risk Assessment",
                     stage_detail=STAGES[3][2], progress_pct=50, retry_info=None)
        agent = _create_agent(create_risk_assessment_agent)
        eval_block = fw_block + "\n" + build_stage_instructions(company_type, "risk_assessment")
        state["risk_assessment"] = agent.run(
            risk_prompt(query, state["company_research"], state["market_analysis"],
                       state["financial_modeling"],
                       data_profile_block=dp_block, consistency_block=cc_block,
                       evaluation_block=eval_block), state
        )
        consistency = check_stage_consistency("Risk Assessment", state["risk_assessment"], data_profile, consistency)
        cc_block = consistency.to_prompt_block()
        store.update(job_id, progress_pct=65, retry_info=None)

        # Stage 5: Investor Memo
        current_stage = 5
        store.update(job_id, stage=5, stage_name="Investor Memo",
                     stage_detail=STAGES[4][2], progress_pct=68, retry_info=None)
        agent = _create_agent(create_investor_memo_agent)
        eval_block = fw_block + "\n" + build_stage_instructions(company_type, "investor_memo")
        state["investor_memo"] = agent.run(
            memo_prompt(query, state["company_research"], state["market_analysis"],
                       state["financial_modeling"], state["risk_assessment"],
                       data_profile_block=dp_block, consistency_block=cc_block,
                       evaluation_block=eval_block), state
        )
        consistency = check_stage_consistency("Investor Memo", state["investor_memo"], data_profile, consistency)
        cc_block = consistency.to_prompt_block()
        store.update(job_id, progress_pct=78, retry_info=None)

        # Stage 6: HTML Report
        current_stage = 6
        store.update(job_id, stage=6, stage_name="Report Generation",
                     stage_detail=STAGES[5][2], progress_pct=80, retry_info=None)
        agent = _create_agent(create_report_generator_agent)
        state["report"] = agent.run(
            report_prompt(query, state["company_research"], state["market_analysis"],
                         state["financial_modeling"], state["risk_assessment"],
                         state["investor_memo"],
                         data_profile_block=dp_block, consistency_block=cc_block,
                         evaluation_block=fw_block), state
        )
        store.update(job_id, progress_pct=90, retry_info=None)

        # Stage 7: Infographic
        current_stage = 7
        store.update(job_id, stage=7, stage_name="Infographic",
                     stage_detail=STAGES[6][2], progress_pct=92, retry_info=None)
        agent = _create_agent(create_infographic_agent)
        state["infographic"] = agent.run(
            infographic_prompt(query, state["company_research"], state["market_analysis"],
                              state["financial_modeling"], state["risk_assessment"],
                              state["investor_memo"],
                              data_profile_block=dp_block, consistency_block=cc_block,
                              evaluation_block=fw_block), state
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
            retry_info=None,
            memo=state.get("investor_memo", ""),
            report=state.get("report", ""),
            infographic=state.get("infographic", ""),
        )

    except Exception as e:
        elapsed = round(time.time() - start, 1)
        is_retryable = isinstance(e, (anthropic.APIStatusError, anthropic.RateLimitError, anthropic.APIConnectionError))
        stage_name = STAGES[current_stage - 1][1] if current_stage > 0 else "Initialization"
        logger.error(f"Job {job_id} failed at stage {current_stage} ({stage_name}): {e}")
        store.update(
            job_id,
            status="failed",
            error=_friendly_error(e),
            error_stage=current_stage,
            retryable=is_retryable,
            retry_info=None,
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
