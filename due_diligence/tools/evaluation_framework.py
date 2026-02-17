"""Stage-specific evaluation frameworks.

A pre-seed startup with 2 founders and an idea should be evaluated on completely
different criteria than a Series B company with $20M ARR. This module produces
an EVALUATION FRAMEWORK block that tells each agent WHAT to focus on and HOW to
evaluate based on the company stage.

Company types (from data_availability.py):
  - pre_product: Pre-revenue, pre-product, concept stage, stealth
  - early_stage: Seed, Series A, accelerator graduates
  - late_private: Series C+, growth stage, unicorn territory
  - public: Publicly traded, IPO candidate
  - unknown: Couldn't determine (treat as early_stage)
"""

# ── Per-stage evaluation criteria by company type ─────────────────────────


FRAMEWORKS = {

    # ══════════════════════════════════════════════════════════════════════
    # PRE-PRODUCT / PRE-SEED
    # ══════════════════════════════════════════════════════════════════════
    "pre_product": {
        "label": "Pre-Product / Pre-Seed",
        "philosophy": (
            "At this stage, you are evaluating a TEAM and an IDEA, not a business. "
            "There are no meaningful financials to model. The investment thesis is: "
            "'Do these founders have the insight, skills, and determination to find "
            "product-market fit in a large enough market?' Everything else is speculation."
        ),

        "company_research": {
            "focus": "FOUNDERS AND IDEA VALIDATION",
            "instructions": """
At pre-product stage, traditional company research is mostly irrelevant. Focus on:

1. **Founder Deep-Dive** (this is 60% of the evaluation):
   - Each founder's background, domain expertise, and relevant track record
   - Have they worked in this domain? Do they have unfair insight into the problem?
   - Prior startup experience — did they build/ship products before?
   - Technical capability — can they build V1 without external dev?
   - Founder-market fit: WHY are these specific people solving this problem?
   - Team dynamics: how did they meet, how long have they worked together?

2. **Problem Validation** (30% of the evaluation):
   - What specific problem are they solving? For whom?
   - How do people currently solve this problem? (existing alternatives)
   - Evidence of real pain: customer interviews, waitlist signups, LOIs
   - Is this a vitamin (nice to have) or painkiller (must have)?

3. **Early Signals** (10%):
   - Prototype or demo available?
   - Any early users, even unpaid?
   - Accelerator participation (YC, Techstars, etc.)
   - Quality of advisors

DO NOT waste time searching for revenue, financial metrics, or detailed traction.
These do not exist at this stage and searching for them adds no value.
""",
        },

        "market_analysis": {
            "focus": "PROBLEM SIZE AND TIMING",
            "instructions": """
For a pre-product company, market analysis should answer: "Is the problem big enough
to justify venture-scale investment?" NOT "What is the exact TAM?"

Focus on:
1. **Problem Magnitude**: How many people/businesses have this problem? How painful is it?
   Bottom-up from the problem, not top-down from industry reports.
2. **Why Now?**: What changed (technology, regulation, behavior) that makes this solvable NOW?
   If this problem existed for 10 years, why hasn't it been solved?
3. **Existing Alternatives**: How do people solve this today? How much do they spend?
   (This IS the real market size — not a Gartner forecast.)
4. **Comparable Companies**: Find 3-5 companies that solved similar problems in adjacent
   markets. What were their trajectories? This is the best proxy for market potential.

DO NOT spend time on precise TAM/SAM/SOM calculations. At pre-product, these are fiction.
Instead, provide a "napkin math" market size with clear assumptions.
""",
        },

        "financial_modeling": {
            "focus": "BURN RATE AND COMPARABLE TRAJECTORIES",
            "instructions": """
Traditional financial modeling is NOT appropriate for pre-product companies.
There is no revenue to project and no unit economics to analyze.

Instead, provide:
1. **Burn Rate Analysis**: How much will they burn monthly? How long will the raise last?
   - Team salaries (based on team size and location)
   - Infrastructure/hosting costs
   - Expected runway from this raise

2. **Comparable Company Trajectories**: Find 3-5 similar companies at similar stages.
   What did their first 3 years look like? Use these as scenario templates:
   - Rocket ship: Found PMF in 6 months, $1M ARR in 18 months
   - Steady build: 12-18 months to PMF, $500K ARR in 24 months
   - Pivot path: Initial idea didn't work, pivoted, eventually found traction

3. **Milestone-Based Valuation**: Instead of DCF or revenue multiples, evaluate:
   - What milestones should the company hit with this capital?
   - What valuation is appropriate at each milestone?
   - Standard pre-seed: $2-8M pre-money; seed: $8-20M pre-money

4. **Capital Efficiency**: How much capital to reach PMF?
   Compare to benchmarks for similar company types.

DO NOT generate detailed 5-year revenue projections. They are meaningless at this stage.
Label everything as [ILLUSTRATIVE SCENARIO] not [MODELED ESTIMATE].
""",
        },

        "risk_assessment": {
            "focus": "TEAM AND FEASIBILITY RISK",
            "instructions": """
At pre-product stage, the risk profile is fundamentally different:

DOMINANT RISKS (weight these 70% of your assessment):
- **Team Risk**: Can these founders execute? Do they have the right skills? Key-person dependency?
- **Technical Feasibility**: Can this actually be built? Is the technology ready?
- **Problem-Solution Fit**: Is the proposed solution actually what customers want?
- **Market Timing**: Is this too early? Too late?

SECONDARY RISKS (weight 30%):
- **Competition**: Who else is working on this? Are well-funded incumbents entering?
- **Capital Risk**: Will they be able to raise the next round? What milestones are needed?

RISKS THAT ARE NOT RELEVANT AT THIS STAGE (DO NOT overweight):
- Financial risk (there are no financials)
- Unit economics risk (there are no unit economics)
- Regulatory risk (unless the entire business model depends on regulation)
- Exit risk (way too early to assess)

Score team risk and feasibility risk separately — these matter most.
""",
        },

        "investor_memo": {
            "focus": "TEAM-BET THESIS",
            "instructions": """
The investment memo for a pre-product company should read as a TEAM BET, not a financial analysis.

Structure:
1. **Why This Team**: The #1 question. Why will THESE founders win in THIS market?
2. **Why This Problem**: Evidence that the problem is real, painful, and large enough
3. **Why Now**: The catalyst that makes this the right time
4. **What Could Go Right**: The bull case — if everything clicks, what does this become?
5. **Key Risks**: Primarily team and execution risk
6. **Milestone Plan**: What should they achieve with this capital? (not revenue targets,
   but product milestones: "ship V1", "10 design partners", "first paying customer")
7. **Recommendation**: Frame as "Do we believe in this team?" not "Do the numbers work?"

The recommendation should be one of:
- INVEST: Exceptional team + large problem + right timing
- PASS: Team gaps, unclear problem, or bad timing
- CONDITIONAL: Would invest if [specific condition met]
""",
        },
    },

    # ══════════════════════════════════════════════════════════════════════
    # EARLY STAGE (Seed / Series A)
    # ══════════════════════════════════════════════════════════════════════
    "early_stage": {
        "label": "Early Stage (Seed / Series A)",
        "philosophy": (
            "At seed/Series A, you are evaluating PRODUCT-MARKET FIT SIGNALS. "
            "The company may have some revenue and early customers, but the core "
            "question is: 'Is there evidence that this product solves a real problem "
            "that people will pay for, and can this scale?' Team still matters enormously, "
            "but now there should be early data to validate or challenge the thesis."
        ),

        "company_research": {
            "focus": "PRODUCT-MARKET FIT SIGNALS",
            "instructions": """
At seed/Series A, research should focus on evidence of product-market fit:

1. **Product & Technology** (30%):
   - What does the product actually do? (not marketing copy — real capabilities)
   - Technology differentiation: what's proprietary vs. commodity?
   - Product maturity: beta, launched, iterating?
   - User reviews, Product Hunt reception, app store ratings

2. **Traction Evidence** (30%):
   - Revenue if available (MRR/ARR), even if small
   - Customer count and type (paying vs. free, enterprise vs. SMB)
   - Growth rate — the RATE matters more than the absolute number
   - Engagement metrics: DAU/MAU ratio, retention curves, NPS
   - Logo quality: any notable customers?

3. **Team & Culture** (25%):
   - Founder backgrounds and domain expertise
   - Key hires made — have they attracted strong talent?
   - Team size and growth rate (hiring velocity = confidence signal)
   - Glassdoor/culture signals

4. **Funding & Investors** (15%):
   - Capital raised to date, investor quality
   - Burn rate and runway
   - Cap table health (red flags: too many small investors, excessive dilution)
""",
        },

        "market_analysis": {
            "focus": "COMPETITIVE POSITIONING AND WEDGE",
            "instructions": """
For early-stage companies, market analysis should focus on competitive positioning:

1. **Market Sizing**: Do TAM/SAM/SOM but anchor to bottom-up methodology.
   Top-down ("the AI market is $500B") is useless. Bottom-up: "There are X potential
   customers × $Y ACV = $Z addressable market."

2. **Competitive Landscape**: This is CRITICAL at this stage.
   - Map ALL competitors (direct, indirect, adjacent)
   - Feature comparison matrix (what does this company do better/worse?)
   - Competitive moat: what prevents incumbents from copying this?
   - Pricing comparison: how does this company price vs. alternatives?

3. **Wedge Strategy**: How is the company entering the market?
   - What's the initial beachhead segment?
   - Land-and-expand potential?
   - Is the wedge defensible?

4. **Market Timing**: Why is this market ready NOW?
   - Technology enablers, regulatory changes, behavior shifts
""",
        },

        "financial_modeling": {
            "focus": "UNIT ECONOMICS AND GROWTH TRAJECTORY",
            "instructions": """
At seed/Series A, the financial model should validate unit economics more than project revenue:

1. **Unit Economics Deep-Dive** (most important):
   - CAC by channel (if available) — is there a scalable acquisition channel?
   - LTV (even if estimated from early cohorts)
   - LTV/CAC ratio — is it >3x? On what timeline?
   - Payback period — how fast does the company recoup CAC?
   - Gross margin — is the delivery model economically viable?

2. **Revenue Model Validation**:
   - Is the pricing model proven? Have customers actually paid?
   - Average deal size / ARPU — is it growing or shrinking?
   - Net Dollar Retention — are existing customers expanding?

3. **Growth Projections** (3 scenarios):
   - Use CURRENT growth rate as base, not aspirational targets
   - Bear: growth decelerates; Base: growth sustains; Bull: growth accelerates
   - 3-year horizon is more relevant than 5-year at this stage

4. **Capital Needs**:
   - How much capital to reach profitability or next milestone?
   - When will they need to raise again?
   - What does dilution path look like?

If revenue data is NOT FOUND, use comparable company benchmarks as proxy.
""",
        },

        "risk_assessment": {
            "focus": "BALANCED RISK WITH GTM EMPHASIS",
            "instructions": """
At seed/Series A, risk assessment should be more balanced than pre-seed:

1. **Product-Market Fit Risk** (25%): Is there real PMF or just early interest?
   - Customer retention signals
   - Organic growth vs. paid acquisition dependency
   - Customer feedback patterns

2. **Execution Risk** (25%): Can the team scale from 0→1 to 1→10?
   - Team completeness (CTO, sales leader, etc.)
   - Hiring plan and talent market
   - Operational complexity of scaling

3. **Go-to-Market Risk** (20%): Can they acquire customers efficiently?
   - CAC trends — improving or worsening?
   - Channel dependency — one channel or diversified?
   - Sales cycle length and complexity

4. **Market Risk** (15%): Competitive and timing risk
   - Well-funded competitors entering the space
   - Market timing — adoption curve position

5. **Financial Risk** (15%): Runway and capital efficiency
   - Burn rate vs. revenue trajectory
   - Funding environment for next round
""",
        },

        "investor_memo": {
            "focus": "TRACTION-VALIDATED THESIS",
            "instructions": """
The early-stage memo should blend team conviction with early data validation:

1. **Traction Evidence**: Lead with data — what metrics prove PMF is emerging?
2. **Team + Market**: Why this team in this market
3. **Unit Economics Viability**: Is the model economically sound?
4. **Competitive Position**: Can they defend and expand?
5. **Growth Path**: Realistic path from current stage to 10x growth
6. **Key Risks + Mitigants**: Honest assessment with concrete mitigants
7. **Recommendation**: Based on blend of qualitative (team, market) and quantitative (metrics)

The recommendation framework:
- INVEST: Clear PMF signals + strong team + large market + reasonable valuation
- MORE DILIGENCE: Promising but need customer references, deeper metrics, or competitive clarity
- PASS: Weak PMF signals, team concerns, or market too small/crowded
""",
        },
    },

    # ══════════════════════════════════════════════════════════════════════
    # GROWTH STAGE (Series B+)
    # ══════════════════════════════════════════════════════════════════════
    "late_private": {
        "label": "Growth Stage (Series B+)",
        "philosophy": (
            "At growth stage, PMF is proven. The question shifts to: 'Can this company "
            "scale efficiently and become a market leader?' The evaluation is now heavily "
            "data-driven. You should have real revenue, real margins, and real growth rates. "
            "If you don't have this data, that itself is a red flag at this stage."
        ),

        "company_research": {
            "focus": "GROWTH METRICS AND OPERATIONAL MATURITY",
            "instructions": """
At growth stage, research should focus on proven metrics and scaling signals:

1. **Financial Metrics** (40% — these should exist at this stage):
   - Revenue / ARR with growth rate (YoY and QoQ)
   - Net Dollar Retention (NDR >120% = excellent)
   - Gross margin and trend
   - Burn multiple (net burn / net new ARR) — <1.5x is efficient
   - Rule of 40 score (growth rate + profit margin)

2. **Operational Maturity** (25%):
   - Management team completeness (CFO, VP Sales, VP Eng, etc.)
   - Board composition and governance
   - Organizational structure and hiring velocity
   - International expansion progress

3. **Market Position** (20%):
   - Market share estimate
   - Win rates vs. specific competitors
   - Customer concentration risk (no single customer >10% of revenue)
   - Logo churn and contraction

4. **Strategic Assets** (15%):
   - IP portfolio, patents
   - Data moats, network effects
   - Strategic partnerships
   - Platform/ecosystem lock-in

If key financial metrics are NOT FOUND at this stage, flag it as a significant
information risk. Growth-stage companies should have this data available.
""",
        },

        "market_analysis": {
            "focus": "MARKET LEADERSHIP AND EXPANSION",
            "instructions": """
At growth stage, market analysis should focus on defensibility and expansion:

1. **Market Share Analysis**: What % of SAM does this company own? Growth trajectory?
2. **Competitive Moat Durability**: Will the moat hold at scale? Switching costs analysis.
3. **Expansion Opportunities**: Adjacent markets, international, new products, platform play
4. **Public Comp Analysis**: How do public companies in this space trade?
   - Revenue multiples, growth rates, profitability metrics
   - Direct comparison table with 5-10 public comps

TAM/SAM/SOM should be precise and well-sourced at this stage.
Use real industry reports, not napkin math.
""",
        },

        "financial_modeling": {
            "focus": "FULL FINANCIAL MODEL WITH REAL DATA",
            "instructions": """
At growth stage, build a proper financial model anchored to REAL DATA:

1. **Revenue Model**: Anchored to actual ARR/revenue.
   - Decompose growth: new business + expansion - churn
   - Model each revenue stream separately
   - Include seasonality patterns if visible

2. **Full P&L Model** (5-year, 3 scenarios):
   - Revenue with growth deceleration curve (high growth can't sustain forever)
   - Gross margin trajectory (should be improving at scale)
   - Operating expenses by category (S&M, R&D, G&A)
   - Path to profitability — when does EBITDA turn positive?

3. **Detailed Unit Economics**:
   - CAC by segment and channel with trends
   - LTV by cohort vintage
   - Payback period trends
   - Magic number (net new ARR / prior quarter S&M spend)

4. **Valuation Analysis**:
   - Public comp multiples (EV/Revenue, EV/EBITDA, EV/FCF)
   - Recent private transaction comps
   - DCF sensitivity analysis
   - MOIC and IRR at various entry valuations

5. **Capital Efficiency**:
   - How much capital consumed to reach current scale?
   - Burn multiple trend
   - Revenue per employee

At this stage, if financial data is not available, recommend PASS or
MORE DILIGENCE NEEDED — you cannot make a growth-stage investment blind.
""",
        },

        "risk_assessment": {
            "focus": "SCALING AND COMPETITIVE DURABILITY",
            "instructions": """
At growth stage, risk assessment shifts to scaling and durability:

1. **Competitive Risk** (25%): Can incumbents or well-funded entrants dislodge them?
   - Competitive response from larger players
   - Open-source or commoditization threat
   - Platform risk (dependency on AWS, Salesforce, etc.)

2. **Execution/Scaling Risk** (25%): Can the org scale from 100→1000 people?
   - Management team gaps
   - Culture scaling challenges
   - International execution complexity

3. **Market Risk** (20%): Will the market sustain this growth?
   - Market saturation signals
   - Macro sensitivity
   - Regulatory headwinds

4. **Financial Risk** (20%): Is the business model sustainable?
   - Gross margin sustainability
   - CAC inflation (harder to acquire each incremental customer)
   - Customer concentration
   - Cash flow and capital needs

5. **Exit Risk** (10%): Is there a clear liquidity path?
   - IPO readiness (revenue scale, governance, audited financials)
   - M&A acquirer universe
   - Secondary market liquidity
""",
        },

        "investor_memo": {
            "focus": "DATA-DRIVEN GROWTH THESIS",
            "instructions": """
Growth-stage memo should be heavily quantitative:

1. **Lead with metrics**: ARR, growth rate, NDR, Rule of 40, burn multiple
2. **Market position**: Share, competitive moat, expansion opportunities
3. **Financial model summary**: All 3 scenarios with clear assumptions
4. **Path to profitability**: When and how
5. **Valuation analysis**: Is the price right? Comp-based and DCF
6. **Risks**: Focused on scaling and competitive durability
7. **Recommendation**: Data-driven, with specific valuation sensitivity

The recommendation should include:
- Maximum entry valuation you'd accept
- Required protective terms at this price
- Expected return profile (MOIC, IRR) per scenario
- Comparison to portfolio benchmarks
""",
        },
    },

    # ══════════════════════════════════════════════════════════════════════
    # PUBLIC COMPANY
    # ══════════════════════════════════════════════════════════════════════
    "public": {
        "label": "Public Company",
        "philosophy": (
            "For public companies, extensive financial data is available. The evaluation "
            "is fundamentally a valuation exercise: 'Is this stock mispriced relative to "
            "fundamentals and comps?' Use SEC filings, earnings transcripts, and analyst "
            "estimates as primary data sources."
        ),

        "company_research": {
            "focus": "PUBLIC FILINGS AND ANALYST COVERAGE",
            "instructions": """
For public companies, prioritize official filings and analyst coverage:

1. **SEC Filings**: 10-K, 10-Q, proxy statements, S-1 (if recent IPO)
2. **Earnings History**: Last 4-8 quarters of results, guidance accuracy, beat/miss pattern
3. **Analyst Coverage**: Number of analysts, consensus estimates, price targets
4. **Management Quality**: Track record on guidance, capital allocation, insider transactions
5. **Institutional Ownership**: Top holders, recent buys/sells, activist involvement
6. **Corporate Governance**: Board independence, executive compensation, shareholder rights
""",
        },

        "market_analysis": {
            "focus": "INDUSTRY POSITIONING AND PUBLIC COMPS",
            "instructions": """
For public companies:
1. **Industry analysis**: Porter's Five Forces, industry lifecycle stage
2. **Public comp table**: 10+ comps with: revenue, growth, margins, EV/Revenue, EV/EBITDA, P/E
3. **Market share**: Precise market share data with trends
4. **Secular trends**: Long-term demand drivers, regulatory environment
""",
        },

        "financial_modeling": {
            "focus": "FULL 3-STATEMENT MODEL AND DCF",
            "instructions": """
For public companies, build a complete financial model:

1. **3-Statement Model**: Full P&L, balance sheet, and cash flow statement (5-year)
2. **DCF Valuation**: WACC calculation, terminal value, sensitivity to discount rate and growth
3. **Public Comp Valuation**: EV/Revenue, EV/EBITDA, P/E vs. peer group
4. **Sum-of-Parts**: If applicable (multi-segment businesses)
5. **Scenario Analysis**: Bull/Base/Bear with probability weighting
6. **Implied upside/downside**: Current price vs. intrinsic value per scenario

All data should come from verified public filings. There is NO excuse for
estimated financials on a public company.
""",
        },

        "risk_assessment": {
            "focus": "VALUATION AND MACRO RISK",
            "instructions": """
For public companies:
1. **Valuation Risk** (30%): Is the stock overvalued? What's priced in?
2. **Competitive Risk** (20%): Market share trends, competitive dynamics
3. **Execution Risk** (20%): Management track record, guidance reliability
4. **Macro Risk** (15%): Interest rate sensitivity, economic cycle, currency
5. **Regulatory Risk** (15%): Antitrust, data privacy, industry-specific regulation
""",
        },

        "investor_memo": {
            "focus": "VALUATION-DRIVEN THESIS",
            "instructions": """
Public company memo should be valuation-centric:
1. **Investment thesis**: Why is the market wrong about this stock?
2. **Catalyst**: What will cause the market to re-rate the stock?
3. **Valuation**: Intrinsic value vs. current price, margin of safety
4. **Risks**: What could cause permanent capital loss?
5. **Position sizing**: Recommended allocation based on conviction and risk
6. **Timeline**: Expected catalyst timeline
""",
        },
    },
}

# "unknown" defaults to early_stage
FRAMEWORKS["unknown"] = FRAMEWORKS["early_stage"]


def get_evaluation_framework(company_type: str) -> dict:
    """Get the evaluation framework for a given company type."""
    return FRAMEWORKS.get(company_type, FRAMEWORKS["early_stage"])


def build_framework_block(company_type: str) -> str:
    """Generate the EVALUATION FRAMEWORK block injected into downstream prompts.

    This block tells each agent HOW to evaluate based on the company stage.
    It gets injected alongside the data profile block.
    """
    fw = get_evaluation_framework(company_type)

    lines = []
    lines.append("=" * 70)
    lines.append(f"EVALUATION FRAMEWORK: {fw['label']}")
    lines.append("=" * 70)
    lines.append(fw["philosophy"])
    lines.append("=" * 70)

    return "\n".join(lines)


def build_stage_instructions(company_type: str, stage_key: str) -> str:
    """Get stage-specific instructions for a given company type and pipeline stage.

    Args:
        company_type: One of pre_product, early_stage, late_private, public, unknown
        stage_key: One of company_research, market_analysis, financial_modeling,
                  risk_assessment, investor_memo

    Returns:
        Stage-specific instruction text to inject into the build_prompt.
    """
    fw = get_evaluation_framework(company_type)
    stage_fw = fw.get(stage_key, {})

    if not stage_fw:
        return ""

    lines = []
    lines.append("")
    lines.append("-" * 50)
    lines.append(f"STAGE-SPECIFIC GUIDANCE: {stage_fw.get('focus', 'GENERAL')}")
    lines.append(f"(Company classified as: {fw['label']})")
    lines.append("-" * 50)
    lines.append(stage_fw.get("instructions", ""))
    lines.append("-" * 50)

    return "\n".join(lines)
