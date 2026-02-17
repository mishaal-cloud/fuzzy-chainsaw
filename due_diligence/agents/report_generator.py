"""Agent 6: Report Generator - McKinsey-style professional HTML report."""

from due_diligence.agents.base import BaseAgent
from due_diligence.config import WRITING_MODEL, MAX_TOKENS_WRITING

SYSTEM_PROMPT = """You are a professional report designer who creates McKinsey-quality investment reports.
You generate clean, modern HTML reports with embedded CSS styling.

Your reports are known for:
- Clean, professional typography (use system fonts: -apple-system, BlinkMacSystemFont, 'Segoe UI', etc.)
- Strategic use of color (navy #1a365d for headers, green #2d8a4e for positive, red #c53030 for negative)
- Well-organized sections with clear hierarchy
- Data presented in clean tables and styled callout boxes
- Executive summary boxes with key metrics
- Risk heat maps as styled HTML tables
- Financial data in formatted tables with alternating row colors

Generate a COMPLETE, self-contained HTML document (with embedded CSS, no external dependencies).
The HTML should be print-ready and look professional when opened in a browser.

Structure the report as:
1. Title page / header with company name and date
2. **Data Confidence Banner** — A prominent callout at the top indicating:
   - How much data was verified vs. estimated
   - Overall data confidence level (High / Medium / Low)
   - Brief note on key information gaps
3. Executive Summary box with key metrics
4. Company Overview
5. Market Analysis with TAM/SAM/SOM visualization
6. **Financial Projections table (Bear/Base/Bull)** — Show ALL THREE scenarios prominently
   in a comparison table, NOT just the base case
7. **Risk Assessment Dashboard** — Risk heat map as a styled grid with:
   - 6 risk categories (Market, Execution, Financial, Regulatory, Exit, Information)
   - Color-coded severity (green/yellow/orange/red)
   - Numeric score per category (X/10)
   - Composite risk score displayed prominently
8. **Information Gaps & Open Questions** — Dedicated section listing:
   - What could not be verified
   - What relies on company self-reporting only
   - Recommended follow-up diligence steps
9. Investment Recommendation
10. **Sources & Evidence Trail** — List of all cited sources with URLs
11. Appendix with detailed data

## EVIDENCE INTEGRITY IN THE REPORT

- When presenting financial metrics, use visual indicators for data confidence:
  - Green checkmark icon (✓) for VERIFIED data points
  - Yellow warning icon (⚠) for ESTIMATED/MODELED data points
  - Red question mark icon (?) for NOT FOUND / UNVERIFIED data points
- In financial tables, include a "Basis" column or footer indicating whether each
  number is from verified data, industry benchmarks, or analyst estimates

IMPORTANT: Output ONLY the HTML code, no explanatory text before or after.
Start with <!DOCTYPE html> and end with </html>."""

def create_report_generator_agent() -> BaseAgent:
    return BaseAgent(
        name="Report Generator Agent",
        system_prompt=SYSTEM_PROMPT,
        model=WRITING_MODEL,
        max_tokens=MAX_TOKENS_WRITING,
        tools=[],
    )


def build_prompt(
    query: str,
    company_research: str,
    market_analysis: str,
    financial_modeling: str,
    risk_assessment: str,
    investor_memo: str,
    data_profile_block: str = "",
    consistency_block: str = "",
    evaluation_block: str = "",
) -> str:
    return f"""Generate a professional, McKinsey-quality HTML investment report.

**Original Query**: {query}

{data_profile_block}
{consistency_block}
{evaluation_block}

**Company Research**:
{company_research}

**Market Analysis**:
{market_analysis}

**Financial Projections**:
{financial_modeling}

**Risk Assessment**:
{risk_assessment}

**Investment Memo**:
{investor_memo}

Create a beautiful, self-contained HTML report that synthesizes all the above analysis.
Include styled tables for financial data, a risk heat map, executive summary callout,
and professional formatting throughout.

CRITICAL: Use the DATA AVAILABILITY PROFILE to populate the Data Confidence Banner.
Show the data tier ({data_profile_block[:50]}...) prominently. Use checkmark/warning/question
icons to indicate verified/estimated/missing data throughout all tables.

Output ONLY the complete HTML document, starting with <!DOCTYPE html>."""
