import os
import json
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.api.types import Documents, Embeddings, EmbeddingFunction
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

class GeminiEmbeddingFunction(EmbeddingFunction):
    """
    Custom Chroma embedding function using langchain-google-genai.
    Avoids downloading heavy local models (like SentenceTransformers)
    by calling Google's embedding API.
    """
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is not set.")
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-04",
            google_api_key=api_key
        )

    def __call__(self, input: Documents) -> Embeddings:
        # embed_documents takes List[str] and returns List[List[float]]
        return self.embeddings.embed_documents(input)

class ChromaMemoryManager:
    """
    Handles persistence and retrieval of research reports to/from ChromaDB.
    """
    def __init__(self):
        # Allow configurable data directory to fix Docker / Render issues
        # Fall back to ./chroma_data if env var is missing
        self.db_path = os.environ.get('CHROMA_DATA_DIR', './chroma_data')
        
        self.client = chromadb.PersistentClient(path=self.db_path)
        self.emb_fn = GeminiEmbeddingFunction()
        
        # Get or create the collection for long-term memory
        self.collection = self.client.get_or_create_collection(
            name="research_memory",
            embedding_function=self.emb_fn
        )

    def save_research(self, topic: str, sub_questions: List[str], report: str) -> None:
        """
        Saves a completed research topic and report to the database.
        Use topic as the ID to avoid duplicates.
        """
        # Store metadata including sub-questions serialized as JSON
        metadata = {
            "topic": topic,
            "sub_questions": json.dumps(sub_questions)
        }
        
        self.collection.upsert(
            documents=[report],
            metadatas=[metadata],
            ids=[topic]
        )

    def search_similar(self, topic: str, limit: int = 2) -> List[Dict[str, Any]]:
        """
        Searches for similar past research topics in ChromaDB.
        Returns a list of dicts: {"topic": str, "sub_questions": List[str], "report": str}
        """
        # Return empty list if collection has no items to avoid empty query errors
        count = self.collection.count()
        if count == 0:
            return []
            
        # Limit cannot exceed available documents
        query_limit = min(limit, count)
        
        results = self.collection.query(
            query_texts=[topic],
            n_results=query_limit
        )
        
        similar_docs = []
        if results and results.get("documents") and len(results["documents"]) > 0:
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            
            for i in range(len(docs)):
                doc = docs[i]
                meta = metas[i]
                
                # Deserialize sub_questions list
                sub_qs = []
                if meta and "sub_questions" in meta:
                    try:
                        sub_qs = json.loads(meta["sub_questions"])
                    except Exception:
                        sub_qs = []
                        
                similar_docs.append({
                    "topic": meta.get("topic", "Unknown Topic") if meta else "Unknown Topic",
                    "sub_questions": sub_qs,
                    "report": doc
                })
                
        return similar_docs

    def list_all_topics(self) -> List[str]:
        """
        Retrieves a list of all unique topic names stored in the database.
        """
        count = self.collection.count()
        if count == 0:
            return []
            
        # Get all metadatas
        results = self.collection.get(include=["metadatas"])
        topics = []
        if results and results.get("metadatas"):
            for meta in results["metadatas"]:
                if meta and "topic" in meta:
                    topics.append(meta["topic"])
                    
        # Return unique list
        return list(set(topics))
        
    def get_report_by_topic(self, topic: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a specific report by its topic name.
        """
        results = self.collection.get(ids=[topic], include=["documents", "metadatas"])
        if results and results.get("documents") and len(results["documents"]) > 0:
            doc = results["documents"][0]
            meta = results["metadatas"][0]
            
            sub_qs = []
            if meta and "sub_questions" in meta:
                try:
                    sub_qs = json.loads(meta["sub_questions"])
                except Exception:
                    sub_qs = []
                    
            return {
                "topic": topic,
                "sub_questions": sub_qs,
                "report": doc
            }
        return None
