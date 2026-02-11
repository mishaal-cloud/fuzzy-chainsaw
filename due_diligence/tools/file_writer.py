"""File output utilities for saving reports and artifacts."""

import os
import re
from datetime import datetime


def sanitize_filename(name: str) -> str:
    """Convert a company name or query into a safe filename."""
    # Extract likely company name from query
    name = name.strip()
    # Remove URLs
    name = re.sub(r"https?://\S+", "", name)
    # Remove common investment phrases
    for phrase in ["analyze", "analyse", "for series", "investment of", "series a", "series b",
                   "series c", "seed", "pre-seed", "investment", "due diligence"]:
        name = re.sub(re.escape(phrase), "", name, flags=re.IGNORECASE)
    # Clean up
    name = re.sub(r"[^\w\s-]", "", name).strip()
    name = re.sub(r"\s+", "_", name)
    name = name.strip("_").lower()
    return name or "analysis"


def save_report(html_content: str, query: str, output_dir: str, suffix: str = "report") -> str:
    """Save an HTML report to the output directory.

    Returns the file path.
    """
    os.makedirs(output_dir, exist_ok=True)
    company = sanitize_filename(query)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{company}_{suffix}_{timestamp}.html"
    filepath = os.path.join(output_dir, filename)

    # Extract HTML from the response (agent might include markdown fences)
    html = extract_html(html_content)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    return filepath


def extract_html(text: str) -> str:
    """Extract HTML content from agent output, handling markdown code fences."""
    # Try to find HTML within code fences
    pattern = r"```html\s*(.*?)\s*```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1)

    # Try to find raw HTML (starts with <!DOCTYPE or <html)
    pattern = r"(<!DOCTYPE html.*?</html>)"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1)

    # Fallback: return the full text
    return text


def save_text_output(text: str, query: str, output_dir: str, suffix: str = "memo") -> str:
    """Save a text output (memo, analysis) to a file."""
    os.makedirs(output_dir, exist_ok=True)
    company = sanitize_filename(query)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{company}_{suffix}_{timestamp}.md"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(text)

    return filepath
