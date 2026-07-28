import os
from typing import List, Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
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
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is not set.")
        
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=google_api_key,
        temperature=0.2  # Slightly higher temperature for more fluid, readable writing
    )
    
    # Format the research notes into context
    notes_context = ""
    for idx, note in enumerate(research_notes):
        notes_context += (
            f"### Section {idx+1}: {note['sub_question']}\n"
            f"{note['findings']}\n\n"
        )
        
    system_prompt = (
        "You are an expert Content Writer agent. Your task is to write a well-structured, professional, "
        "and comprehensive Markdown report based on the provided research findings. "
        "Ensure proper use of Markdown headings, bullet points, and clean typography. "
        "You must maintain and organize all inline citations (e.g. [1], [2]) and provide a "
        "complete, numbered References section at the very bottom based on the sources cited."
    )
    
    user_prompt = (
        f"Research Topic: {topic}\n\n"
        f"Detailed Research Findings for each sub-question:\n{notes_context}\n\n"
        f"Instructions:\n"
        f"1. Generate a comprehensive Markdown report with a compelling title.\n"
        f"2. Include an Executive Summary at the start.\n"
        f"3. Organize the body into logical sections corresponding to the sub-questions.\n"
        f"4. Consolidate and maintain inline citations throughout the body.\n"
        f"5. End with a unified 'References' section containing all original source URLs.\n"
    )
    
    # If this is a revision, append the feedback to the prompt
    if revision_count > 0 and review_feedback:
        user_prompt += (
            f"\n--- REVISION REQUIRED ---\n"
            f"This is revision #{revision_count}. A reviewer has critiqued the draft. "
            f"You MUST address and implement the following reviewer feedback to improve the report:\n"
            f"{review_feedback}\n"
            f"---------------------------\n"
        )
        
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    response = llm.invoke(messages)
    return response.content
