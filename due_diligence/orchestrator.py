"""Sequential pipeline orchestrator for the due diligence agent team."""

import time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from due_diligence.agents.company_research import create_company_research_agent, build_prompt as company_prompt
from due_diligence.agents.market_analysis import create_market_analysis_agent, build_prompt as market_prompt
from due_diligence.agents.financial_modeling import create_financial_modeling_agent, build_prompt as financial_prompt
from due_diligence.agents.risk_assessment import create_risk_assessment_agent, build_prompt as risk_prompt
from due_diligence.agents.investor_memo import create_investor_memo_agent, build_prompt as memo_prompt
from due_diligence.agents.report_generator import create_report_generator_agent, build_prompt as report_prompt
from due_diligence.agents.infographic import create_infographic_agent, build_prompt as infographic_prompt
from due_diligence.tools.chart_generator import generate_all_charts
from due_diligence.tools.file_writer import save_report, save_text_output
from due_diligence.config import OUTPUT_DIR

console = Console()


class DueDiligencePipeline:
    """Orchestrates the 7-stage due diligence analysis pipeline.

    Each agent runs sequentially, with outputs from prior stages
    passed to subsequent agents via a shared state dictionary.
    """

    def __init__(self, output_dir: str | None = None):
        self.output_dir = output_dir or OUTPUT_DIR
        self.state: dict[str, str] = {}
        self.generated_files: list[str] = []

    def run(self, query: str) -> dict:
        """Run the full due diligence pipeline.

        Args:
            query: The user's input, e.g. "Analyze https://agno.com for Series A investment of $30-50M"

        Returns:
            Dict with all outputs and file paths.
        """
        start_time = time.time()

        console.print()
        console.print(Panel(
            f"[bold white]{query}[/bold white]",
            title="[bold cyan]AI Due Diligence Analysis[/bold cyan]",
            subtitle="7-Stage Investment Pipeline",
            style="bold blue",
            padding=(1, 2),
        ))
        console.print()

        # Stage 1: Company Research
        console.print("[bold]Stage 1/7[/bold] — Company Research")
        agent = create_company_research_agent()
        prompt = company_prompt(query)
        self.state["company_research"] = agent.run(prompt, self.state)
        console.print()

        # Stage 2: Market Analysis
        console.print("[bold]Stage 2/7[/bold] — Market Analysis")
        agent = create_market_analysis_agent()
        prompt = market_prompt(query, self.state["company_research"])
        self.state["market_analysis"] = agent.run(prompt, self.state)
        console.print()

        # Stage 3: Financial Modeling
        console.print("[bold]Stage 3/7[/bold] — Financial Modeling")
        agent = create_financial_modeling_agent()
        prompt = financial_prompt(query, self.state["company_research"], self.state["market_analysis"])
        self.state["financial_modeling"] = agent.run(prompt, self.state)

        # Generate charts from financial data
        charts = generate_all_charts(self.state["financial_modeling"], self.output_dir)
        self.state["charts"] = str(charts)
        for name, path in charts.items():
            console.print(f"  [green]✓[/green] Chart generated: {path}")
            self.generated_files.append(path)
        console.print()

        # Stage 4: Risk Assessment
        console.print("[bold]Stage 4/7[/bold] — Risk Assessment")
        agent = create_risk_assessment_agent()
        prompt = risk_prompt(
            query,
            self.state["company_research"],
            self.state["market_analysis"],
            self.state["financial_modeling"],
        )
        self.state["risk_assessment"] = agent.run(prompt, self.state)
        console.print()

        # Stage 5: Investor Memo
        console.print("[bold]Stage 5/7[/bold] — Investor Memo")
        agent = create_investor_memo_agent()
        prompt = memo_prompt(
            query,
            self.state["company_research"],
            self.state["market_analysis"],
            self.state["financial_modeling"],
            self.state["risk_assessment"],
        )
        self.state["investor_memo"] = agent.run(prompt, self.state)

        memo_path = save_text_output(self.state["investor_memo"], query, self.output_dir, "memo")
        console.print(f"  [green]✓[/green] Memo saved: {memo_path}")
        self.generated_files.append(memo_path)
        console.print()

        # Stage 6: HTML Report
        console.print("[bold]Stage 6/7[/bold] — Report Generation")
        agent = create_report_generator_agent()
        prompt = report_prompt(
            query,
            self.state["company_research"],
            self.state["market_analysis"],
            self.state["financial_modeling"],
            self.state["risk_assessment"],
            self.state["investor_memo"],
        )
        self.state["report"] = agent.run(prompt, self.state)

        report_path = save_report(self.state["report"], query, self.output_dir, "report")
        console.print(f"  [green]✓[/green] Report saved: {report_path}")
        self.generated_files.append(report_path)
        console.print()

        # Stage 7: Infographic
        console.print("[bold]Stage 7/7[/bold] — Infographic Generation")
        agent = create_infographic_agent()
        prompt = infographic_prompt(
            query,
            self.state["company_research"],
            self.state["market_analysis"],
            self.state["financial_modeling"],
            self.state["risk_assessment"],
            self.state["investor_memo"],
        )
        self.state["infographic"] = agent.run(prompt, self.state)

        infographic_path = save_report(self.state["infographic"], query, self.output_dir, "infographic")
        console.print(f"  [green]✓[/green] Infographic saved: {infographic_path}")
        self.generated_files.append(infographic_path)
        console.print()

        # Summary
        elapsed = time.time() - start_time
        self._print_summary(query, elapsed)

        return {
            "state": self.state,
            "files": self.generated_files,
            "elapsed_seconds": elapsed,
        }

    def _print_summary(self, query: str, elapsed: float):
        """Print a summary table of all generated outputs."""
        table = Table(title="Generated Outputs", style="cyan")
        table.add_column("Type", style="bold")
        table.add_column("File", style="green")

        for filepath in self.generated_files:
            filename = filepath.split("/")[-1]
            if "memo" in filename:
                table.add_row("Investor Memo", filepath)
            elif "report" in filename:
                table.add_row("HTML Report", filepath)
            elif "infographic" in filename:
                table.add_row("Infographic", filepath)
            elif "revenue" in filename:
                table.add_row("Revenue Chart", filepath)
            elif "ebitda" in filename:
                table.add_row("EBITDA Chart", filepath)
            elif "unit_economics" in filename:
                table.add_row("Unit Economics Chart", filepath)
            else:
                table.add_row("Output", filepath)

        console.print(table)
        console.print()
        console.print(Panel(
            f"[bold green]Analysis complete![/bold green]\n"
            f"Time: {elapsed:.1f}s | Files: {len(self.generated_files)} | Agents: 7",
            style="green",
        ))
