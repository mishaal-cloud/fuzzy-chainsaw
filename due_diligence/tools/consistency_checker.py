"""Cross-stage consistency checker — catches hallucination leakage between stages.

Runs after each downstream stage and checks whether the output references
specific data points that Stage 1 marked as NOT FOUND. When it catches a
violation, it injects a warning into the pipeline state so subsequent stages
and the final report are aware.
"""

import re
import logging
from dataclasses import dataclass, field

from due_diligence.tools.data_availability import DataProfile

logger = logging.getLogger(__name__)


@dataclass
class ConsistencyViolation:
    """A single consistency violation found in a stage's output."""
    stage_name: str
    field: str
    description: str
    severity: str  # "warning" or "error"
    excerpt: str  # the offending text snippet


@dataclass
class ConsistencyReport:
    """Report of all consistency violations found across stages."""
    violations: list[ConsistencyViolation] = field(default_factory=list)

    @property
    def has_violations(self) -> bool:
        return len(self.violations) > 0

    @property
    def error_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == "warning")

    def to_prompt_block(self) -> str:
        """Generate a warning block to inject into subsequent stage prompts."""
        if not self.violations:
            return ""

        lines = []
        lines.append("")
        lines.append("!" * 70)
        lines.append("CONSISTENCY WARNINGS (from automated verification)")
        lines.append("!" * 70)
        lines.append("The following issues were detected in prior stage outputs.")
        lines.append("Do NOT repeat these issues. Correct them in your output.")
        lines.append("")

        for v in self.violations:
            prefix = "ERROR" if v.severity == "error" else "WARNING"
            lines.append(f"[{prefix}] Stage: {v.stage_name} | Field: {v.field}")
            lines.append(f"  Issue: {v.description}")
            lines.append(f"  Excerpt: \"{v.excerpt[:150]}...\"")
            lines.append("")

        lines.append("!" * 70)
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "total_violations": len(self.violations),
            "errors": self.error_count,
            "warnings": self.warning_count,
            "violations": [
                {
                    "stage": v.stage_name,
                    "field": v.field,
                    "description": v.description,
                    "severity": v.severity,
                }
                for v in self.violations
            ],
        }


# Patterns that suggest a stage is presenting a specific dollar amount
DOLLAR_PATTERN = re.compile(
    r'\$[\d,]+(?:\.\d+)?(?:\s*(?:M|B|K|million|billion|thousand))?',
    re.IGNORECASE,
)

# Patterns that suggest a specific count
COUNT_PATTERN = re.compile(
    r'(?:(?:approximately|about|roughly|over|more than|around)\s+)?'
    r'[\d,]+(?:\+)?\s*(?:customers?|users?|clients?|enterprises?|companies|subscribers?)',
    re.IGNORECASE,
)

# Dollar amount pattern fragment (matches $2.5M, $100K, $1.2 billion, etc.)
_DOLLAR = r'\$[\d,]+(?:\.\d+)?(?:\s*(?:M|B|K|million|billion|thousand))?'

# Fields and their associated keywords for detecting specific claims
FIELD_CLAIM_PATTERNS = {
    "revenue": [
        (rf'(?:revenue|ARR|MRR|annual recurring revenue|monthly recurring revenue)\s+(?:of|is|was|at|reached|hit|exceeded)\s+{_DOLLAR}', "error"),
        (rf'generates?\s+{_DOLLAR}\s+(?:in\s+)?(?:revenue|ARR|annual recurring revenue)', "error"),
        (rf'{_DOLLAR}\s+(?:in\s+)?(?:revenue|ARR|MRR|annual recurring revenue)', "error"),
        (rf'(?:revenue|ARR|MRR)\s+of\s+{_DOLLAR}', "error"),
    ],
    "customer_count": [
        (r'(?:has|serves?|with)\s+[\d,]+(?:\+)?\s+(?:customers?|clients?|enterprises?|enterprise customers?)', "warning"),
        (r'(?:customer|client)\s+(?:base|count)\s+of\s+[\d,]+', "warning"),
        (r'[\d,]+\s+(?:paying|active|enterprise)\s+(?:customers?|clients?)', "warning"),
    ],
    "user_count": [
        (r'(?:has|with|serves?)\s+[\d,]+(?:\+)?\s+(?:users?|subscribers?)', "warning"),
        (r'(?:user|subscriber)\s+(?:base|count)\s+of\s+[\d,]+', "warning"),
        (r'[\d,]+\s+(?:active|registered|monthly)\s+(?:users?)', "warning"),
    ],
    "valuation": [
        (rf'valued?\s+at\s+{_DOLLAR}', "warning"),
        (rf'valuation\s+(?:of|at|is|was)\s+{_DOLLAR}', "warning"),
        (rf'{_DOLLAR}\s+(?:pre-money|post-money)\s+valuation', "warning"),
    ],
    "growth_rate": [
        (r'(?:growing|growth rate|grew)\s+(?:at\s+)?[\d]+%\s+(?:YoY|year-over-year|annually)', "warning"),
        (r'(?:grow|growth)\s+(?:at\s+)?[\d]+%', "warning"),
    ],
    "gross_margin": [
        (r'gross\s+margin\s+(?:of|at|is|was)\s+[\d]+%', "warning"),
    ],
    "burn_rate": [
        (rf'(?:burn|burning)\s+{_DOLLAR}\s+(?:per\s+month|monthly|/month)', "warning"),
    ],
}

# Phrases that indicate the number is clearly labeled as an estimate
ESTIMATE_INDICATORS = [
    r'\[ESTIMATE\]',
    r'\[MODELED\]',
    r'\[ANALYST ESTIMATE\]',
    r'\[INDUSTRY BENCHMARK\]',
    r'(?:our |we )?(?:estimate|model|project|assume)',
    r'modeled estimate',
    r'scenario (?:analysis|illustration)',
    r'assumed',
    r'hypothetical',
    r'if we assume',
    r'based on (?:our |the )?(?:assumptions?|model)',
]


def _is_labeled_as_estimate(text: str, match_start: int, window: int = 200) -> bool:
    """Check if a matched claim is properly labeled as an estimate."""
    start = max(0, match_start - window)
    end = min(len(text), match_start + window)
    context = text[start:end]

    for indicator in ESTIMATE_INDICATORS:
        if re.search(indicator, context, re.IGNORECASE):
            return True
    return False


def check_stage_consistency(
    stage_name: str,
    stage_output: str,
    data_profile: DataProfile,
    report: ConsistencyReport | None = None,
) -> ConsistencyReport:
    """Check a stage's output for consistency violations against the data profile.

    Args:
        stage_name: Name of the stage being checked (e.g., "Financial Modeling")
        stage_output: The full text output of the stage
        data_profile: The data availability profile from Stage 1
        report: Optional existing report to append to

    Returns:
        ConsistencyReport with any violations found
    """
    if report is None:
        report = ConsistencyReport()

    # Get the set of fields that were NOT FOUND
    missing_fields = {
        dp.field for dp in data_profile.data_points
        if dp.status == "not_found"
    }

    for field_name in missing_fields:
        patterns = FIELD_CLAIM_PATTERNS.get(field_name, [])

        for pattern, severity in patterns:
            for match in re.finditer(pattern, stage_output, re.IGNORECASE):
                # Check if this claim is properly labeled as an estimate
                if _is_labeled_as_estimate(stage_output, match.start()):
                    continue  # Properly labeled, no violation

                excerpt = stage_output[max(0, match.start() - 50):match.end() + 50]

                violation = ConsistencyViolation(
                    stage_name=stage_name,
                    field=field_name.replace("_", " ").title(),
                    description=(
                        f"Stage presents specific {field_name.replace('_', ' ')} data, but "
                        f"Company Research marked this as NOT FOUND. This number should be "
                        f"labeled as [ESTIMATE] or [MODELED]."
                    ),
                    severity=severity,
                    excerpt=excerpt.strip(),
                )
                report.violations.append(violation)
                logger.warning(
                    f"Consistency violation in {stage_name}: "
                    f"{field_name} claimed but not found in research"
                )

    return report


def generate_consistency_summary(report: ConsistencyReport) -> str:
    """Generate a human-readable summary for the final report."""
    if not report.has_violations:
        return "All stages are consistent with the source data. No hallucination detected."

    lines = [
        f"Consistency check found {len(report.violations)} issue(s) "
        f"({report.error_count} errors, {report.warning_count} warnings):",
        "",
    ]

    for v in report.violations:
        lines.append(f"- [{v.severity.upper()}] {v.stage_name}: {v.description}")

    lines.append("")
    lines.append(
        "Note: These violations mean some downstream stages may have presented "
        "estimated values without proper labeling. Review flagged sections carefully."
    )

    return "\n".join(lines)
