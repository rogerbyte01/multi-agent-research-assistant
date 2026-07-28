import os
from dotenv import load_dotenv

load_dotenv()

def get_llm(temperature: float = 0.1):
    """
    Returns an LLM client instance.
    Prefers Groq (llama-3.3-70b-versatile) if GROQ_API_KEY is present.
    Otherwise falls back to Google Gemini (gemini-3.5-flash).
    """
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key and groq_key.strip():
        from langchain_groq import ChatGroq
        return ChatGroq(
            model_name="llama-3.3-70b-versatile",
            groq_api_key=groq_key.strip(),
            temperature=temperature
        )
        
    google_key = os.getenv("GOOGLE_API_KEY")
    if google_key and google_key.strip():
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model="gemini-3.5-flash",
            google_api_key=google_key.strip(),
            temperature=temperature
        )
        
    raise ValueError("Neither GROQ_API_KEY nor GOOGLE_API_KEY is configured in environment variables.")
