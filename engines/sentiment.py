"""FinBERT sentiment analysis with DeepSeek LLM fallback."""

from datetime import datetime, timezone

from openai import AsyncOpenAI

from config import settings
from db.models import SentimentAnalysis, SentimentLabel, SentimentResult
from observability.langfuse_setup import trace_tool

_finbert_pipeline = None
_HAS_TRANSFORMERS = False

try:
    from transformers import pipeline as _hf_pipeline

    _HAS_TRANSFORMERS = True
except ImportError:
    pass


def _get_finbert():
    """Lazy-load FinBERT model to avoid startup cost."""
    global _finbert_pipeline
    if _finbert_pipeline is None:
        if not _HAS_TRANSFORMERS:
            return None
        _finbert_pipeline = _hf_pipeline(
            "sentiment-analysis",
            model="ProsusAI/finbert",
            tokenizer="ProsusAI/finbert",
            top_k=None,
        )
    return _finbert_pipeline


def _finbert_analyze(text: str) -> SentimentResult:
    """Run FinBERT on a single text."""
    pipe = _get_finbert()
    output = pipe(text[:512])  # FinBERT max 512 tokens
    results = output[0] if isinstance(output[0], list) else output

    best = max(results, key=lambda x: x["score"])
    label_map = {
        "positive": SentimentLabel.POSITIVE,
        "negative": SentimentLabel.NEGATIVE,
        "neutral": SentimentLabel.NEUTRAL,
    }

    return SentimentResult(
        text=text[:200],
        label=label_map.get(best["label"], SentimentLabel.NEUTRAL),
        score=best["score"],
        model="finbert",
    )


async def _deepseek_analyze(text: str) -> SentimentResult:
    """Fallback: use DeepSeek LLM for sentiment analysis when FinBERT is unavailable."""
    client = AsyncOpenAI(api_key=settings.deepseek_api_key, base_url=settings.deepseek_base_url)

    response = await client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a financial sentiment classifier. "
                    "Classify the following text as exactly one of: positive, negative, neutral. "
                    "Respond with ONLY a JSON object: {\"label\": \"...\", \"score\": 0.0-1.0}"
                ),
            },
            {"role": "user", "content": text[:1000]},
        ],
        temperature=0.1,
        max_tokens=50,
    )

    import json

    raw = response.choices[0].message.content or '{"label":"neutral","score":0.5}'
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = {"label": "neutral", "score": 0.5}

    label_map = {
        "positive": SentimentLabel.POSITIVE,
        "negative": SentimentLabel.NEGATIVE,
        "neutral": SentimentLabel.NEUTRAL,
    }

    return SentimentResult(
        text=text[:200],
        label=label_map.get(parsed.get("label", "neutral"), SentimentLabel.NEUTRAL),
        score=float(parsed.get("score", 0.5)),
        model="deepseek",
    )


@trace_tool("analyze_sentiment")
async def analyze_sentiment(ticker: str, texts: list[str]) -> SentimentAnalysis:
    """Analyze sentiment using FinBERT (preferred) or DeepSeek LLM (fallback).

    Each text is scored independently, then aggregated into an overall sentiment.
    """
    use_finbert = _get_finbert() is not None

    if use_finbert:
        results = [_finbert_analyze(t) for t in texts]
    else:
        results = [await _deepseek_analyze(t) for t in texts]

    # Aggregate: weighted average of sentiment scores
    sentiment_scores = {"positive": 0.0, "negative": 0.0, "neutral": 0.0}
    for r in results:
        sentiment_scores[r.label.value] += r.score

    total = sum(sentiment_scores.values()) or 1
    for key in sentiment_scores:
        sentiment_scores[key] /= total

    overall_label = max(sentiment_scores, key=lambda k: sentiment_scores[k])
    overall_score = sentiment_scores[overall_label]

    return SentimentAnalysis(
        ticker=ticker.upper(),
        results=results,
        overall_sentiment=SentimentLabel(overall_label),
        overall_score=overall_score,
        analyzed_at=datetime.now(timezone.utc),
    )
