"""Background worker that processes queued analyses."""

import json
import time
import threading
import traceback
import logging

import anthropic

from due_diligence.api.database import (
    get_next_queued,
    update_analysis_stage,
    complete_analysis,
    fail_analysis,
)
from due_diligence.orchestrator import DueDiligencePipeline
from due_diligence.agents.company_research import create_company_research_agent, build_prompt as company_prompt
from due_diligence.agents.market_analysis import create_market_analysis_agent, build_prompt as market_prompt
from due_diligence.agents.financial_modeling import create_financial_modeling_agent, build_prompt as financial_prompt
from due_diligence.agents.risk_assessment import create_risk_assessment_agent, build_prompt as risk_prompt
from due_diligence.agents.investor_memo import create_investor_memo_agent, build_prompt as memo_prompt
from due_diligence.agents.report_generator import create_report_generator_agent, build_prompt as report_prompt
from due_diligence.agents.infographic import create_infographic_agent, build_prompt as infographic_prompt
from due_diligence.tools.chart_generator import generate_all_charts

logger = logging.getLogger(__name__)


def _friendly_error(exc: Exception) -> str:
    """Convert raw API exceptions into user-friendly messages."""
    if isinstance(exc, anthropic.APIStatusError) and exc.status_code == 529:
        return (
            "The AI service is temporarily overloaded. "
            "This usually resolves within a few minutes — please retry."
        )
    if isinstance(exc, anthropic.RateLimitError):
        return "Rate limit reached. Please try again in a few minutes."
    if isinstance(exc, anthropic.AuthenticationError):
        return "API authentication failed. Please check the server's API key configuration."
    if isinstance(exc, anthropic.APIConnectionError):
        return "Could not connect to the AI service. Please check network connectivity and retry."
    return f"An unexpected error occurred ({type(exc).__name__}). Please retry or contact support."


STAGE_NAMES = [
    "",
    "Company Research",
    "Market Analysis",
    "Financial Modeling",
    "Risk Assessment",
    "Investor Memo",
    "Report Generation",
    "Infographic Generation",
]


def run_analysis(analysis_id: str, query: str):
    """Run the full 7-stage pipeline for an analysis job, updating status along the way."""
    start_time = time.time()
    state: dict[str, str] = {}

    try:
        # Stage 1: Company Research
        update_analysis_stage(analysis_id, 1, STAGE_NAMES[1])
        agent = create_company_research_agent()
        prompt = company_prompt(query)
        state["company_research"] = agent.run(prompt, state)

        # Stage 2: Market Analysis
        update_analysis_stage(analysis_id, 2, STAGE_NAMES[2])
        agent = create_market_analysis_agent()
        prompt = market_prompt(query, state["company_research"])
        state["market_analysis"] = agent.run(prompt, state)

        # Stage 3: Financial Modeling
        update_analysis_stage(analysis_id, 3, STAGE_NAMES[3])
        agent = create_financial_modeling_agent()
        prompt = financial_prompt(query, state["company_research"], state["market_analysis"])
        state["financial_modeling"] = agent.run(prompt, state)

        # Stage 4: Risk Assessment
        update_analysis_stage(analysis_id, 4, STAGE_NAMES[4])
        agent = create_risk_assessment_agent()
        prompt = risk_prompt(query, state["company_research"], state["market_analysis"], state["financial_modeling"])
        state["risk_assessment"] = agent.run(prompt, state)

        # Stage 5: Investor Memo
        update_analysis_stage(analysis_id, 5, STAGE_NAMES[5])
        agent = create_investor_memo_agent()
        prompt = memo_prompt(query, state["company_research"], state["market_analysis"], state["financial_modeling"], state["risk_assessment"])
        state["investor_memo"] = agent.run(prompt, state)

        # Stage 6: HTML Report
        update_analysis_stage(analysis_id, 6, STAGE_NAMES[6])
        agent = create_report_generator_agent()
        prompt = report_prompt(query, state["company_research"], state["market_analysis"], state["financial_modeling"], state["risk_assessment"], state["investor_memo"])
        state["report"] = agent.run(prompt, state)

        # Stage 7: Infographic
        update_analysis_stage(analysis_id, 7, STAGE_NAMES[7])
        agent = create_infographic_agent()
        prompt = infographic_prompt(query, state["company_research"], state["market_analysis"], state["financial_modeling"], state["risk_assessment"], state["investor_memo"])
        state["infographic"] = agent.run(prompt, state)

        elapsed = time.time() - start_time

        # Build summary JSON
        summary = json.dumps({
            "query": query,
            "stages_completed": 7,
            "elapsed_seconds": round(elapsed, 1),
        })

        complete_analysis(
            analysis_id,
            memo=state.get("investor_memo", ""),
            report=state.get("report", ""),
            infographic=state.get("infographic", ""),
            summary=summary,
            elapsed=elapsed,
        )

    except Exception as e:
        logger.error(f"Analysis {analysis_id} failed: {traceback.format_exc()}")
        fail_analysis(analysis_id, _friendly_error(e))


class AnalysisWorker:
    """Background worker thread that polls for queued analyses and processes them."""

    def __init__(self, poll_interval: float = 2.0, max_concurrent: int = 2):
        self.poll_interval = poll_interval
        self.max_concurrent = max_concurrent
        self._running = False
        self._thread: threading.Thread | None = None
        self._active_jobs: set[str] = set()
        self._lock = threading.Lock()

    def start(self):
        """Start the background worker."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)

    def _poll_loop(self):
        while self._running:
            try:
                with self._lock:
                    active_count = len(self._active_jobs)

                if active_count < self.max_concurrent:
                    job = get_next_queued()
                    if job:
                        analysis_id = job["id"]
                        with self._lock:
                            if analysis_id in self._active_jobs:
                                continue
                            self._active_jobs.add(analysis_id)

                        t = threading.Thread(
                            target=self._run_job,
                            args=(analysis_id, job["query"]),
                            daemon=True,
                        )
                        t.start()

            except Exception:
                pass  # Don't crash the poller

            time.sleep(self.poll_interval)

    def _run_job(self, analysis_id: str, query: str):
        try:
            # Mark as running so poller doesn't pick it up again
            update_analysis_stage(analysis_id, 0, "Starting")
            run_analysis(analysis_id, query)
        finally:
            with self._lock:
                self._active_jobs.discard(analysis_id)
