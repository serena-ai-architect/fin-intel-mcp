"""
Hong Kong Regulatory Rules Database
=====================================
Compliance-as-infrastructure: regulatory rules encoded as structured data,
not agent prompts. Any MCP-compatible system can query these rules.

Covers: HKMA, SFC, PDPO, HKEX
"""

from __future__ import annotations

HK_REGULATORY_RULES: dict[str, list[dict]] = {
    # ── HKMA (Hong Kong Monetary Authority) ─────────────────────────
    "HKMA": [
        {
            "rule_id": "HKMA-TM-G1",
            "title": "Technology Risk Management (TM-G-1)",
            "summary": "Banks must establish IT governance frameworks covering AI/ML model risk, data management, and technology outsourcing.",
            "applies_to": ["banks", "virtual_banks", "stored_value_facilities"],
            "citation": "HKMA Supervisory Policy Manual TM-G-1 (Rev. 2024)",
            "relevance": ["ai_deployment", "model_risk", "technology_governance"],
        },
        {
            "rule_id": "HKMA-GenAI-Sandbox",
            "title": "Generative AI Sandbox",
            "summary": "Asia's first financial sector GenAI sandbox. Phase 1: 10 banks, 15 use cases. Phase 2 (2025): 20 banks, 14 tech partners, 27 use cases. Sandbox++ (2026): expanded to securities, insurance, asset management, MPF.",
            "applies_to": ["banks", "securities", "insurance", "asset_management"],
            "citation": "HKMA GenAI Sandbox Programme (Dec 2024 - ongoing)",
            "relevance": ["genai", "sandbox", "ai_deployment"],
        },
        {
            "rule_id": "HKMA-VA-01",
            "title": "Virtual Asset Service Provider Licensing",
            "summary": "Banks providing virtual asset services must comply with anti-money laundering and counter-terrorist financing requirements under AMLO.",
            "applies_to": ["banks", "virtual_asset_providers"],
            "citation": "HKMA Circular: Intermediaries dealing in virtual assets (2024)",
            "relevance": ["crypto", "virtual_assets", "aml"],
        },
        {
            "rule_id": "HKMA-OB-01",
            "title": "Open Banking API Framework",
            "summary": "Phase I-IV open banking implementation requiring banks to share product info, new applications, account info, and transactions via APIs.",
            "applies_to": ["banks", "virtual_banks", "fintech"],
            "citation": "HKMA Open API Framework (2018-2025)",
            "relevance": ["open_banking", "api", "data_sharing"],
        },
        {
            "rule_id": "HKMA-STABLECOIN-01",
            "title": "Stablecoin Issuer Licensing Regime",
            "summary": "Fiat-referenced stablecoin issuers must obtain HKMA license. Requirements: reserve assets, redemption at par, disclosure, AML/CFT compliance. Effective August 2025.",
            "applies_to": ["stablecoin_issuers", "virtual_asset_providers"],
            "citation": "Stablecoins Ordinance (gazetted March 2025)",
            "relevance": ["stablecoin", "crypto", "licensing"],
        },
    ],

    # ── SFC (Securities and Futures Commission) ─────────────────────
    "SFC": [
        {
            "rule_id": "SFC-VA-01",
            "title": "Virtual Asset Trading Platform Licensing",
            "summary": "All VA trading platforms operating in HK or marketing to HK investors must be SFC-licensed. Dual licensing regime covers both securities and non-securities tokens.",
            "applies_to": ["va_exchanges", "crypto_platforms"],
            "citation": "SFC Guidelines for Virtual Asset Trading Platform Operators (2023, updated 2025)",
            "relevance": ["crypto", "exchange", "licensing"],
        },
        {
            "rule_id": "SFC-TYPE-9",
            "title": "Type 9 Licence — Asset Management",
            "summary": "Required for managing portfolios of securities/futures. AI-driven fund management and robo-advisory fall under this licence.",
            "applies_to": ["asset_managers", "robo_advisors", "fund_managers"],
            "citation": "Securities and Futures Ordinance (Cap. 571), Schedule 5",
            "relevance": ["asset_management", "ai_trading", "robo_advisory"],
        },
        {
            "rule_id": "SFC-AI-GUIDANCE",
            "title": "Use of AI in Licensed Activities",
            "summary": "Licensed corporations using AI must maintain human oversight, ensure explainability for investment decisions, and document model validation procedures.",
            "applies_to": ["licensed_corporations", "fund_managers", "brokers"],
            "citation": "SFC Circular: Use of Artificial Intelligence (2025)",
            "relevance": ["ai_governance", "explainability", "model_risk"],
        },
    ],

    # ── PDPO (Personal Data Privacy Ordinance) ──────────────────────
    "PDPO": [
        {
            "rule_id": "PDPO-DPP1-6",
            "title": "Six Data Protection Principles",
            "summary": "Collection limitation, accuracy, retention, use limitation, security, transparency. All apply to AI training data and model outputs.",
            "applies_to": ["all_organizations"],
            "citation": "Personal Data (Privacy) Ordinance (Cap. 486)",
            "relevance": ["data_privacy", "ai_training", "data_governance"],
        },
        {
            "rule_id": "PDPO-CROSS-BORDER",
            "title": "Cross-Border Data Transfer",
            "summary": "Section 33 (not yet in force but followed in practice): personal data transfers outside HK require adequate protection. China's PIPL adds stricter requirements for Mainland transfers.",
            "applies_to": ["all_organizations", "cross_border"],
            "citation": "PDPO Section 33; China PIPL Articles 38-43",
            "relevance": ["cross_border", "data_localization", "china_pipl"],
        },
        {
            "rule_id": "PDPO-AI-GUIDANCE",
            "title": "Guidance on Use of AI / Big Data",
            "summary": "PCPD guidance requires: data minimization in AI training, algorithmic fairness assessment, privacy impact assessment for AI systems, and transparency about automated decision-making.",
            "applies_to": ["all_organizations"],
            "citation": "PCPD Guidance on Ethical Development and Use of AI (2024)",
            "relevance": ["ai_ethics", "algorithmic_fairness", "pia"],
        },
    ],

    # ── HKEX (Hong Kong Exchanges and Clearing) ─────────────────────
    "HKEX": [
        {
            "rule_id": "HKEX-CH18A",
            "title": "Chapter 18A — Biotech Listing Rules",
            "summary": "Pre-revenue biotech companies can list with market cap ≥ HK$1.5B. Requires at least one core product past Phase I clinical trials.",
            "applies_to": ["biotech", "pre_revenue"],
            "citation": "HKEX Main Board Listing Rules Chapter 18A",
            "relevance": ["listing", "biotech", "ipo"],
        },
        {
            "rule_id": "HKEX-CH19C",
            "title": "Chapter 19C — Secondary Listing of Greater China Companies",
            "summary": "Qualifying issuers from Greater China already listed on NYSE/NASDAQ can secondary list on HKEX with reduced requirements. Used by Alibaba, JD, Baidu, etc.",
            "applies_to": ["dual_listed", "secondary_listing", "greater_china"],
            "citation": "HKEX Main Board Listing Rules Chapter 19C",
            "relevance": ["dual_listing", "secondary_listing", "us_china"],
        },
        {
            "rule_id": "HKEX-ESG",
            "title": "ESG Reporting Requirements",
            "summary": "All listed companies must report on environmental, social, and governance metrics in annual reports. Climate-related disclosures (TCFD-aligned) mandatory from 2025.",
            "applies_to": ["listed_companies"],
            "citation": "HKEX Appendix C2: Environmental, Social and Governance Reporting Guide",
            "relevance": ["esg", "climate", "disclosure"],
        },
        {
            "rule_id": "HKEX-CONNECT",
            "title": "Stock Connect (Shanghai-HK / Shenzhen-HK)",
            "summary": "Mutual market access: Northbound (HK→Mainland) and Southbound (Mainland→HK) trading. Daily quotas: RMB 52B northbound, RMB 42B southbound. Eligible stocks determined by index inclusion.",
            "applies_to": ["listed_companies", "cross_border", "investors"],
            "citation": "HKEX Stock Connect Rules",
            "relevance": ["stock_connect", "cross_border", "mainland_capital"],
        },
    ],
}

# ── Cross-Border Risk Factors ───────────────────────────────────────

CROSS_BORDER_RISK_FACTORS: list[dict] = [
    {
        "factor": "data_localization",
        "description": "China PIPL requires personal data of mainland citizens to be stored in mainland China. Companies operating across HK-Mainland must implement data segregation.",
        "severity": "high",
        "jurisdictions": ["HK", "CN"],
    },
    {
        "factor": "capital_flow_restrictions",
        "description": "Mainland capital outflow controls (SAFE quota system) limit cross-border investment. Stock Connect provides regulated channels but with daily quotas.",
        "severity": "medium",
        "jurisdictions": ["HK", "CN"],
    },
    {
        "factor": "dual_listing_compliance",
        "description": "Companies listed on both US and HK exchanges face dual compliance: SEC vs SFC reporting, accounting standards (US GAAP vs IFRS), and audit oversight (PCAOB vs AFRC).",
        "severity": "high",
        "jurisdictions": ["HK", "US"],
    },
    {
        "factor": "sanctions_screening",
        "description": "HK entities must comply with UN sanctions (enforced by CE) and may be subject to US secondary sanctions. SDN list screening required for financial institutions.",
        "severity": "high",
        "jurisdictions": ["HK", "US", "CN"],
    },
    {
        "factor": "vie_structure_risk",
        "description": "Variable Interest Entity structures used by many Chinese tech companies (Alibaba, Tencent, etc.) face ongoing regulatory uncertainty in both PRC and US jurisdictions.",
        "severity": "medium",
        "jurisdictions": ["HK", "US", "CN"],
    },
    {
        "factor": "regulatory_divergence",
        "description": "Post-2020 regulatory divergence between HK and Mainland creates compliance complexity. National Security Law and Article 23 introduce new compliance dimensions.",
        "severity": "medium",
        "jurisdictions": ["HK", "CN"],
    },
]
