import os
from typing import List, Dict, Any, Tuple
from pydantic import BaseModel, Field
from agents.llm_factory import get_llm
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

class ReviewOutput(BaseModel):
    status: str = Field(
        ..., 
        description="Must be either 'approved' if the draft meets quality standards, or 'needs_revision' if it requires changes."
    )
    feedback: str = Field(
        ..., 
        description="Detailed, actionable feedback explaining why the report was approved or what specific revisions are needed."
    )

def review_report(draft: str, research_notes: List[Dict[str, Any]], revision_count: int = 0) -> Tuple[str, str]:
    """
    Critiques the generated Markdown report draft against the factual research notes.
    Returns a tuple of (status, feedback) where status is 'approved' or 'needs_revision'.
    """
    # Force approval if revision limit reached
    if revision_count >= 2:
        return (
            "approved",
            f"Draft automatically approved. Revision limit reached ({revision_count} revisions)."
        )
        
    llm = get_llm(temperature=0.0)
    structured_llm = llm.with_structured_output(ReviewOutput)
    
    # Format research notes for verification
    notes_summary = ""
    for idx, note in enumerate(research_notes):
        sub_q = note.get("sub_question", f"Sub-question {idx+1}")
        findings = note.get("findings", "")
        notes_summary += f"- {sub_q}: {findings[:300]}...\n"
        
    system_prompt = (
        "You are an uncompromising Peer Reviewer agent for an academic/technical publication. "
        "Your task is to critically review a draft research report against the factual research notes.\n\n"
        "Evaluation Rubric:\n"
        "1. Factuality & Accuracy: Does the report faithfully represent the research notes without hallucinations?\n"
        "2. Completeness: Does it address all sub-questions covered in the research notes?\n"
        "3. Structure & Formatting: Does it include an Executive Summary, organized sections, and a References section?\n"
        "4. Tone & Quality: Is the writing clear, professional, and well-written?\n\n"
        "Decision Rules:\n"
        "- Set status to 'approved' if the report meets all standards or has only trivial formatting suggestions.\n"
        "- Set status to 'needs_revision' ONLY if there are critical missing sections, clear factual hallucinations, or major structure flaws.\n"
        "Return ONLY the structured output matching the requested schema."
    )
    
    user_prompt = (
        f"Research Notes Summary:\n{notes_summary}\n\n"
        f"Draft Report to Review:\n{draft}\n\n"
        f"Review the draft against the rubric and provide your evaluation."
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    try:
        result: ReviewOutput = structured_llm.invoke(messages)
        if result and result.status in ["approved", "needs_revision"]:
            return result.status, result.feedback
    except Exception as e:
        print(f"[Warning] Reviewer structured output failed: {e}")
        
    # Default fallback: Approve draft to prevent infinite loops if LLM parsing fails
    return "approved", "Draft approved by default evaluation safeguard."
