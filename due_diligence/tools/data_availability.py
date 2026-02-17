"""Data availability parser — extracts what Stage 1 actually found vs. didn't find.

This runs AFTER the Company Research stage and produces a structured "data profile"
that is injected into every downstream agent prompt. This is the key mechanism for
preventing hallucination: downstream agents can only reference data that was actually found.
"""

import re
import json
import logging
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)


# ── Critical data points we look for in Stage 1 output ────────────────────

CRITICAL_FIELDS = [
    "revenue",
    "arr",
    "mrr",
    "customer_count",
    "user_count",
    "growth_rate",
    "funding_total",
    "latest_round",
    "valuation",
    "employee_count",
    "founding_date",
    "founders",
    "gross_margin",
    "burn_rate",
    "runway",
    "ndr",
    "churn",
    "cac",
    "ltv",
    "arpu",
]

# Patterns that indicate a data point was NOT found
NOT_FOUND_PATTERNS = [
    r"NOT FOUND",
    r"not publicly available",
    r"no public .* (data|figures|information|metrics)",
    r"could not (find|locate|verify|confirm)",
    r"no (reliable|credible|verifiable) .* (data|source|information)",
    r"not disclosed",
    r"undisclosed",
    r"information (is |was )?not available",
    r"data (is |was )?not available",
    r"unable to (find|verify|confirm|determine)",
    r"no .* (found|identified|discovered) in search",
]

# Patterns that indicate a data point was verified
VERIFIED_PATTERNS = [
    r"\[VERIFIED",
    r"\[Source:",
    r"\[Confirmed",
]

# Patterns that indicate unverified/self-reported
UNVERIFIED_PATTERNS = [
    r"\[UNVERIFIED",
    r"company website only",
    r"self-reported",
    r"according to (the |their )?website",
    r"company claims",
]


@dataclass
class DataPoint:
    """A single data point extracted from research."""
    field: str
    status: str  # "verified", "unverified", "not_found", "unknown"
    value: str | None = None
    source: str | None = None


@dataclass
class DataProfile:
    """Structured profile of what data is and isn't available."""
    tier: str = "C"  # A = data-rich, B = partial, C = data-scarce
    score: float = 0.0  # 0.0 to 1.0
    data_points: list[DataPoint] = field(default_factory=list)
    verified_facts: list[str] = field(default_factory=list)
    not_found: list[str] = field(default_factory=list)
    unverified_claims: list[str] = field(default_factory=list)
    company_type: str = "unknown"  # "public", "late_private", "early_stage", "pre_product"
    has_revenue_data: bool = False
    has_funding_data: bool = False
    has_team_data: bool = False
    has_traction_data: bool = False

    def to_prompt_block(self) -> str:
        """Generate the DATA PROFILE block that gets injected into downstream prompts."""
        lines = []
        lines.append("=" * 70)
        lines.append("DATA AVAILABILITY PROFILE (auto-generated — DO NOT ignore)")
        lines.append("=" * 70)
        lines.append(f"Data Tier: {self.tier} ({'Data-rich' if self.tier == 'A' else 'Partial data' if self.tier == 'B' else 'Data-scarce'})")
        lines.append(f"Data Score: {self.score:.0%}")
        lines.append(f"Company Type: {self.company_type}")
        lines.append("")

        # What WAS found
        lines.append("VERIFIED DATA POINTS (you may reference these as facts):")
        if self.verified_facts:
            for fact in self.verified_facts:
                lines.append(f"  [OK] {fact}")
        else:
            lines.append("  (none — no data points were independently verified)")
        lines.append("")

        # What was NOT found
        lines.append("NOT FOUND (DO NOT invent values for these — say 'not publicly available'):")
        if self.not_found:
            for gap in self.not_found:
                lines.append(f"  [MISSING] {gap}")
        else:
            lines.append("  (all critical data points were found)")
        lines.append("")

        # Unverified claims
        if self.unverified_claims:
            lines.append("UNVERIFIED CLAIMS (company self-reported — note as unverified):")
            for claim in self.unverified_claims:
                lines.append(f"  [CAUTION] {claim}")
            lines.append("")

        # Hard rules for downstream agents
        lines.append("HALLUCINATION PREVENTION RULES:")
        if not self.has_revenue_data:
            lines.append("  - Revenue/ARR/MRR: NOT AVAILABLE. Do NOT generate specific revenue figures")
            lines.append("    as if they are real. Label ALL revenue numbers as 'MODELED ESTIMATE'.")
        if not self.has_traction_data:
            lines.append("  - Customer/user counts: NOT AVAILABLE. Do NOT cite specific customer numbers.")
            lines.append("    Use ranges based on comparable companies and label as estimates.")
        if not self.has_funding_data:
            lines.append("  - Funding/valuation: NOT AVAILABLE. Do NOT cite specific funding amounts or valuations.")
        lines.append("  - EVERY specific number you generate that is NOT in the VERIFIED list above")
        lines.append("    MUST be prefixed with '[ESTIMATE]' or '[MODELED]'.")
        lines.append("  - When in doubt, say 'not publicly available' rather than guessing.")
        lines.append("=" * 70)

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Serialize for JSON storage / API response."""
        return {
            "tier": self.tier,
            "score": round(self.score, 2),
            "company_type": self.company_type,
            "has_revenue_data": self.has_revenue_data,
            "has_funding_data": self.has_funding_data,
            "has_team_data": self.has_team_data,
            "has_traction_data": self.has_traction_data,
            "verified_count": len(self.verified_facts),
            "not_found_count": len(self.not_found),
            "unverified_count": len(self.unverified_claims),
            "verified_facts": self.verified_facts,
            "not_found": self.not_found,
            "unverified_claims": self.unverified_claims,
        }


def _find_all_occurrences(text: str, keyword: str) -> list[int]:
    """Find all positions of a keyword in text (case-insensitive)."""
    positions = []
    text_lower = text.lower()
    keyword_lower = keyword.lower()
    start = 0
    while True:
        idx = text_lower.find(keyword_lower, start)
        if idx == -1:
            break
        positions.append(idx)
        start = idx + 1
    return positions


def _get_line_context(text: str, pos: int) -> str:
    """Get ONLY the line containing a position.

    Single-line context prevents cross-contamination from adjacent lines
    that might have different verification markers.
    """
    lines = text.split("\n")
    char_count = 0
    for i, line in enumerate(lines):
        char_count += len(line) + 1  # +1 for newline
        if char_count > pos:
            return line
    return lines[-1] if lines else ""


def _classify_field(text: str, field_name: str) -> DataPoint:
    """Classify a single data field as verified, unverified, or not_found.

    Uses LINE-level context to avoid cross-contamination between sections.
    For each occurrence of a keyword, checks the immediate surrounding lines
    (not a 300-char window that could span sections).
    """
    variants = [field_name]
    if "_" in field_name:
        variants.append(field_name.replace("_", " "))

    aliases = {
        "revenue": ["revenue", "sales", "annual revenue", "total revenue"],
        "arr": ["arr", "annual recurring revenue", "annualized revenue"],
        "mrr": ["mrr", "monthly recurring revenue"],
        "customer_count": ["customer count", "customers", "number of customers", "client count"],
        "user_count": ["user count", "users", "active users", "registered users", "dau", "mau"],
        "growth_rate": ["growth rate", "revenue growth", "yoy growth", "year-over-year"],
        "funding_total": ["total funding", "total raised", "funding raised", "raised to date", "raised a"],
        "latest_round": ["latest round", "series", "last round", "most recent round", "seed round"],
        "valuation": ["valuation", "post-money", "pre-money", "valued at"],
        "employee_count": ["employees", "team size", "headcount", "staff"],
        "founding_date": ["founded", "founding", "established", "incorporated"],
        "founders": ["founder", "co-founder", "founding team", "ceo"],
        "gross_margin": ["gross margin", "gross profit margin"],
        "burn_rate": ["burn rate", "monthly burn", "cash burn"],
        "runway": ["runway", "months of runway", "cash runway"],
        "ndr": ["ndr", "net dollar retention", "net revenue retention", "nrr"],
        "churn": ["churn", "churn rate", "customer churn", "logo churn"],
        "cac": ["cac", "customer acquisition cost", "acquisition cost"],
        "ltv": ["ltv", "lifetime value", "customer lifetime value", "clv"],
        "arpu": ["arpu", "average revenue per user", "average revenue per customer"],
    }

    search_terms = aliases.get(field_name, variants)

    # Collect classifications from ALL occurrences, pick the best
    best_status = None
    best_source = None

    for term in search_terms:
        positions = _find_all_occurrences(text, term)
        for pos in positions:
            # Get tight context: just the surrounding lines
            context = _get_line_context(text, pos)

            # Check NOT FOUND
            is_not_found = False
            for pattern in NOT_FOUND_PATTERNS:
                if re.search(pattern, context, re.IGNORECASE):
                    is_not_found = True
                    break

            if is_not_found:
                if best_status is None:
                    best_status = "not_found"
                continue  # Keep looking — another occurrence might be verified

            # Check VERIFIED
            for pattern in VERIFIED_PATTERNS:
                if re.search(pattern, context, re.IGNORECASE):
                    # Verified beats everything
                    return DataPoint(field=field_name, status="verified", source=context.strip()[:200])

            # Check UNVERIFIED
            for pattern in UNVERIFIED_PATTERNS:
                if re.search(pattern, context, re.IGNORECASE):
                    if best_status != "verified":
                        best_status = "unverified"
                        best_source = context.strip()[:200]
                    break
            else:
                # Mentioned but no clear marker — at least it exists
                if best_status is None:
                    best_status = "unknown"

    if best_status == "unverified":
        return DataPoint(field=field_name, status="unverified", source=best_source)
    if best_status == "unknown":
        return DataPoint(field=field_name, status="unknown")
    if best_status == "not_found":
        return DataPoint(field=field_name, status="not_found")

    # Not even mentioned
    return DataPoint(field=field_name, status="not_found")


def _detect_company_type(text: str) -> str:
    """Heuristically detect the company type from research text using weighted scoring.

    Uses a scoring approach rather than first-match to handle ambiguous signals.
    Each signal category has weighted indicators; the category with the highest
    total score wins.
    """
    text_lower = text.lower()

    scores: dict[str, float] = {
        "public": 0,
        "late_private": 0,
        "early_stage": 0,
        "pre_product": 0,
    }

    # ── Public company signals ─────────────────────────────────────
    public_strong = ["nasdaq", "nyse", "publicly traded", "10-k", "sec filing",
                     "stock price", "earnings call", "quarterly earnings"]
    public_moderate = ["ipo", "market cap", "stock ticker", "ticker symbol",
                       "annual report", "shareholders", "public offering",
                       "s-1 filing", "10-q"]
    scores["public"] += 3.0 * sum(1 for s in public_strong if s in text_lower)
    scores["public"] += 1.5 * sum(1 for s in public_moderate if s in text_lower)

    # ── Late-stage private signals ─────────────────────────────────
    late_strong = ["series c", "series d", "series e", "series f", "series g",
                   "growth round", "late-stage", "unicorn"]
    late_moderate = ["billion-dollar valuation", "billion valuation",
                     "1000+ employees", "500+ employees", "hundreds of employees",
                     "over 500 employees", "over 1000 employees",
                     "ipo candidate", "pre-ipo", "crossover round",
                     "decacorn", "growth equity"]
    # Revenue scale signals (strong indicator of late-stage)
    late_revenue = ["$100m", "$200m", "$500m", "$1b", "nine-figure revenue",
                    "hundreds of millions", "over $50m arr", "over $100m"]
    scores["late_private"] += 3.0 * sum(1 for s in late_strong if s in text_lower)
    scores["late_private"] += 2.0 * sum(1 for s in late_moderate if s in text_lower)
    scores["late_private"] += 2.0 * sum(1 for s in late_revenue if s in text_lower)

    # ── Early-stage signals ────────────────────────────────────────
    early_strong = ["series a", "series b", "seed round", "seed funding"]
    early_moderate = ["angel round", "angel investors", "early-stage",
                      "y combinator", "techstars", "accelerator",
                      "500 startups", "500 global", "first round capital",
                      "incubator", "venture-backed", "a]round",
                      "pre-series a", "bridge round",
                      "seed extension", "post-seed"]
    early_weak = ["startup", "founded in 202", "founded in 2023",
                  "founded in 2024", "founded in 2025", "founded in 2026",
                  "small team", "early customers", "initial traction",
                  "product-market fit", "finding pmf"]
    scores["early_stage"] += 3.0 * sum(1 for s in early_strong if s in text_lower)
    scores["early_stage"] += 1.5 * sum(1 for s in early_moderate if s in text_lower)
    scores["early_stage"] += 0.5 * sum(1 for s in early_weak if s in text_lower)

    # ── Pre-product signals ────────────────────────────────────────
    pre_strong = ["pre-revenue", "pre-product", "concept stage", "stealth mode",
                  "stealth startup", "no revenue", "zero revenue"]
    pre_moderate = ["just launched", "alpha version", "prototype", "mvp",
                    "minimum viable product", "pre-launch", "waitlist",
                    "idea stage", "bootstrapping", "no customers yet",
                    "looking for co-founder", "solo founder"]
    pre_weak = ["beta version", "beta testing", "private beta",
                "recently incorporated", "exploring", "early prototype"]
    scores["pre_product"] += 3.0 * sum(1 for s in pre_strong if s in text_lower)
    scores["pre_product"] += 1.5 * sum(1 for s in pre_moderate if s in text_lower)
    scores["pre_product"] += 0.5 * sum(1 for s in pre_weak if s in text_lower)

    # ── Resolve: pick the highest scoring category ─────────────────
    # Public requires a minimum threshold (don't classify as public on one mention of "ipo")
    if scores["public"] < 3.0:
        scores["public"] = 0

    best_type = max(scores, key=scores.get)  # type: ignore[arg-type]
    best_score = scores[best_type]

    if best_score == 0:
        return "unknown"

    logger.debug(f"Company type scores: {scores} -> {best_type}")
    return best_type


def parse_data_availability(company_research_text: str) -> DataProfile:
    """Parse Stage 1 output and produce a structured data availability profile.

    This is the key anti-hallucination mechanism. The resulting DataProfile
    tells every downstream agent exactly what data exists and what doesn't,
    with hard rules preventing them from inventing missing data points.
    """
    profile = DataProfile()

    # Classify each critical field
    for field_name in CRITICAL_FIELDS:
        dp = _classify_field(company_research_text, field_name)
        profile.data_points.append(dp)

        if dp.status == "verified":
            label = field_name.replace("_", " ").title()
            source_snippet = f" — {dp.source[:100]}..." if dp.source else ""
            profile.verified_facts.append(f"{label}{source_snippet}")
        elif dp.status == "not_found":
            profile.not_found.append(field_name.replace("_", " ").title())
        elif dp.status == "unverified":
            label = field_name.replace("_", " ").title()
            profile.unverified_claims.append(f"{label} (company self-reported)")

    # Detect company type
    profile.company_type = _detect_company_type(company_research_text)

    # Compute category flags
    revenue_fields = {"revenue", "arr", "mrr"}
    funding_fields = {"funding_total", "latest_round", "valuation"}
    team_fields = {"employee_count", "founders", "founding_date"}
    traction_fields = {"customer_count", "user_count", "growth_rate", "ndr", "churn"}

    def _has_verified_in(field_set):
        return any(
            dp.status in ("verified", "unverified")
            for dp in profile.data_points
            if dp.field in field_set
        )

    profile.has_revenue_data = _has_verified_in(revenue_fields)
    profile.has_funding_data = _has_verified_in(funding_fields)
    profile.has_team_data = _has_verified_in(team_fields)
    profile.has_traction_data = _has_verified_in(traction_fields)

    # Compute overall score (0.0 to 1.0)
    verified_count = sum(1 for dp in profile.data_points if dp.status == "verified")
    unverified_count = sum(1 for dp in profile.data_points if dp.status == "unverified")
    total = len(profile.data_points)
    # Verified = full credit, unverified = half credit
    profile.score = (verified_count + 0.5 * unverified_count) / total if total > 0 else 0.0

    # Compute tier
    if profile.score >= 0.5:
        profile.tier = "A"
    elif profile.score >= 0.25:
        profile.tier = "B"
    else:
        profile.tier = "C"

    logger.info(
        f"Data profile: tier={profile.tier}, score={profile.score:.2f}, "
        f"verified={verified_count}, not_found={len(profile.not_found)}, "
        f"type={profile.company_type}"
    )

    return profile
