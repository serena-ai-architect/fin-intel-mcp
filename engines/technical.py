"""Technical analysis engine: yfinance + pandas-ta for RSI, MACD, Bollinger Bands, Moving Averages."""

from datetime import datetime, timezone

import pandas as pd
import pandas_ta as ta
import yfinance as yf

from db.models import SignalStrength, TechnicalAnalysis, TechnicalIndicator
from observability.langfuse_setup import trace_tool


def _rsi_signal(value: float) -> SignalStrength:
    if value > 70:
        return SignalStrength.SELL
    if value > 80:
        return SignalStrength.STRONG_SELL
    if value < 30:
        return SignalStrength.BUY
    if value < 20:
        return SignalStrength.STRONG_BUY
    return SignalStrength.NEUTRAL


def _macd_signal(macd: float, signal: float) -> SignalStrength:
    diff = macd - signal
    if diff > 0.5:
        return SignalStrength.BUY
    if diff > 1.5:
        return SignalStrength.STRONG_BUY
    if diff < -0.5:
        return SignalStrength.SELL
    if diff < -1.5:
        return SignalStrength.STRONG_SELL
    return SignalStrength.NEUTRAL


def _bb_signal(close: float, upper: float, lower: float) -> SignalStrength:
    if close > upper:
        return SignalStrength.SELL
    if close < lower:
        return SignalStrength.BUY
    return SignalStrength.NEUTRAL


def _ma_signal(close: float, ma50: float, ma200: float) -> SignalStrength:
    if ma50 > ma200 and close > ma50:
        return SignalStrength.BUY
    if ma50 < ma200 and close < ma50:
        return SignalStrength.SELL
    return SignalStrength.NEUTRAL


@trace_tool("get_technical_signals")
async def get_technical_signals(ticker: str, period: str = "6mo") -> TechnicalAnalysis:
    """Calculate RSI, MACD, Bollinger Bands, and Moving Averages for a ticker."""
    stock = yf.Ticker(ticker.upper())
    df = stock.history(period=period)

    if df.empty:
        raise ValueError(f"No price data found for {ticker}")

    close = df["Close"]
    current_price = float(close.iloc[-1])
    price_start = float(close.iloc[0])
    change_pct = ((current_price - price_start) / price_start) * 100

    indicators: list[TechnicalIndicator] = []

    # RSI (14-period)
    rsi = ta.rsi(close, length=14)
    if rsi is not None and not rsi.empty:
        rsi_val = float(rsi.iloc[-1])
        indicators.append(
            TechnicalIndicator(
                name="RSI (14)",
                value=round(rsi_val, 2),
                signal=_rsi_signal(rsi_val),
                description=f"RSI at {rsi_val:.1f} — {'overbought' if rsi_val > 70 else 'oversold' if rsi_val < 30 else 'neutral zone'}",
            )
        )

    # MACD (12, 26, 9)
    macd_df = ta.macd(close, fast=12, slow=26, signal=9)
    if macd_df is not None and not macd_df.empty:
        macd_val = float(macd_df.iloc[-1, 0])
        signal_val = float(macd_df.iloc[-1, 2])
        indicators.append(
            TechnicalIndicator(
                name="MACD (12,26,9)",
                value=round(macd_val, 4),
                signal=_macd_signal(macd_val, signal_val),
                description=f"MACD {macd_val:.4f}, Signal {signal_val:.4f} — {'bullish' if macd_val > signal_val else 'bearish'} crossover",
            )
        )

    # Bollinger Bands (20, 2)
    bb = ta.bbands(close, length=20, std=2)
    if bb is not None and not bb.empty:
        upper = float(bb.iloc[-1, 2])
        lower = float(bb.iloc[-1, 0])
        indicators.append(
            TechnicalIndicator(
                name="Bollinger Bands (20,2)",
                value=round(current_price, 2),
                signal=_bb_signal(current_price, upper, lower),
                description=f"Price ${current_price:.2f} | Upper ${upper:.2f} | Lower ${lower:.2f}",
            )
        )

    # Moving Averages (50 & 200)
    ma50 = ta.sma(close, length=50)
    ma200 = ta.sma(close, length=200)
    if ma50 is not None and not ma50.empty:
        ma50_val = float(ma50.iloc[-1])
        ma200_val = float(ma200.iloc[-1]) if ma200 is not None and not ma200.empty else ma50_val
        indicators.append(
            TechnicalIndicator(
                name="MA (50/200)",
                value=round(ma50_val, 2),
                signal=_ma_signal(current_price, ma50_val, ma200_val),
                description=f"SMA50 ${ma50_val:.2f} | SMA200 ${ma200_val:.2f} — {'golden cross' if ma50_val > ma200_val else 'death cross'}",
            )
        )

    # Overall signal: majority vote
    signal_weights = {
        SignalStrength.STRONG_BUY: 2,
        SignalStrength.BUY: 1,
        SignalStrength.NEUTRAL: 0,
        SignalStrength.SELL: -1,
        SignalStrength.STRONG_SELL: -2,
    }
    total = sum(signal_weights[ind.signal] for ind in indicators)
    avg = total / len(indicators) if indicators else 0
    if avg > 1:
        overall = SignalStrength.STRONG_BUY
    elif avg > 0.3:
        overall = SignalStrength.BUY
    elif avg < -1:
        overall = SignalStrength.STRONG_SELL
    elif avg < -0.3:
        overall = SignalStrength.SELL
    else:
        overall = SignalStrength.NEUTRAL

    return TechnicalAnalysis(
        ticker=ticker.upper(),
        period=period,
        price_current=round(current_price, 2),
        price_change_pct=round(change_pct, 2),
        indicators=indicators,
        overall_signal=overall,
        analyzed_at=datetime.now(timezone.utc),
    )
