"""Chart generation tool using matplotlib for financial visualizations."""

import json
import os
import re
import base64
from io import BytesIO

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker


def extract_json_from_text(text: str) -> dict | None:
    """Extract a JSON block from agent text output."""
    pattern = r"```json\s*(.*?)\s*```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            return None
    return None


def generate_revenue_chart(financial_data: dict, output_dir: str) -> str | None:
    """Generate a revenue projections chart (Bear/Base/Bull) and return the file path."""
    revenue = financial_data.get("revenue_projections")
    if not revenue:
        return None

    years = ["Year 1", "Year 2", "Year 3", "Year 4", "Year 5"]
    year_keys = ["year1", "year2", "year3", "year4", "year5"]

    fig, ax = plt.subplots(figsize=(10, 6))

    bear_vals = [revenue["bear"].get(k, 0) for k in year_keys]
    base_vals = [revenue["base"].get(k, 0) for k in year_keys]
    bull_vals = [revenue["bull"].get(k, 0) for k in year_keys]

    ax.plot(years, bear_vals, "o-", color="#e53e3e", linewidth=2.5, markersize=8, label="Bear Case")
    ax.plot(years, base_vals, "o-", color="#3182ce", linewidth=2.5, markersize=8, label="Base Case")
    ax.plot(years, bull_vals, "o-", color="#38a169", linewidth=2.5, markersize=8, label="Bull Case")

    ax.fill_between(years, bear_vals, bull_vals, alpha=0.1, color="#3182ce")

    ax.set_title("Revenue Projections (Bear / Base / Bull)", fontsize=16, fontweight="bold", pad=20)
    ax.set_ylabel("Revenue ($M)", fontsize=12)
    ax.set_xlabel("", fontsize=12)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f"${x:,.0f}M"))
    ax.legend(fontsize=11, loc="upper left")
    ax.grid(True, alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()

    filepath = os.path.join(output_dir, "revenue_projections.png")
    fig.savefig(filepath, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return filepath


def generate_ebitda_chart(financial_data: dict, output_dir: str) -> str | None:
    """Generate an EBITDA projections chart and return the file path."""
    ebitda = financial_data.get("ebitda_projections")
    if not ebitda:
        return None

    years = ["Year 1", "Year 2", "Year 3", "Year 4", "Year 5"]
    year_keys = ["year1", "year2", "year3", "year4", "year5"]

    fig, ax = plt.subplots(figsize=(10, 6))

    bear_vals = [ebitda["bear"].get(k, 0) for k in year_keys]
    base_vals = [ebitda["base"].get(k, 0) for k in year_keys]
    bull_vals = [ebitda["bull"].get(k, 0) for k in year_keys]

    x_pos = range(len(years))
    width = 0.25

    bars_bear = ax.bar([p - width for p in x_pos], bear_vals, width, label="Bear", color="#e53e3e", alpha=0.85)
    bars_base = ax.bar(x_pos, base_vals, width, label="Base", color="#3182ce", alpha=0.85)
    bars_bull = ax.bar([p + width for p in x_pos], bull_vals, width, label="Bull", color="#38a169", alpha=0.85)

    ax.set_title("EBITDA Projections (Bear / Base / Bull)", fontsize=16, fontweight="bold", pad=20)
    ax.set_ylabel("EBITDA ($M)", fontsize=12)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(years)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f"${x:,.0f}M"))
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3, axis="y")
    ax.axhline(y=0, color="black", linewidth=0.8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()

    filepath = os.path.join(output_dir, "ebitda_projections.png")
    fig.savefig(filepath, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return filepath


def generate_unit_economics_chart(financial_data: dict, output_dir: str) -> str | None:
    """Generate a unit economics summary chart."""
    ue = financial_data.get("unit_economics")
    if not ue:
        return None

    fig, axes = plt.subplots(1, 3, figsize=(14, 5))

    # LTV vs CAC
    ax1 = axes[0]
    vals = [ue.get("cac", 0), ue.get("ltv", 0)]
    colors = ["#e53e3e", "#38a169"]
    bars = ax1.bar(["CAC", "LTV"], vals, color=colors, width=0.5, alpha=0.85)
    ax1.set_title("LTV vs CAC", fontsize=13, fontweight="bold")
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f"${x:,.0f}"))
    for bar, val in zip(bars, vals):
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(vals) * 0.02,
                 f"${val:,.0f}", ha="center", fontsize=11, fontweight="bold")

    # LTV/CAC Ratio
    ax2 = axes[1]
    ratio = ue.get("ltv_cac_ratio", 0)
    color = "#38a169" if ratio >= 3 else "#ecc94b" if ratio >= 1 else "#e53e3e"
    ax2.barh(["LTV/CAC"], [ratio], color=color, height=0.4, alpha=0.85)
    ax2.axvline(x=3, color="#38a169", linestyle="--", alpha=0.7, label="Target (3x)")
    ax2.set_title("LTV/CAC Ratio", fontsize=13, fontweight="bold")
    ax2.legend(fontsize=10)
    ax2.set_xlim(0, max(ratio * 1.3, 5))

    # Gross Margin
    ax3 = axes[2]
    gm = ue.get("gross_margin_pct", 0)
    color = "#38a169" if gm >= 70 else "#ecc94b" if gm >= 50 else "#e53e3e"
    ax3.barh(["Gross Margin"], [gm], color=color, height=0.4, alpha=0.85)
    ax3.set_xlim(0, 100)
    ax3.set_title("Gross Margin %", fontsize=13, fontweight="bold")
    ax3.text(gm + 1, 0, f"{gm:.0f}%", va="center", fontsize=13, fontweight="bold")

    for ax in axes:
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    plt.tight_layout()

    filepath = os.path.join(output_dir, "unit_economics.png")
    fig.savefig(filepath, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return filepath


def generate_all_charts(financial_text: str, output_dir: str) -> dict:
    """Parse financial data from agent output and generate all charts.

    Returns dict of chart_name -> file_path for generated charts.
    """
    os.makedirs(output_dir, exist_ok=True)
    financial_data = extract_json_from_text(financial_text)

    if not financial_data:
        return {}

    charts = {}

    revenue_path = generate_revenue_chart(financial_data, output_dir)
    if revenue_path:
        charts["revenue_projections"] = revenue_path

    ebitda_path = generate_ebitda_chart(financial_data, output_dir)
    if ebitda_path:
        charts["ebitda_projections"] = ebitda_path

    ue_path = generate_unit_economics_chart(financial_data, output_dir)
    if ue_path:
        charts["unit_economics"] = ue_path

    return charts


def chart_to_base64(filepath: str) -> str:
    """Convert a chart image to base64 for embedding in HTML."""
    with open(filepath, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")
