"""Pydantic models for fin-intel-mcp — the Python equivalent of Zod schemas."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


# ── Enums ──────────────────────────────────────────────────────────────────────


class FilingType(str, Enum):
    TEN_K = "10-K"
    TEN_Q = "10-Q"
    EIGHT_K = "8-K"


class DocumentType(str, Enum):
    SEC_FILING = "sec_filing"
    EARNINGS_CALL = "earnings_call"
    CUSTOM = "custom"


class SentimentLabel(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class SignalStrength(str, Enum):
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    NEUTRAL = "neutral"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


# ── Document Models ────────────────────────────────────────────────────────────


class DocumentMetadata(BaseModel):
    ticker: str
    filing_type: FilingType | None = None
    document_type: DocumentType
    filed_date: datetime | None = None
    fiscal_year: int | None = None
    fiscal_quarter: int | None = None
    source_url: str | None = None


class DocumentChunk(BaseModel):
    id: str | None = None
    document_id: str
    content: str
    chunk_index: int
    embedding: list[float] | None = None
    metadata: DocumentMetadata


class Document(BaseModel):
    id: str | None = None
    ticker: str
    title: str
    document_type: DocumentType
    metadata: DocumentMetadata
    created_at: datetime | None = None


# ── RAG Models ─────────────────────────────────────────────────────────────────


class Citation(BaseModel):
    chunk_id: str
    document_title: str
    content_snippet: str = Field(description="First 200 chars of the cited chunk")
    relevance_score: float = Field(ge=0, le=1)


class RAGResult(BaseModel):
    answer: str
    citations: list[Citation]
    query: str
    retrieval_method: str = "hybrid"


# ── Sentiment Models ───────────────────────────────────────────────────────────


class SentimentResult(BaseModel):
    text: str = Field(description="Input text analyzed")
    label: SentimentLabel
    score: float = Field(ge=0, le=1, description="Confidence score")
    model: str = Field(description="Model used: finbert or deepseek")


class SentimentAnalysis(BaseModel):
    ticker: str
    results: list[SentimentResult]
    overall_sentiment: SentimentLabel
    overall_score: float = Field(ge=0, le=1)
    analyzed_at: datetime


# ── Technical Analysis Models ──────────────────────────────────────────────────


class TechnicalIndicator(BaseModel):
    name: str
    value: float | None
    signal: SignalStrength
    description: str


class TechnicalAnalysis(BaseModel):
    ticker: str
    period: str = Field(description="e.g., '6mo', '1y'")
    price_current: float
    price_change_pct: float
    indicators: list[TechnicalIndicator]
    overall_signal: SignalStrength
    analyzed_at: datetime


# ── MCP Tool Input Models ──────────────────────────────────────────────────────


class SearchFilingsInput(BaseModel):
    ticker: str = Field(description="Stock ticker symbol, e.g., NVDA")
    query: str = Field(description="Natural language query about the filing")
    filing_type: FilingType | None = Field(default=None, description="Filter by filing type")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of results to return")


class SearchEarningsInput(BaseModel):
    ticker: str
    query: str
    top_k: int = Field(default=5, ge=1, le=20)


class AnalyzeSentimentInput(BaseModel):
    ticker: str
    texts: list[str] = Field(description="List of texts to analyze", min_length=1, max_length=20)


class GetTechnicalSignalsInput(BaseModel):
    ticker: str
    period: str = Field(default="6mo", description="yfinance period: 1mo, 3mo, 6mo, 1y, 2y")


class IngestDocumentInput(BaseModel):
    ticker: str
    filing_type: FilingType = Field(default=FilingType.TEN_K)
    fiscal_year: int | None = Field(default=None, description="If None, fetches the latest")


class QueryKnowledgeBaseInput(BaseModel):
    query: str = Field(description="Natural language question")
    ticker: str | None = Field(default=None, description="Optional ticker filter")
    top_k: int = Field(default=5, ge=1, le=20)


# ── HK Regulatory Compliance Models ──────────────────────────────────


class ComplianceRule(BaseModel):
    rule_id: str
    regulator: str = Field(description="HKMA, SFC, PDPO, or HKEX")
    title: str
    summary: str
    citation: str
    applies_to: list[str]


class ComplianceCheckResult(BaseModel):
    ticker: str
    activity_type: str
    jurisdiction: str
    rules: list[ComplianceRule]
    total_rules_checked: int
    checked_at: datetime


class HKEXFiling(BaseModel):
    title: str
    filing_type: str
    date: str
    url: str
    summary: str


class HKEXFilingResult(BaseModel):
    ticker: str
    filings: list[HKEXFiling]
    total_found: int
    period: str
    searched_at: datetime
    note: str = ""


class CrossBorderRiskFactor(BaseModel):
    factor: str
    description: str
    severity: str = Field(description="high, medium, or low")
    jurisdictions: list[str]


class CrossBorderRiskResult(BaseModel):
    ticker: str
    source_jurisdiction: str
    target_jurisdiction: str
    risk_factors: list[CrossBorderRiskFactor]
    overall_risk_score: float = Field(ge=0, le=10)
    assessed_at: datetime
