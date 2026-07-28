import os
from typing import List, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from tools.search_tool import web_search
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

def perform_research(sub_questions: List[str]) -> List[Dict[str, Any]]:
    """
    For each sub-question:
    1. Runs a web search to fetch top 3 results.
    2. Synthesizes findings using Gemini, ensuring inline citations and source URL tracking.
    3. Returns a list of dicts with: sub_question, findings, sources.
    """
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is not set.")
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=google_api_key,
        temperature=0.0  # Use low temperature for research summaries to maximize factual accuracy
    )
    
    research_notes = []
    
    for question in sub_questions:
        # 1. Search the web
        try:
            search_results = web_search(question)
        except Exception as e:
            # Fallback in case search fails
            search_results = [{"title": "Error", "url": "", "snippet": f"Search failed: {str(e)}"}]
        
        # Format the search results as context for the LLM
        context_str = ""
        for idx, result in enumerate(search_results):
            context_str += (
                f"Source [{idx+1}]: {result.get('title', 'No Title')}\n"
                f"URL: {result.get('url', 'No URL')}\n"
                f"Snippet: {result.get('snippet', 'No Snippet')}\n\n"
            )
            
        system_prompt = (
            "You are a meticulous Researcher agent. Your goal is to synthesize the provided web search results "
            "to answer a specific sub-question. You must base your answer strictly on the provided sources. "
            "Use inline citations like [1], [2] to reference your sources, and list the source URLs clearly "
            "at the end of your findings."
        )
        
        user_prompt = (
            f"Sub-question to answer: {question}\n\n"
            f"Web Search Results:\n{context_str}\n"
            f"Please synthesize these results into a detailed, factually grounded answer with inline citations."
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # 2. Invoke Gemini for synthesis
        try:
            response = llm.invoke(messages)
            findings = response.content
        except Exception as e:
            findings = f"Failed to synthesize findings: {str(e)}"
        
        # 3. Store findings
        research_notes.append({
            "sub_question": question,
            "findings": findings,
            "sources": search_results
        })
        
    return research_notes
