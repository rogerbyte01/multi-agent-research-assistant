import os
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

class PlannerOutput(BaseModel):
    """
    Structured output structure for the Planner agent.
    """
    sub_questions: List[str] = Field(
        ..., 
        description="A list of 3 to 5 highly focused sub-questions to guide the research on the topic."
    )

def generate_plan(topic: str, past_context: Optional[str] = None) -> List[str]:
    """
    Generates a list of 3 to 5 research sub-questions for the given topic.
    If past research context is provided, it is integrated into the generation prompt.
    """
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is not set.")
    
    # Initialize the LLM. Using gemini-2.5-flash as default.
    llm = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash",
        google_api_key=google_api_key,
        temperature=0.1
    )
    
    # Enable structured output using the PlannerOutput schema
    structured_llm = llm.with_structured_output(PlannerOutput)
    
    system_prompt = (
        "You are an expert Research Planner. Your task is to break down a main research topic "
        "into 3 to 5 distinct, highly focused sub-questions. These questions should cover the "
        "topic's core aspects, key facts, challenges, and recent developments. Avoid overlapping questions."
    )
    
    user_prompt = f"Main Research Topic: {topic}\n\n"
    if past_context:
        user_prompt += (
            f"Here is context from similar past research topics stored in memory. "
            f"Please build upon these topics to avoid duplication and dive deeper:\n{past_context}\n\n"
        )
    user_prompt += "Generate the list of sub-questions."
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    result: PlannerOutput = structured_llm.invoke(messages)
    return result.sub_questions
