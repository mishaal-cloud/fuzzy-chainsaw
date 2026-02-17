"""Agent 7: Infographic Generator - Visual HTML/CSS summary infographic."""

from due_diligence.agents.base import BaseAgent
from due_diligence.config import WRITING_MODEL, MAX_TOKENS_WRITING

SYSTEM_PROMPT = """You are an expert infographic designer who creates stunning visual summaries using HTML and CSS.
Your infographics are used by top investment firms and featured in pitch decks.

Create a single-page, visually striking HTML infographic that summarizes the investment analysis.
The infographic should be designed to fit on one screen / one printed page.

Design principles:
- Use a dark navy (#0f172a) or white background with high contrast
- Bold, large typography for key numbers and metrics
- Color-coded sections (green for strengths, red for risks, blue for market data)
- Icon-like elements using Unicode symbols (📊 📈 💰 🎯 ⚠️ ✅ etc.)
- Grid layout for metrics (use CSS Grid or Flexbox)
- Circular or badge-style elements for ratings
- Progress bars or gauge-like elements for risk levels
- Clean data visualization using CSS (bar charts with div widths, etc.)

The infographic MUST include:
1. Company name and one-line description (large header)
2. **Data Confidence Indicator** — A visual badge showing overall data confidence
   (High/Medium/Low) based on how much information was verified vs. estimated.
   Use color coding: green = high confidence, yellow = medium, red = low.
3. Key metrics dashboard (4-6 metric cards): funding, market size, revenue, team size, etc.
   - Each metric card should have a small icon indicating if the data is ✓ verified or ⚠ estimated
4. Market opportunity visualization (TAM/SAM/SOM as nested circles or bars)
5. **Financial projection snapshot showing ALL 3 SCENARIOS** (Bear/Base/Bull Year 5 revenue
   as grouped bars or a comparison visual using CSS)
6. **Risk Score Badge** — Large, prominent composite risk score (X.X/10) with a circular
   gauge or progress ring visualization. Below it, show the 6 risk category mini-scores.
7. Investment recommendation badge (INVEST / PASS / MORE DILIGENCE)
8. Top 3 strengths and Top 3 risks as bullet points
9. **Key Open Questions** — 2-3 critical items that need verification before investment

Generate a COMPLETE, self-contained HTML document with embedded CSS.
Use CSS animations sparingly (subtle fade-ins are ok).
The design should look polished and professional, suitable for a board presentation.

IMPORTANT: Output ONLY the HTML code. Start with <!DOCTYPE html> and end with </html>."""

def create_infographic_agent() -> BaseAgent:
    return BaseAgent(
        name="Infographic Generator Agent",
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
    return f"""Create a visually stunning HTML/CSS infographic summarizing this investment analysis.

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

Design a single-page infographic that captures the essence of this investment opportunity
at a glance. Focus on the most impactful data points and make it visually compelling.

CRITICAL: Use the DATA AVAILABILITY PROFILE to set the Data Confidence badge color and label.
Mark each metric card with a checkmark (verified) or warning icon (estimated/missing).

Output ONLY the complete HTML document, starting with <!DOCTYPE html>."""
