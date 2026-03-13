"""SEC EDGAR API client — fetch 10-K, 10-Q, 8-K filings."""

import json

import httpx

from config import settings
from db.models import FilingType

# SEC EDGAR requires a User-Agent identifying the requester
HEADERS = {"User-Agent": settings.sec_user_agent, "Accept": "application/json"}
BASE_URL = "https://efts.sec.gov/LATEST"
SUBMISSIONS_URL = "https://data.sec.gov/submissions"


async def get_cik(ticker: str) -> str:
    """Resolve a ticker symbol to a CIK (Central Index Key)."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE_URL}/search-index?q=%22{ticker}%22&dateRange=custom&startdt=2020-01-01&forms=10-K",
            headers=HEADERS,
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("hits", {}).get("hits"):
            raise ValueError(f"No CIK found for ticker {ticker}")

        # Extract CIK from first hit
        first_hit = data["hits"]["hits"][0]["_source"]
        return str(first_hit.get("entity_id", first_hit.get("file_num", ""))).split("-")[0]


async def search_filings(
    ticker: str,
    filing_type: FilingType = FilingType.TEN_K,
    count: int = 5,
) -> list[dict]:
    """Search SEC EDGAR full-text search for filings.

    Returns list of filing metadata with download URLs.
    """
    form_type = filing_type.value
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE_URL}/search-index",
            params={
                "q": f'"{ticker}"',
                "forms": form_type,
                "dateRange": "custom",
                "startdt": "2020-01-01",
            },
            headers=HEADERS,
        )
        resp.raise_for_status()
        data = resp.json()

    filings = []
    for hit in data.get("hits", {}).get("hits", [])[:count]:
        source = hit["_source"]
        filings.append(
            {
                "accession_number": source.get("file_num", ""),
                "filing_type": form_type,
                "filed_date": source.get("file_date", ""),
                "document_url": f"https://www.sec.gov/Archives/edgar/data/{source.get('entity_id', '')}/{source.get('file_num', '').replace('-', '')}/{source.get('file_name', '')}",
                "title": source.get("display_names", [ticker])[0] if source.get("display_names") else ticker,
                "ticker": ticker.upper(),
            }
        )

    return filings


async def fetch_filing_content(url: str) -> str:
    """Download the raw HTML/text content of a filing."""
    async with httpx.AsyncClient(follow_redirects=True) as client:
        resp = await client.get(url, headers=HEADERS, timeout=60.0)
        resp.raise_for_status()
        return resp.text
