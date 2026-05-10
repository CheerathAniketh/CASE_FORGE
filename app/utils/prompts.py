def get_case_generation_prompt(
    industry: str,
    complexity: str,
    focus_area: str = None,
    time_limit: int = 60,
    num_questions: int = 3
) -> str:
    """
    Generate a structured prompt optimized for GROQ Mixtral.
    GROQ is fast, so we can use detailed prompts.
    """
    
    difficulty_guidance = {
        "beginner": "Keep concepts clear and simple. Avoid jargon. Use real-world relatable scenarios.",
        "intermediate": "Include industry terminology. Moderate complexity. Mix strategic and tactical decisions.",
        "advanced": "Include complex metrics (NPV, IRR, WACC). Strategic dilemmas. Nuanced stakeholder analysis."
    }
    
    prompt = f"""You are an expert business consultant and MBA professor creating case studies for professional development.

Your task: Generate a comprehensive, realistic business case study for educational use.

REQUIREMENTS:
- Industry: {industry}
- Difficulty Level: {complexity}
- {difficulty_guidance.get(complexity, '')}
- Focus Area: {focus_area if focus_area else 'General business challenge'}
- Time to Solve: {time_limit} minutes
- Number of Discussion Questions: {num_questions}

IMPORTANT: Return ONLY valid JSON (no markdown, no code blocks, no explanation text).

Return this exact JSON structure:
{{
  "title": "Compelling case study title",
  "industry": "{industry}",
  "complexity": "{complexity}",
  "executive_summary": "2-3 sentence overview of the situation",
  "background": {{
    "company_name": "Company name (real or realistic)",
    "founded_year": 2020,
    "company_context": "Company history, mission, and background (3-4 sentences)",
    "market_situation": "Current market conditions, trends, competitive landscape (3-4 sentences)",
    "key_players": "Main competitors, partners, stakeholders (list format)"
  }},
  "problem_statement": "Clear, specific description of the challenge (2-3 paragraphs)",
  "current_situation": {{
    "challenges": ["Challenge 1", "Challenge 2", "Challenge 3"],
    "opportunities": ["Opportunity 1", "Opportunity 2"],
    "constraints": ["Constraint 1", "Constraint 2", "Constraint 3"]
  }},
  "financial_data": {{
    "current_revenue_millions": 50,
    "market_size_billions": 10,
    "growth_rate_percent": 15,
    "profit_margin_percent": 25,
    "key_metrics": {{"metric_name": "value"}}
  }},
  "discussion_questions": [
    {{
      "id": 1,
      "question": "What should be the strategic priority?",
      "hint": "Consider market trends and internal capabilities",
      "focus_area": "Strategy",
      "expected_thinking": "Multi-factor analysis, risk assessment"
    }},
    {{
      "id": 2,
      "question": "How should the company execute this?",
      "hint": "Think about implementation roadmap",
      "focus_area": "Execution",
      "expected_thinking": "Phased approach, resource allocation"
    }},
    {{
      "id": 3,
      "question": "What are the success metrics?",
      "hint": "Define KPIs and tracking mechanisms",
      "focus_area": "Measurement",
      "expected_thinking": "Quantifiable goals, milestones"
    }}
  ],
  "solution_framework": {{
    "recommended_approach": "Detailed explanation of best approach (2-3 paragraphs)",
    "implementation_steps": ["Step 1: Action", "Step 2: Action", "Step 3: Action"],
    "expected_outcomes": "What success looks like",
    "timeline": "Estimated implementation timeline",
    "risks": ["Risk 1", "Risk 2", "Risk 3"],
    "mitigation_strategies": ["Strategy 1", "Strategy 2", "Strategy 3"]
  }},
  "key_learnings": [
    "Lesson 1: What students should understand",
    "Lesson 2: Applicable business principle",
    "Lesson 3: Real-world application"
  ]
}}

Generate the case study now. Return ONLY the JSON, nothing else:"""
    
    return prompt


def get_case_validation_prompt(case_json: str) -> str:
    """Prompt to validate case study quality"""
    return f"""Validate this case study JSON. Check for:
1. All required fields present and non-empty
2. Content length appropriate (at least 50 chars per field)
3. Questions are specific and answerable
4. Financial data is reasonable

Case data:
{case_json}

Respond with ONLY this JSON format:
{{
  "is_valid": true/false,
  "score": 0.85,
  "issues": ["issue1", "issue2"],
  "suggestions": ["suggestion1", "suggestion2"]
}}"""


def get_case_refinement_prompt(
    original_case: str,
    validation_errors: list,
    refinement_attempt: int
) -> str:
    """Prompt to refine a case that failed validation"""
    
    errors_str = "\n".join([f"- {error}" for error in validation_errors])
    
    prompt = f"""The following case study had these validation issues:

{errors_str}

Original case:
{original_case}

Please refine it to fix these issues. Keep the same structure but improve the content quality and completeness.
This is refinement attempt {refinement_attempt}.

Return ONLY the refined JSON object (same structure as before), nothing else:"""
    
    return prompt