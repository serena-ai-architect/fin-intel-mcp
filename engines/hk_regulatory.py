"""
Hong Kong Regulatory Compliance Tools
=======================================
Compliance-as-infrastructure: regulatory rules as composable MCP skills.

Three tools:
  1. check_hk_compliance — applicable regulatory requirements for a company/activity
  2. search_hkex_filings — HKEX announcements and disclosure filings
  3. assess_cross_border_risk — cross-border regulatory risk (HK↔Mainland↔International)
"""

from __future__ import annotations

import json
from datetime import datetime

from db.models import (
    ComplianceCheckResult,
    ComplianceRule,
    CrossBorderRiskResult,
    CrossBorderRiskFactor,
    HKEXFilingResult,
    HKEXFiling,
)
from engines.hk_rules_data import CROSS_BORDER_RISK_FACTORS, HK_REGULATORY_RULES


async def check_hk_compliance(
    ticker: str,
    activity_type: str,
    jurisdiction: str = "HK",
) -> ComplianceCheckResult:
    """Return applicable HK regulatory requirements for a company/activity.

    Searches the structured rules database by activity type and jurisdiction,
    returning relevant rules with citations.
    """
    activity_lower = activity_type.lower()
    applicable_rules: list[ComplianceRule] = []

    for regulator, rules in HK_REGULATORY_RULES.items():
        for rule in rules:
            # Match by relevance keywords
            relevance_match = any(
                kw in activity_lower
                for kw in rule["relevance"]
            )
            # Also match if activity_type directly mentions the regulator
            regulator_match = regulator.lower() in activity_lower

            if relevance_match or regulator_match:
                applicable_rules.append(
                    ComplianceRule(
                        rule_id=rule["rule_id"],
                        regulator=regulator,
                        title=rule["title"],
                        summary=rule["summary"],
                        citation=rule["citation"],
                        applies_to=rule["applies_to"],
                    )
                )

    return ComplianceCheckResult(
        ticker=ticker,
        activity_type=activity_type,
        jurisdiction=jurisdiction,
        rules=applicable_rules,
        total_rules_checked=sum(len(r) for r in HK_REGULATORY_RULES.values()),
        checked_at=datetime.now(),
    )


async def search_hkex_filings(
    ticker: str,
    filing_type: str | None = None,
    period: str = "1y",
) -> HKEXFilingResult:
    """Search HKEX announcements and disclosure filings.

    Note: In production this would call the HKEX ESS API. For portfolio demo
    purposes, returns structured placeholder data that demonstrates the tool's
    interface and integration pattern.
    """
    # Demonstrate the tool interface with realistic placeholder data
    # In production: call HKEX ESS (Electronic Submission System) API
    filings: list[HKEXFiling] = []

    if ticker.endswith(".HK") or ticker.startswith("0") or ticker.startswith("1") or ticker.startswith("3") or ticker.startswith("9"):
        filings = [
            HKEXFiling(
                title=f"{ticker} Annual Results Announcement",
                filing_type="Annual Results",
                date="2025-03-20",
                url=f"https://www1.hkexnews.hk/listedco/listconews/sehk/{ticker.replace('.HK', '')}/",
                summary="Annual results for the year ended December 31, 2024. Revenue, profit, and dividend details.",
            ),
            HKEXFiling(
                title=f"{ticker} Connected Transaction — Share Repurchase",
                filing_type="Connected Transaction",
                date="2025-02-15",
                url=f"https://www1.hkexnews.hk/listedco/listconews/sehk/{ticker.replace('.HK', '')}/",
                summary="Announcement regarding share repurchase programme under general mandate.",
            ),
            HKEXFiling(
                title=f"{ticker} ESG Report 2024",
                filing_type="ESG Report",
                date="2025-04-01",
                url=f"https://www1.hkexnews.hk/listedco/listconews/sehk/{ticker.replace('.HK', '')}/",
                summary="Environmental, Social and Governance report covering climate disclosures (TCFD-aligned).",
            ),
        ]

    return HKEXFilingResult(
        ticker=ticker,
        filings=filings,
        total_found=len(filings),
        period=period,
        searched_at=datetime.now(),
        note="Demo data — production version calls HKEX ESS API" if filings else "No HKEX filings found for this ticker",
    )


async def assess_cross_border_risk(
    ticker: str,
    source_jurisdiction: str = "HK",
    target_jurisdiction: str = "CN",
) -> CrossBorderRiskResult:
    """Evaluate cross-border regulatory risk for companies operating across jurisdictions.

    Covers: data localization (PIPL/PDPO), capital flows, Stock Connect,
    dual-listing compliance, sanctions screening.
    """
    jurisdictions = {source_jurisdiction.upper(), target_jurisdiction.upper()}

    applicable_factors: list[CrossBorderRiskFactor] = []
    for factor in CROSS_BORDER_RISK_FACTORS:
        factor_jurisdictions = set(factor["jurisdictions"])
        if jurisdictions & factor_jurisdictions:
            applicable_factors.append(
                CrossBorderRiskFactor(
                    factor=factor["factor"],
                    description=factor["description"],
                    severity=factor["severity"],
                    jurisdictions=factor["jurisdictions"],
                )
            )

    # Calculate overall risk score (simple weighted average)
    severity_weights = {"high": 3, "medium": 2, "low": 1}
    if applicable_factors:
        total_weight = sum(severity_weights.get(f.severity, 1) for f in applicable_factors)
        max_weight = len(applicable_factors) * 3
        risk_score = round((total_weight / max_weight) * 10, 1)
    else:
        risk_score = 0.0

    return CrossBorderRiskResult(
        ticker=ticker,
        source_jurisdiction=source_jurisdiction,
        target_jurisdiction=target_jurisdiction,
        risk_factors=applicable_factors,
        overall_risk_score=risk_score,
        assessed_at=datetime.now(),
    )
