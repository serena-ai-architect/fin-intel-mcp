"""Document parsing — convert raw SEC HTML/text into clean text for chunking."""

import re


def parse_html_to_text(html_content: str) -> str:
    """Extract clean text from SEC filing HTML.

    Uses a lightweight approach first; falls back to unstructured if available.
    """
    try:
        from unstructured.partition.html import partition_html

        elements = partition_html(text=html_content)
        return "\n\n".join(str(el) for el in elements if str(el).strip())
    except ImportError:
        # Fallback: basic HTML tag stripping
        return _basic_html_strip(html_content)


def _basic_html_strip(html: str) -> str:
    """Simple regex-based HTML to text conversion."""
    # Remove script/style blocks
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Decode common entities
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&nbsp;", " ").replace("&quot;", '"')
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    # Restore paragraph breaks
    text = re.sub(r"\s{3,}", "\n\n", text)
    return text


def clean_filing_text(text: str) -> str:
    """Clean parsed filing text: remove boilerplate, normalize whitespace."""
    # Remove common SEC boilerplate patterns
    boilerplate_patterns = [
        r"UNITED STATES\s+SECURITIES AND EXCHANGE COMMISSION.*?(?=PART|Table of Contents|ITEM)",
        r"Table of Contents\s*\n",
    ]
    for pattern in boilerplate_patterns:
        text = re.sub(pattern, "", text, flags=re.DOTALL | re.IGNORECASE)

    # Collapse excessive newlines
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text.strip()
