"""Tests for SEC EDGAR ingestion — fetches real data from SEC."""

import pytest

from ingestion.parser import clean_filing_text, parse_html_to_text
from ingestion.sec_edgar import search_filings
from db.models import FilingType


@pytest.mark.asyncio
async def test_search_filings_nvda():
    """Test that we can find NVDA 10-K filings on EDGAR."""
    filings = await search_filings("NVDA", FilingType.TEN_K, count=3)

    assert len(filings) > 0
    filing = filings[0]
    assert filing["ticker"] == "NVDA"
    assert filing["filing_type"] == "10-K"
    assert "document_url" in filing
    assert "accession_number" in filing
    assert filing["filed_date"] >= "2020"  # Should be recent


@pytest.mark.asyncio
async def test_search_filings_aapl_10q():
    """Test 10-Q search for AAPL."""
    filings = await search_filings("AAPL", FilingType.TEN_Q, count=2)

    assert len(filings) > 0
    assert filings[0]["filing_type"] == "10-Q"


class TestParser:
    def test_parse_simple_html(self):
        """Test basic HTML parsing."""
        html = "<html><body><p>Revenue was $60.9 billion.</p><p>Net income grew 200%.</p></body></html>"
        text = parse_html_to_text(html)
        assert "Revenue" in text
        assert "60.9 billion" in text

    def test_parse_html_strips_scripts(self):
        """Test that script tags are removed."""
        html = "<p>Real content</p><script>alert('xss')</script><p>More content</p>"
        text = parse_html_to_text(html)
        assert "Real content" in text
        assert "alert" not in text

    def test_clean_filing_text_collapses_whitespace(self):
        """Test whitespace normalization."""
        text = "Section 1\n\n\n\n\n\n\n\nSection 2"
        cleaned = clean_filing_text(text)
        assert "\n\n\n\n" not in cleaned
        assert "Section 1" in cleaned
        assert "Section 2" in cleaned

    def test_parse_empty_html(self):
        """Empty HTML should return empty string."""
        text = parse_html_to_text("")
        assert text == ""
