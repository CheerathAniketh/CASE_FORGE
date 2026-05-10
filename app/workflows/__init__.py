"""GROQ tool definitions for LangGraph"""

from langchain_core.tools import tool
from app.services.groq_service import GroqService


@tool
async def generate_case_via_groq(prompt: str) -> str:
    """
    Tool to generate case study via GROQ API.
    
    Args:
        prompt: The case generation prompt
        
    Returns:
        Generated case study as JSON string
    """
    groq_service = GroqService()
    result = await groq_service.generate_case(prompt)
    
    if result["success"]:
        return result["content"]
    else:
        raise Exception(f"GROQ generation failed: {result['error']}")