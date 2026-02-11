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
2. Executive Summary box with key metrics
3. Company Overview
4. Market Analysis with TAM/SAM/SOM visualization
5. Financial Projections table (Bear/Base/Bull)
6. Risk Assessment heat map
7. Investment Recommendation
8. Appendix with detailed data

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
) -> str:
    return f"""Generate a professional, McKinsey-quality HTML investment report.

**Original Query**: {query}

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

Output ONLY the complete HTML document, starting with <!DOCTYPE html>."""
