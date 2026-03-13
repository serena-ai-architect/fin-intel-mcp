"""Server-Sent Events (SSE) streaming for real-time analysis results."""

import json
from typing import Any, AsyncGenerator


async def format_sse_event(
    event_type: str, data: Any, event_id: str | None = None
) -> str:
    """Format a single SSE event string."""
    lines = []
    if event_id:
        lines.append(f"id: {event_id}")
    lines.append(f"event: {event_type}")
    if isinstance(data, (dict, list)):
        lines.append(f"data: {json.dumps(data, default=str)}")
    else:
        lines.append(f"data: {data}")
    lines.append("")
    lines.append("")
    return "\n".join(lines)


async def analysis_stream(
    ticker: str,
) -> AsyncGenerator[str, None]:
    """Stream technical + sentiment analysis results as SSE events.

    Event types:
    - technical_start / technical_result
    - sentiment_start / sentiment_result
    - complete
    - error
    """
    from engines.technical import get_technical_signals

    # Phase 1: Technical analysis
    yield await format_sse_event("technical_start", {"ticker": ticker, "status": "analyzing"})

    try:
        tech_result = await get_technical_signals(ticker)
        yield await format_sse_event("technical_result", tech_result.model_dump())
    except Exception as e:
        yield await format_sse_event("error", {"phase": "technical", "error": str(e)})

    # Phase 2: Sentiment (placeholder — needs texts from caller in real usage)
    yield await format_sse_event("sentiment_start", {"ticker": ticker, "status": "analyzing"})
    yield await format_sse_event(
        "sentiment_result", {"ticker": ticker, "note": "Provide texts via analyze_sentiment tool"}
    )

    # Done
    yield await format_sse_event("complete", {"ticker": ticker, "status": "done"})
