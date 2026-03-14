"""Document parsing — convert raw SEC HTML/text into clean text for chunking."""

import re


def parse_html_to_text(html_content: str) -> str:
    """Extract clean text from SEC filing HTML.

    Uses a lightweight approach first; falls back to unstructured if available.
    """
    if not html_content:
        return ""

    try:
        from unstructured.partition.html import partition_html

        elements = partition_html(text=html_content)
        return "\n\n".join(str(el) for el in elements if str(el).strip())
    except ImportError:
        return _basic_html_strip(html_content)


def _basic_html_strip(html: str) -> str:
    """Regex-based HTML to text conversion optimized for SEC filings."""
    # Remove XBRL/XML processing instructions and hidden elements
    text = re.sub(r"<\?xml[^>]*\?>", "", html)
    text = re.sub(r"<ix:[^>]*>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"</ix:[^>]*>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<xbrli?:[^>]*>.*?</xbrli?:[^>]*>", " ", text, flags=re.DOTALL | re.IGNORECASE)

    # Remove script/style/head blocks
    text = re.sub(r"<(script|style|head)[^>]*>.*?</\1>", "", text, flags=re.DOTALL | re.IGNORECASE)

    # Remove hidden div/span elements (display:none)
    text = re.sub(r'<[^>]+display\s*:\s*none[^>]*>.*?</[^>]+>', "", text, flags=re.DOTALL | re.IGNORECASE)

    # Remove HTML tags but preserve block-level line breaks
    text = re.sub(r"</?(p|div|br|h[1-6]|tr|li|section|article)[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</?t[dh][^>]*>", " | ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)

    # Decode common entities
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&nbsp;", " ").replace("&quot;", '"').replace("&#8217;", "'")
    text = text.replace("&mdash;", "—").replace("&ndash;", "–")
    text = re.sub(r"&#\d+;", " ", text)  # Remove remaining numeric entities

    # Collapse whitespace within lines
    text = re.sub(r"[ \t]+", " ", text)
    # Collapse excessive newlines
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)

    return text.strip()


def clean_filing_text(text: str) -> str:
    """Clean parsed filing text: remove XBRL preamble, boilerplate, normalize whitespace."""
    # Remove XBRL context/namespace blocks that leak through as text
    # These look like: "iso4217:USD xbrli:shares nvda:segment 0001045810 2025-01-27..."
    text = re.sub(
        r"(?:[\w-]+:[\w-]+\s+)+(?:\d{10}\s+\d{4}-\d{2}-\d{2}\s*)+",
        "",
        text,
    )

    # Remove lines that are mostly CIK numbers, dates, or XBRL identifiers
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            cleaned_lines.append("")
            continue
        # Skip lines that are just numbers/dates/identifiers
        if re.match(r"^[\d\s:.\-/]+$", stripped):
            continue
        # Skip lines that look like XBRL metadata
        if re.match(r"^(?:[\w-]+:[\w-]+\s*)+$", stripped):
            continue
        # Skip very short lines that are just codes
        if len(stripped) < 5 and not stripped[0].isalpha():
            continue
        cleaned_lines.append(line)

    text = "\n".join(cleaned_lines)

    # Remove common SEC boilerplate
    boilerplate_patterns = [
        r"UNITED STATES\s+SECURITIES AND EXCHANGE COMMISSION.*?(?=PART|Table of Contents|ITEM)",
        r"Table of Contents\s*\n",
    ]
    for pattern in boilerplate_patterns:
        text = re.sub(pattern, "", text, flags=re.DOTALL | re.IGNORECASE)

    # Collapse excessive newlines
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text.strip()
