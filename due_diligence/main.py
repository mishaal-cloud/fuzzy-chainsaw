"""CLI entry point for the AI Due Diligence Agent Tool."""

import sys
import os

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from due_diligence.config import ANTHROPIC_API_KEY, OUTPUT_DIR
from due_diligence.orchestrator import DueDiligencePipeline

console = Console()

BANNER = """
[bold cyan]╔═══════════════════════════════════════════════════════════╗
║          AI Due Diligence Agent Tool                      ║
║          Powered by Claude + Anthropic API                ║
╚═══════════════════════════════════════════════════════════╝[/bold cyan]

[dim]A 7-agent sequential pipeline that researches any startup,
analyzes the market, builds financial models, assesses risks,
and generates professional investment reports.[/dim]
"""

EXAMPLES = """[bold]Example queries:[/bold]
  • Analyze https://agno.com for Series A investment of $30-50M
  • Due diligence on Stripe for a growth-stage investment
  • Research Anthropic for a $500M Series D evaluation
  • Analyze Cursor (AI code editor) for seed investment of $5-10M
"""


def validate_environment():
    """Check that required environment variables are set."""
    if not ANTHROPIC_API_KEY:
        console.print("[bold red]Error:[/bold red] ANTHROPIC_API_KEY is not set.")
        console.print()
        console.print("Set it in your environment or create a .env file:")
        console.print("  export ANTHROPIC_API_KEY=sk-ant-xxxxx")
        console.print("  # or")
        console.print("  echo 'ANTHROPIC_API_KEY=sk-ant-xxxxx' > due_diligence/.env")
        sys.exit(1)


def main():
    console.print(BANNER)

    validate_environment()

    # Get query from command line args or interactive prompt
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        console.print(EXAMPLES)
        query = Prompt.ask("\n[bold cyan]Enter your analysis query[/bold cyan]")

    if not query.strip():
        console.print("[bold red]Error:[/bold red] Please provide an analysis query.")
        sys.exit(1)

    # Run the pipeline
    pipeline = DueDiligencePipeline(output_dir=OUTPUT_DIR)

    try:
        results = pipeline.run(query.strip())
    except KeyboardInterrupt:
        console.print("\n[yellow]Analysis interrupted by user.[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]Error during analysis:[/bold red] {e}")
        console.print("[dim]Check your API key and network connection.[/dim]")
        raise

    # Final output
    console.print()
    console.print("[bold]To view the report, open the HTML file in your browser:[/bold]")
    for f in results["files"]:
        if f.endswith(".html"):
            console.print(f"  [cyan]file://{os.path.abspath(f)}[/cyan]")


if __name__ == "__main__":
    main()
