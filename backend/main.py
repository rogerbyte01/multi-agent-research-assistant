import os
import json
import logging
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

# Set up imports from local modules
from graph.build_graph import app_graph
from memory.chroma_memory import ChromaMemoryManager

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Multi-Agent Research Assistant API")

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ResearchRequest(BaseModel):
    topic: str

@app.get("/health")
async def health_check():
    """
    Simple health check endpoint.
    """
    return {"status": "ok", "service": "multi-agent-research-assistant"}

@app.get("/memory")
async def get_memory():
    """
    Lists past research topics and their details stored in ChromaDB.
    """
    try:
        memory_mgr = ChromaMemoryManager()
        topics = memory_mgr.list_all_topics()
        
        results = []
        for topic in topics:
            data = memory_mgr.get_report_by_topic(topic)
            if data:
                results.append({
                    "topic": data["topic"],
                    "sub_questions": data["sub_questions"],
                    "report": data["report"]
                })
        return {"topics": results}
    except Exception as e:
        logger.error(f"Error fetching memory list: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch memories: {str(e)}")

@app.get("/report/{topic}")
async def get_report(topic: str):
    """
    Retrieves a specific research report by topic name.
    """
    try:
        memory_mgr = ChromaMemoryManager()
        data = memory_mgr.get_report_by_topic(topic)
        if data:
            return {
                "topic": data["topic"],
                "sub_questions": data["sub_questions"],
                "report": data["report"]
            }
        else:
            raise HTTPException(status_code=404, detail=f"Report for topic '{topic}' not found.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching report for topic {topic}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch report: {str(e)}")

@app.post("/research")
async def run_research(request: ResearchRequest):
    """
    Streams research agent progress as Server-Sent Events (SSE) with keepalive pings.
    """
    async def event_generator():
        initial_state = {
            "topic": request.topic,
            "plan": [],
            "research_notes": [],
            "draft": "",
            "review_feedback": "",
            "review_status": "",
            "revision_count": 0
        }
        
        # 1. Notify that the Planner is starting
        yield {
            "event": "Planner",
            "data": json.dumps({"status": "running", "output": None})
        }
        
        last_state = initial_state
        
        try:
            # Stream events from LangGraph
            iterator = app_graph.astream(initial_state, stream_mode="updates")
            
            while True:
                try:
                    # Wait for next event or timeout after 15 seconds for keepalive
                    event = await asyncio.wait_for(iterator.__anext__(), timeout=15.0)
                    
                    if "planner" in event:
                        plan = event["planner"].get("plan", [])
                        last_state["plan"] = plan
                        yield {
                            "event": "Planner",
                            "data": json.dumps({"status": "done", "output": plan})
                        }
                        yield {
                            "event": "Researcher",
                            "data": json.dumps({"status": "running", "output": None})
                        }
                        
                    elif "researcher" in event:
                        notes = event["researcher"].get("research_notes", [])
                        last_state["research_notes"] = notes
                        yield {
                            "event": "Researcher",
                            "data": json.dumps({"status": "done", "output": notes})
                        }
                        yield {
                            "event": "Writer",
                            "data": json.dumps({"status": "running", "output": None})
                        }
                        
                    elif "writer" in event:
                        draft = event["writer"].get("draft", "")
                        rev_count = event["writer"].get("revision_count", last_state["revision_count"] + 1)
                        last_state["draft"] = draft
                        last_state["revision_count"] = rev_count
                        yield {
                            "event": "Writer",
                            "data": json.dumps({
                                "status": "done",
                                "output": {
                                    "draft": draft,
                                    "revision_count": rev_count
                                }
                            })
                        }
                        yield {
                            "event": "Reviewer",
                            "data": json.dumps({"status": "running", "output": None})
                        }
                        
                    elif "reviewer" in event:
                        status = event["reviewer"].get("review_status", "")
                        feedback = event["reviewer"].get("review_feedback", "")
                        last_state["review_status"] = status
                        last_state["review_feedback"] = feedback
                        yield {
                            "event": "Reviewer",
                            "data": json.dumps({
                                "status": "done",
                                "output": {
                                    "review_status": status,
                                    "review_feedback": feedback
                                }
                            })
                        }
                        # Check if the graph will route back to Writer
                        if status == "needs_revision" and last_state["revision_count"] < 2:
                            yield {
                                "event": "Writer",
                                "data": json.dumps({"status": "running", "output": None})
                            }
                            
                except asyncio.TimeoutError:
                    # Send a keepalive ping to prevent SSE connection drop
                    yield {
                        "event": "ping",
                        "data": json.dumps({"status": "keepalive", "message": "Processing..."})
                    }
                except StopAsyncIteration:
                    break
            
            # Graph execution is finished successfully. Save to long-term memory.
            if last_state.get("draft"):
                try:
                    memory_mgr = ChromaMemoryManager()
                    await asyncio.to_thread(
                        memory_mgr.save_research,
                        topic=last_state["topic"],
                        sub_questions=last_state["plan"],
                        report=last_state["draft"]
                    )
                except Exception as e:
                    logger.error(f"Failed to save research report to memory: {e}")
                    
            yield {
                "event": "complete",
                "data": json.dumps({
                    "topic": last_state["topic"],
                    "plan": last_state["plan"],
                    "report": last_state["draft"]
                })
            }
            
        except Exception as e:
            logger.error(f"Error during graph execution: {str(e)}")
            yield {
                "event": "error",
                "data": json.dumps({"message": str(e)})
            }
            
    return EventSourceResponse(event_generator())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
