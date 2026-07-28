import os
from typing import List, Optional
from pydantic import BaseModel, Field
from agents.llm_factory import get_llm
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

class PlannerOutput(BaseModel):
    sub_questions: List[str] = Field(
        ..., 
        description="A list of 3 to 5 highly focused sub-questions to guide the research on the topic."
    )

def generate_plan(topic: str, past_context: Optional[str] = None) -> List[str]:
    """
    Generates a list of 3 to 5 research sub-questions for the given topic.
    If past research context is provided, it is integrated into the generation prompt.
    """
    llm = get_llm(temperature=0.1)
    
    # Enable structured output using the PlannerOutput schema
    structured_llm = llm.with_structured_output(PlannerOutput)
    
    system_prompt = (
        "You are an expert Research Planner agent. Your task is to break down a main research topic "
        "into 3 to 5 specific, distinct, and logical sub-questions that need to be answered to write a comprehensive report.\n"
        "Each sub-question should be clear, actionable, and cover a specific dimension of the topic (e.g., technical overview, applications, ethical considerations, future outlook).\n"
        "Return ONLY the structured output matching the requested schema."
    )
    
    context_str = f"\n\nContext from previous related research:\n{past_context}" if past_context else ""
    user_prompt = f"Main Topic: {topic}{context_str}\n\nGenerate 3 to 5 sub-questions to guide the research."
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    try:
        result: PlannerOutput = structured_llm.invoke(messages)
        if result and result.sub_questions:
            return result.sub_questions
    except Exception as e:
        print(f"[Warning] Planner structured output failed, falling back to default parsing: {e}")
        
    # Fallback default plan if structured output fails
    return [
        f"What are the core concepts and background of {topic}?",
        f"What are the key developments and state of the art in {topic}?",
        f"What are the main challenges, risks, or ethical concerns related to {topic}?",
        f"What is the future outlook and potential impact of {topic}?"
    ]
