"""
All prompts for case study generation and evaluation.
Simple, reusable, and easy to modify.
"""


def get_case_generation_prompt(
    industry: str,
    complexity: str,
    focus_area: str,
    time_limit: int = 60,
) -> str:
    """Generate prompt for case study creation"""
    
    complexity_guide = {
        "beginner": """
- Clear, well-structured scenario
- Unambiguous problem statement
- Complete data provided
- 3-4 straightforward questions
- Expected resolution time: 10-15 minutes
""",
        "intermediate": """
- Real-world scenario with nuance
- Problem with some ambiguity
- Mixed clear and incomplete data
- 4-5 questions requiring analysis
- Stakeholder conflicts present
- Expected resolution time: 20-30 minutes
""",
        "advanced": """
- Complex, realistic scenario
- Heavy ambiguity and missing data
- Multiple valid solutions with trade-offs
- 5-7 open-ended strategic questions
- Red herrings and hidden assumptions
- Expected resolution time: 45-60 minutes
""",
    }

    complexity_instructions = complexity_guide.get(complexity.lower(), complexity_guide["intermediate"])

    prompt = f"""Generate a unique, realistic case study for an online business scenario.

INDUSTRY: {industry}
COMPLEXITY LEVEL: {complexity}
FOCUS AREA: {focus_area}
TIME LIMIT: {time_limit} minutes

QUALITY REQUIREMENTS:
{complexity_instructions}

CASE STRUCTURE (return as JSON):
{{
    "title": "Company/Case Title",
    "industry": "{industry}",
    "complexity": "{complexity}",
    "company_name": "Name of company",
    "company_background": "Brief history and context (2-3 sentences)",
    "scenario_overview": "Detailed problem description (3-4 paragraphs)",
    "key_metrics": {{
        "metric_name": "value with unit",
        "metric_name": "value with unit"
    }},
    "discussion_questions": [
        "Question 1?",
        "Question 2?",
        "Question 3?"
    ],
    "hidden_assumptions": [
        "Assumption that may not be obvious",
        "Market condition that impacts decision"
    ],
    "solution_framework": "What a good solution should address"
}}

IMPORTANT:
- Be creative and unique - never repeat templates
- Make metrics realistic and specific
- Questions should build on each other
- Include at least one non-obvious assumption
- Ensure scenario is solvable within {time_limit} minutes

Return ONLY valid JSON, no markdown, no code blocks."""

    return prompt


def get_evaluation_prompt(
    case_study: dict,
    student_solution: str,
) -> str:
    """Generate prompt for solution evaluation"""
    
    prompt = f"""You are an expert business consultant evaluating a case study solution.

CASE STUDY:
Title: {case_study.get('title', 'Unknown')}
Industry: {case_study.get('industry', 'Unknown')}
Complexity: {case_study.get('complexity', 'Unknown')}

Problem: {case_study.get('scenario_overview', 'N/A')[:500]}...

Questions to solve:
{chr(10).join([f"- {q}" for q in case_study.get('discussion_questions', [])])}

STUDENT'S SOLUTION:
{student_solution}

EVALUATION CRITERIA:

1. PROBLEM UNDERSTANDING (1-10)
   - Did they grasp the core issue?
   - Did they identify all constraints?

2. ANALYTICAL RIGOR (1-10)
   - Is reasoning data-driven?
   - Did they use the provided metrics?
   - Are assumptions stated?

3. BUSINESS ACUMEN (1-10)
   - Does solution show business sense?
   - Are trade-offs considered?
   - Is ROI/impact realistic?

4. COMMUNICATION (1-10)
   - Is solution clearly articulated?
   - Is structure logical?
   - Can a non-expert understand it?

5. FEASIBILITY (1-10)
   - Can this actually be executed?
   - Are resources considered?
   - Are risks identified?

Return as JSON:
{{
    "overall_score": 1-10,
    "problem_understanding": 1-10,
    "analytical_rigor": 1-10,
    "business_acumen": 1-10,
    "communication": 1-10,
    "feasibility": 1-10,
    "strengths": ["strength 1", "strength 2"],
    "weaknesses": ["weakness 1", "weakness 2"],
    "suggestions": ["actionable tip 1", "actionable tip 2"],
    "feedback": "2-3 sentence summary of performance"
}}

Return ONLY valid JSON."""

    return prompt


def get_feedback_prompt(
    feedback_data: dict,
    overall_score: float,
) -> str:
    """Generate personalized mentor feedback"""
    
    strengths = feedback_data.get("strengths", [])
    weaknesses = feedback_data.get("weaknesses", [])
    suggestions = feedback_data.get("suggestions", [])
    
    prompt = f"""You are an inspiring, constructive business mentor providing feedback.

STUDENT PERFORMANCE:
- Overall Score: {overall_score}/10
- Strengths: {', '.join(strengths)}
- Areas to improve: {', '.join(weaknesses)}

Provide warm, actionable mentorship feedback as JSON:
{{
    "title": "A positive, specific title for their attempt",
    "celebration": "Genuine praise for what they did well (1-2 sentences)",
    "growth_areas": [
        "Area 1 with specific example",
        "Area 2 with specific example"
    ],
    "next_steps": [
        "Specific action 1",
        "Specific action 2",
        "Specific action 3"
    ],
    "advanced_tip": "One expert-level insight they could explore",
    "encouragement": "Final motivational message"
}}

Return ONLY valid JSON."""

    return prompt