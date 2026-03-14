"""SEC EDGAR API client — fetch 10-K, 10-Q, 8-K filings.

Uses the company submissions API (data.sec.gov) for reliable, recent filing data.
"""

import httpx

from config import settings
from db.models import FilingType

HEADERS = {"User-Agent": settings.sec_user_agent, "Accept": "application/json"}

# Ticker → CIK mapping cache
_CIK_CACHE: dict[str, str] = {}


async def _resolve_cik(ticker: str) -> str:
    """Resolve ticker to 10-digit zero-padded CIK using SEC company tickers file."""
    ticker_upper = ticker.upper()
    if ticker_upper in _CIK_CACHE:
        return _CIK_CACHE[ticker_upper]

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://www.sec.gov/files/company_tickers.json",
            headers=HEADERS,
            timeout=15.0,
        )
        resp.raise_for_status()
        data = resp.json()

    for entry in data.values():
        if entry.get("ticker", "").upper() == ticker_upper:
            cik = str(entry["cik_str"]).zfill(10)
            _CIK_CACHE[ticker_upper] = cik
            return cik

    raise ValueError(f"Ticker '{ticker}' not found in SEC EDGAR")


async def search_filings(
    ticker: str,
    filing_type: FilingType = FilingType.TEN_K,
    count: int = 5,
) -> list[dict]:
    """Get recent filings for a ticker from SEC EDGAR submissions API.

    Returns list of filing metadata sorted by date (most recent first).
    """
    cik = await _resolve_cik(ticker)
    form_type = filing_type.value

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"https://data.sec.gov/submissions/CIK{cik}.json",
            headers=HEADERS,
            timeout=15.0,
        )
        resp.raise_for_status()
        data = resp.json()

    recent = data.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    accessions = recent.get("accessionNumber", [])
    primary_docs = recent.get("primaryDocument", [])
    descriptions = recent.get("primaryDocDescription", [])

    filings = []
    cik_raw = cik.lstrip("0")

    for i, form in enumerate(forms):
        if form != form_type:
            continue

        adsh = accessions[i]
        adsh_no_dashes = adsh.replace("-", "")
        primary_doc = primary_docs[i] if i < len(primary_docs) else ""

        # Direct URL to the primary document (the actual 10-K HTML)
        doc_url = f"https://www.sec.gov/Archives/edgar/data/{cik_raw}/{adsh_no_dashes}/{primary_doc}"

        filings.append(
            {
                "accession_number": adsh,
                "cik": cik_raw,
                "filing_type": form_type,
                "filed_date": dates[i] if i < len(dates) else "",
                "document_url": doc_url,
                "primary_doc": primary_doc,
                "description": descriptions[i] if i < len(descriptions) else "",
                "title": f"{ticker.upper()} {form_type} {dates[i] if i < len(dates) else ''}",
                "ticker": ticker.upper(),
            }
        )

        if len(filings) >= count:
            break

    return filings


async def fetch_filing_content(url: str) -> str:
    """Download the raw HTML/text content of a filing."""
    async with httpx.AsyncClient(follow_redirects=True) as client:
        resp = await client.get(url, headers=HEADERS, timeout=60.0)
        resp.raise_for_status()
        return resp.text
