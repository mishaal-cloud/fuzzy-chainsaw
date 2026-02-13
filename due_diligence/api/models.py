"""Pydantic models for API request/response schemas."""

from pydantic import BaseModel, Field


# ── Requests ─────────────────────────────────────────────────────────


class AnalyzeRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="The analysis query, e.g. 'Analyze Stripe for a growth-stage investment'",
        json_schema_extra={"examples": ["Analyze https://agno.com for Series A investment of $30-50M"]},
    )
    webhook_url: str | None = Field(
        None,
        description="Optional webhook URL to POST results when analysis completes",
    )


# ── Responses ────────────────────────────────────────────────────────


class AnalysisStatus(BaseModel):
    id: str
    query: str
    status: str = Field(description="queued | running | completed | failed")
    current_stage: int = Field(description="Current pipeline stage (0-7)")
    stage_name: str = Field(description="Human-readable stage name")
    created_at: str
    started_at: str | None = None
    completed_at: str | None = None
    elapsed_seconds: float | None = None
    error: str | None = None


class AnalysisResult(BaseModel):
    id: str
    query: str
    status: str
    memo: str | None = Field(None, description="Markdown investor memo")
    report: str | None = Field(None, description="HTML investment report")
    infographic: str | None = Field(None, description="HTML infographic")
    summary: str | None = Field(None, description="JSON summary data")
    elapsed_seconds: float | None = None


class AnalysisListItem(BaseModel):
    id: str
    query: str
    status: str
    current_stage: int
    stage_name: str
    created_at: str
    completed_at: str | None = None
    elapsed_seconds: float | None = None


class SubmitResponse(BaseModel):
    id: str
    status: str = "queued"
    message: str = "Analysis queued successfully"
    poll_url: str


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
    service: str = "AI Due Diligence API"


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None


class CreditInfo(BaseModel):
    tier: str
    credits_remaining: int
    name: str
