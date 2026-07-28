import os
from typing import List, Dict, Any, Optional
from agents.llm_factory import get_llm
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

def generate_report(
    topic: str, 
    research_notes: List[Dict[str, Any]], 
    review_feedback: Optional[str] = None, 
    revision_count: int = 0
) -> str:
    """
    Assembles the research notes into a coherent, comprehensive Markdown report.
    If it is a revision (revision_count > 0) and feedback is provided, it incorporates
    the critique to improve the report.
    """
    llm = get_llm(temperature=0.2)
    
    # Format the research notes into context
    notes_context = ""
    for idx, note in enumerate(research_notes):
        sub_q = note.get("sub_question", f"Sub-question {idx+1}")
        findings = note.get("findings", "No findings available.")
        notes_context += f"### Section: {sub_q}\n{findings}\n\n"
        
    system_prompt = (
        "You are an expert Science & Technology Writer agent. Your goal is to write a comprehensive, "
        "well-structured, engaging, and professional Markdown research report based on provided research notes.\n\n"
        "Guidelines:\n"
        "1. Include an Executive Summary at the top.\n"
        "2. Organize the body into logical sections matching the sub-questions.\n"
        "3. Preserve all factual claims and inline citations [1], [2] from the research notes.\n"
        "4. Include a References section at the end listing all source URLs cited.\n"
        "5. Use proper Markdown formatting (headers, bullet points, bold text, code blocks if appropriate).\n"
        "6. Do NOT invent facts or cite sources that were not provided in the research notes."
    )
    
    revision_prompt = ""
    if revision_count > 0 and review_feedback:
        revision_prompt = (
            f"\n\nIMPORTANT: This is Revision #{revision_count}. A reviewer analyzed your previous draft and provided the following feedback:\n"
            f"--- REVIEWER FEEDBACK ---\n{review_feedback}\n-------------------------\n"
            f"Please address all points in the reviewer feedback and improve the report accordingly."
        )
        
    user_prompt = (
        f"Research Topic: {topic}\n\n"
        f"Synthesized Research Notes:\n{notes_context}"
        f"{revision_prompt}\n\n"
        f"Write the complete, final Markdown research report."
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    try:
        response = llm.invoke(messages)
        return response.content
    except Exception as e:
        return f"# Error Generating Report\n\nFailed to generate report draft: {str(e)}"
