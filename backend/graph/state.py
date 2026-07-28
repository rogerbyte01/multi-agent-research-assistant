from typing import TypedDict, List, Dict, Any

class ResearchState(TypedDict):
    """
    Shared state schema for the research assistant graph.
    """
    topic: str
    plan: List[str]  # List of sub-questions from the Planner
    research_notes: List[Dict[str, Any]]  # List of research notes (each dict has: sub_question, findings, sources)
    draft: str  # Markdown text of the report
    review_feedback: str  # Critique from the Reviewer
    review_status: str  # "approved" or "needs_revision"
    revision_count: int  # Tracking number of revisions to prevent infinite loops
