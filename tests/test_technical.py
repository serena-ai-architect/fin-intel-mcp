"""Tests for the technical analysis engine — uses live yfinance data."""

import pytest

from db.models import SignalStrength, TechnicalAnalysis
from engines.technical import get_technical_signals


@pytest.mark.asyncio
async def test_get_technical_signals_aapl():
    """Test that AAPL returns valid technical signals."""
    result = await get_technical_signals("AAPL", "6mo")

    assert isinstance(result, TechnicalAnalysis)
    assert result.ticker == "AAPL"
    assert result.period == "6mo"
    assert result.price_current > 0
    assert isinstance(result.overall_signal, SignalStrength)
    assert len(result.indicators) >= 3  # RSI, MACD, BB at minimum


@pytest.mark.asyncio
async def test_get_technical_signals_different_periods():
    """Test that different periods return valid results."""
    for period in ["1mo", "3mo", "6mo"]:
        result = await get_technical_signals("MSFT", period)
        assert result.ticker == "MSFT"
        assert result.price_current > 0
        assert len(result.indicators) >= 2


@pytest.mark.asyncio
async def test_get_technical_signals_invalid_ticker():
    """Test that invalid ticker raises ValueError."""
    with pytest.raises(ValueError, match="No price data"):
        await get_technical_signals("XYZNOTREAL123", "6mo")


@pytest.mark.asyncio
async def test_indicator_descriptions_populated():
    """Test that all indicators have descriptions."""
    result = await get_technical_signals("NVDA", "3mo")
    for ind in result.indicators:
        assert ind.name
        assert ind.description
        assert isinstance(ind.signal, SignalStrength)
