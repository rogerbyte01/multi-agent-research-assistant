import asyncio
from langgraph.graph import StateGraph, END
from graph.state import ResearchState
from agents.planner import generate_plan
from agents.researcher import perform_research
from agents.writer import generate_report
from agents.reviewer import review_report
from memory.chroma_memory import ChromaMemoryManager

async def planner_node(state: ResearchState) -> dict:
    """
    Planner Node:
    1. Queries ChromaDB for similar past topics.
    2. Constructs context and calls the planner agent to produce sub-questions.
    """
    def _planner():
        topic = state.get("topic", "")
        
        # Try querying ChromaDB memory for context
        past_context = None
        try:
            memory_mgr = ChromaMemoryManager()
            similar_past = memory_mgr.search_similar(topic, limit=2)
            if similar_past:
                past_context = "Summaries of past research:\n"
                for idx, item in enumerate(similar_past):
                    past_context += (
                        f"- Topic {idx+1}: {item['topic']}\n"
                        f"  Sub-questions: {', '.join(item['sub_questions'])}\n"
                        f"  Report Excerpt: {item['report'][:400]}...\n\n"
                    )
        except Exception as e:
            # Gracefully handle memory search errors
            print(f"[Warning] Failed to fetch past memory context: {e}")
            
        sub_questions = generate_plan(topic, past_context=past_context)
        return {"plan": sub_questions}
        
    return await asyncio.to_thread(_planner)

async def researcher_node(state: ResearchState) -> dict:
    """
    Researcher Node:
    Calls Tavily search and Gemini to synthesize findings for each sub-question.
    """
    def _researcher():
        notes = perform_research(state.get("plan", []))
        return {"research_notes": notes}
        
    return await asyncio.to_thread(_researcher)

async def writer_node(state: ResearchState) -> dict:
    """
    Writer Node:
    Generates a Markdown report, incorporating review feedback if it is a revision.
    """
    def _writer():
        draft = generate_report(
            topic=state.get("topic", ""),
            research_notes=state.get("research_notes", []),
            review_feedback=state.get("review_feedback"),
            revision_count=state.get("revision_count", 0)
        )
        return {
            "draft": draft,
            "revision_count": state.get("revision_count", 0) + 1
        }
        
    return await asyncio.to_thread(_writer)

async def reviewer_node(state: ResearchState) -> dict:
    """
    Reviewer Node:
    Critiques the draft against the factual notes and returns status & feedback.
    """
    def _reviewer():
        status, feedback = review_report(
            draft=state.get("draft", ""),
            research_notes=state.get("research_notes", []),
            revision_count=state.get("revision_count", 0)
        )
        return {
            "review_status": status,
            "review_feedback": feedback
        }
        
    return await asyncio.to_thread(_reviewer)

def route_after_review(state: ResearchState) -> str:
    """
    Conditional routing edge.
    Routes back to writer if review fails and revision count is under the limit.
    Otherwise routes to END.
    """
    status = state.get("review_status", "")
    rev_count = state.get("revision_count", 0)
    
    if status == "needs_revision" and rev_count < 2:
        return "writer"
    else:
        return END

# Build and compile StateGraph
workflow = StateGraph(ResearchState)

# Add Nodes
workflow.add_node("planner", planner_node)
workflow.add_node("researcher", researcher_node)
workflow.add_node("writer", writer_node)
workflow.add_node("reviewer", reviewer_node)

# Set Entry Point
workflow.set_entry_point("planner")

# Add Normal Transitions
workflow.add_edge("planner", "researcher")
workflow.add_edge("researcher", "writer")
workflow.add_edge("writer", "reviewer")

# Add Conditional Transition
workflow.add_conditional_edges(
    "reviewer",
    route_after_review,
    {
        "writer": "writer",
        END: END
    }
)

app_graph = workflow.compile()
