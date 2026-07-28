import os
from typing import List, Dict, Any, Tuple
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

class ReviewerOutput(BaseModel):
    """
    Structured output structure for the Reviewer agent.
    """
    review_status: str = Field(
        ...,
        description="The status of the review. Must be exactly 'approved' or 'needs_revision'."
    )
    review_feedback: str = Field(
        ...,
        description="Detailed, constructive feedback on the draft, focusing on factual grounding in the research notes, structure, and completeness. If approved, summarize why."
    )

def review_report(
    draft: str,
    research_notes: List[Dict[str, Any]],
    revision_count: int = 0
) -> Tuple[str, str]:
    """
    Critiques the draft report against a rubric (factual grounding, structure, completeness).
    If revision_count >= 2, forces approval to avoid infinite loops.
    Returns:
        review_status (str): "approved" or "needs_revision"
        review_feedback (str): specific feedback/critique
    """
    # Force approval if revision limit reached
    if revision_count >= 2:
        return (
            "approved",
            f"Draft automatically approved. Revision limit reached ({revision_count} revisions)."
        )
        
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is not set.")
        
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=google_api_key,
        temperature=0.0  # Set to 0.0 for strict, objective rubric validation
    )
    
    # Enable structured output
    structured_llm = llm.with_structured_output(ReviewerOutput)
    
    # Format original research notes for comparison
    notes_context = ""
    for idx, note in enumerate(research_notes):
        notes_context += (
            f"### Sub-question {idx+1}: {note['sub_question']}\n"
            f"Factual Source Findings:\n{note['findings']}\n\n"
        )
        
    system_prompt = (
        "You are an objective Reviewer agent. Your task is to critique the written draft report against a strict rubric:\n"
        "1. Factual Grounding: Is the report strictly supported by the provided factual findings? Does it introduce unsupported claims?\n"
        "2. Structure: Is the report well-organized with clear headings, introductory sections, and reference lists?\n"
        "3. Completeness: Does it address all planned research sub-questions?\n\n"
        "You must output either 'approved' or 'needs_revision'. Be strict but constructive."
    )
    
    user_prompt = (
        f"--- Original Factual Research Notes ---\n{notes_context}\n\n"
        f"--- Draft Report under Review ---\n{draft}\n\n"
        f"Please critique the draft against the research notes. If everything is accurate, well-structured, "
        f"and complete, set status to 'approved'. Otherwise, set it to 'needs_revision' and specify feedback."
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    result: ReviewerOutput = structured_llm.invoke(messages)
    
    # Standardize the status output in case LLM outputs something close
    status = result.review_status.strip().lower()
    if "approved" in status:
        status = "approved"
    else:
        status = "needs_revision"
        
    return status, result.review_feedback
