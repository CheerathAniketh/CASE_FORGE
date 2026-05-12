"""
Tools for Case Generation
These tools enhance case studies with realistic data
"""

import json
from typing import Dict, Any
from app.logger import get_logger

logger = get_logger(__name__)


class CaseStudyTools:
    """Tools that provide data for case generation"""

    @staticmethod
    def market_research(industry: str, company_type: str = "startup") -> Dict[str, Any]:
        """
        Market research tool - provides market context
        
        Returns market size, growth rate, trends, competitors
        """
        logger.info(f"tool_market_research: {industry}")
        
        market_data = {
            "fintech": {
                "market_size": "$150B globally",
                "growth_rate": "15-20% YoY",
                "key_trends": [
                    "AI-powered personalization",
                    "Open banking APIs",
                    "Embedded finance",
                    "Regulatory consolidation"
                ],
                "major_competitors": [
                    "Traditional banks (digitizing)",
                    "Big Tech (Apple Pay, Google Wallet)",
                    "Neobanks (Revolut, N26, Chime)",
                    "Payment processors (Stripe, Square)"
                ],
                "market_dynamics": "Highly competitive with regulatory pressure. Winners consolidating. Niche players focusing on underserved segments."
            },
            "healthcare": {
                "market_size": "$200B+ in US alone",
                "growth_rate": "8-12% YoY",
                "key_trends": [
                    "Telemedicine adoption",
                    "AI diagnostics",
                    "Value-based care",
                    "Remote patient monitoring"
                ],
                "major_competitors": [
                    "Legacy health systems",
                    "Insurance companies",
                    "Tech giants (Amazon Pharmacy, Apple Health)",
                    "Specialized telehealth platforms"
                ],
                "market_dynamics": "Fragmented market. Regulatory complexity. High switching costs. Digital disruption accelerating."
            },
            "ecommerce": {
                "market_size": "$800B+ in US alone",
                "growth_rate": "10-15% YoY",
                "key_trends": [
                    "Social commerce",
                    "Live shopping",
                    "Same-day delivery",
                    "Personalization at scale"
                ],
                "major_competitors": [
                    "Amazon dominance (40% market share)",
                    "Walmart, Target online",
                    "Specialized vertical marketplaces",
                    "Direct-to-consumer brands"
                ],
                "market_dynamics": "Amazon-dominated. Niche players competing on UX, curation, community. Rising shipping costs pressure margins."
            },
            "saas": {
                "market_size": "$250B+ globally",
                "growth_rate": "10-20% YoY (varies by segment)",
                "key_trends": [
                    "Vertical SaaS growth",
                    "AI/ML feature additions",
                    "Platform consolidation",
                    "Lower CAC through partnerships"
                ],
                "major_competitors": [
                    "Salesforce, Microsoft, Adobe (horizontal)",
                    "Vertical players (industry-specific)",
                    "Open source alternatives",
                    "In-house solutions by enterprises"
                ],
                "market_dynamics": "Land-and-expand model dominant. CAC payback 12-24 months standard. Consolidation accelerating."
            }
        }
        
        # Default if industry not found
        default_market = {
            "market_size": "$50B+ market",
            "growth_rate": "15-25% YoY",
            "key_trends": ["Digital transformation", "AI integration", "Consolidation"],
            "major_competitors": ["Established players", "Rising startups", "Big Tech"],
            "market_dynamics": "Dynamic market with significant opportunity for differentiated players"
        }
        
        return market_data.get(industry.lower(), default_market)

    @staticmethod
    def financial_analysis(
        industry: str,
        user_count: int = 10000,
        arpu: float = 50.0
    ) -> Dict[str, Any]:
        """
        Financial analysis tool - provides unit economics benchmarks
        
        Returns: CAC, LTV, payback period, margins, growth projections
        """
        logger.info(f"tool_financial_analysis: {industry}, users={user_count}, arpu=${arpu}")
        
        # Base benchmarks by industry
        benchmarks = {
            "fintech": {
                "cac": "$200-500",
                "ltv": "$5,000-15,000",
                "payback_months": "6-12",
                "gross_margin": "70-85%",
                "operating_margin": "-10% to +15%",
                "churn": "3-7% monthly",
                "rule_of_40": "Growth% + Margin% should be >40%"
            },
            "healthcare": {
                "cac": "$500-2000",
                "ltv": "$10,000-50,000",
                "payback_months": "12-24",
                "gross_margin": "60-75%",
                "operating_margin": "-20% to +10%",
                "churn": "2-5% monthly",
                "rule_of_40": "Regulatory overhead impacts profitability"
            },
            "ecommerce": {
                "cac": "$20-100",
                "ltv": "$500-2000",
                "payback_months": "3-6",
                "gross_margin": "30-50%",
                "operating_margin": "-5% to +10%",
                "churn": "15-25% monthly",
                "rule_of_40": "Thin margins require scale"
            },
            "saas": {
                "cac": "$200-1000",
                "ltv": "$5,000-50,000",
                "payback_months": "9-18",
                "gross_margin": "70-90%",
                "operating_margin": "-30% to +30%",
                "churn": "3-7% monthly",
                "rule_of_40": "Land-and-expand model standard"
            }
        }
        
        default_bench = {
            "cac": "$500",
            "ltv": "$10,000",
            "payback_months": "12",
            "gross_margin": "60-70%",
            "operating_margin": "-10% to +10%",
            "churn": "5-10% monthly",
            "rule_of_40": "Growth + Margin should target >40%"
        }
        
        bench = benchmarks.get(industry.lower(), default_bench)
        
        # Calculate projections
        monthly_revenue = user_count * arpu
        annual_revenue = monthly_revenue * 12
        
        return {
            "unit_economics": bench,
            "current_metrics": {
                "monthly_active_users": user_count,
                "monthly_revenue": f"${monthly_revenue:,.0f}",
                "annual_revenue": f"${annual_revenue:,.0f}",
                "arpu": f"${arpu}"
            },
            "growth_projections": {
                "year_1": f"${annual_revenue:,.0f}",
                "year_2": f"${annual_revenue * 2.5:,.0f} (assuming 150% growth)",
                "year_3": f"${annual_revenue * 6:,.0f} (assuming 140% growth)"
            },
            "key_metrics": {
                "break_even": "18-36 months typically",
                "path_to_profitability": "Improve CAC/LTV ratio or reduce churn",
                "focus_areas": ["Reduce CAC", "Improve LTV", "Lower churn", "Increase ARPU"]
            }
        }

    @staticmethod
    def competitive_intelligence(industry: str, target_segment: str = "SMB") -> Dict[str, Any]:
        """
        Competitive intelligence tool - analyzes competitive landscape
        
        Returns: competitor analysis, positioning, white space opportunities
        """
        logger.info(f"tool_competitive_intelligence: {industry}, segment={target_segment}")
        
        competitive_data = {
            "fintech": {
                "direct_competitors": 50,
                "indirect_competitors": 200,
                "market_concentration": {
                    "top_3": "20-30% market share",
                    "fragmented": "70-80% spread across neobanks and specialists"
                },
                "competitive_advantages": [
                    "Network effects (user base)",
                    "Data (transaction history, spending patterns)",
                    "Brand trust",
                    "Technology moat (AI, ML)"
                ],
                "white_space": [
                    "Vertical fintech (industry-specific)",
                    "Underserved demographics (seniors, immigrants)",
                    "Emerging markets",
                    "B2B fintech for SMBs"
                ],
                "threat_level": "HIGH - Big Tech entering, consolidation accelerating",
                "defensibility": "Medium - Commoditizing but network effects matter"
            },
            "healthcare": {
                "direct_competitors": 100,
                "indirect_competitors": 500,
                "market_concentration": {
                    "top_3": "30-40% (legacy health systems)",
                    "fragmented": "60-70% across specialists and digital players"
                },
                "competitive_advantages": [
                    "Regulatory moat (licenses, certifications)",
                    "Data (patient records, outcomes)",
                    "Clinical partnerships",
                    "Trust (especially for sensitive data)"
                ],
                "white_space": [
                    "Mental health platforms",
                    "Rare disease specialists",
                    "Preventive care (wellness)",
                    "Rural healthcare"
                ],
                "threat_level": "VERY HIGH - Regulation, incumbents, Amazon/Apple entering",
                "defensibility": "High if you have clinical/regulatory moat"
            },
            "ecommerce": {
                "direct_competitors": 1000,
                "indirect_competitors": 10000,
                "market_concentration": {
                    "amazon": "40% market share",
                    "walmart_target": "15%",
                    "rest": "45% fragmented"
                },
                "competitive_advantages": [
                    "Curation (curated selection vs Amazon's everything)",
                    "Community (engaged users, reviews)",
                    "UX (frictionless checkout)",
                    "Brand (loyalty, repeat purchases)"
                ],
                "white_space": [
                    "Vertical marketplaces (niche products)",
                    "Social commerce (Instagram, TikTok native)",
                    "Subscription models (recurring revenue)",
                    "DTC brand aggregators"
                ],
                "threat_level": "CRITICAL - Amazon dominance, thin margins",
                "defensibility": "Low on price, medium on brand"
            },
            "saas": {
                "direct_competitors": 200,
                "indirect_competitors": 1000,
                "market_concentration": {
                    "top_3": "Salesforce, Microsoft, Adobe dominate",
                    "rest": "Vertical players, open source alternatives"
                },
                "competitive_advantages": [
                    "Integration ecosystem (API)",
                    "Customer lock-in (switching costs)",
                    "Brand (trusted enterprise vendor)",
                    "Feature velocity (R&D investment)"
                ],
                "white_space": [
                    "Vertical SaaS (industry-specific solutions)",
                    "Micro-SaaS (niche, low CAC)",
                    "Open source (vs proprietary)",
                    "AI-native platforms"
                ],
                "threat_level": "MEDIUM - Platforms consolidating, but room for verticals",
                "defensibility": "High for vertical specialists"
            }
        }
        
        default_intel = {
            "direct_competitors": 50,
            "indirect_competitors": 500,
            "market_concentration": {"leader": "20-30%", "rest": "70-80%"},
            "competitive_advantages": ["Differentiation", "Customer lock-in", "Scale"],
            "white_space": ["Vertical specialization", "Underserved segments", "Emerging tech"],
            "threat_level": "MEDIUM",
            "defensibility": "Medium - depends on execution"
        }
        
        return competitive_data.get(industry.lower(), default_intel)

    @staticmethod
    def industry_benchmarks(industry: str, metric: str = "growth") -> Dict[str, Any]:
        """
        Industry benchmarks tool - provides performance benchmarks
        
        Returns: how a company compares to industry averages
        """
        logger.info(f"tool_industry_benchmarks: {industry}, metric={metric}")
        
        benchmarks = {
            "fintech_growth": "15-25% YoY for profitable players",
            "fintech_churn": "3-7% monthly is acceptable",
            "fintech_unit_economics": "CAC payback in 6-12 months",
            "healthcare_growth": "8-15% YoY depending on segment",
            "healthcare_cac": "High due to sales-driven model",
            "ecommerce_growth": "20-30% for DTC brands",
            "ecommerce_margins": "Gross 30-50%, Operating 0-10%",
            "saas_growth": "20-50% for high-growth SaaS",
            "saas_magic_number": "0.75+ is good, 1.0+ is excellent"
        }
        
        return {
            "metric": metric,
            "industry": industry,
            "benchmark": benchmarks.get(f"{industry.lower()}_{metric}", "Industry-specific"),
            "note": "Benchmarks vary by business model, stage, and geography"
        }