import json
import datetime
from langchain_core.tools import tool
from backend.services.rag_pipeline import get_source_retriever, get_vectorstore, RELEVANCE_SCORE_THRESHOLD
from backend.services.mongo_client import get_mongo_db, log_tool_call
from backend.services.web_search import web_search_answer

@tool
def rag_search(query: str) -> str:
    """Searches the knowledge base for information across all documents, meetings, and videos."""
    vectorstore = get_vectorstore()
    score_results = vectorstore.similarity_search_with_score(query, k=6)
    
    has_relevant = any(score <= RELEVANCE_SCORE_THRESHOLD for _, score in score_results)
    if not has_relevant or not score_results:
        return "No relevant information found in the knowledge base."
        
    base_retriever = get_source_retriever(source_id=None)
    docs = base_retriever.invoke(query)
        
    results = []
    for d in docs:
        source_name = d.metadata.get("source_name", "Unknown Source")
        source_type = d.metadata.get("source_type", "Unknown Type")
        results.append(f"Source: {source_name} ({source_type})\nContent: {d.page_content}")
        
    return "\n\n".join(results)

@tool
def mongo_lookup(collection_name: str, filter_description: str) -> str:
    """
    Queries the MongoDB metadata collections to find information about ingested documents or media.
    Args:
        collection_name: Either 'documents' or 'media'.
        filter_description: A simple keyword to search in filenames/summaries (e.g., 'meeting', 'project').
    """
    if collection_name not in ["documents", "media"]:
        return "Error: Invalid collection name. Must be 'documents' or 'media'."
        
    db = get_mongo_db()
    collection = db[collection_name]
    
    keyword = filter_description.lower().strip()
    
    query = {
        "$or": [
            {"source_name": {"$regex": keyword, "$options": "i"}},
            {"summary": {"$regex": keyword, "$options": "i"}},
            {"filename": {"$regex": keyword, "$options": "i"}}
        ]
    }
    
    cursor = collection.find(query).limit(10)
    results = list(cursor)
    
    if not results:
        return f"No matching records found in the '{collection_name}' collection for '{filter_description}'."
        
    out = []
    for r in results:
        name = r.get("source_name") or r.get("filename", "Unknown")
        status = r.get("status", "Unknown")
        summary = r.get("summary", "")
        if summary:
            out.append(f"Name: {name}, Status: {status}, Summary: {summary}")
        else:
            out.append(f"Name: {name}, Status: {status}")
            
    return "\n".join(out)

@tool
def create_task(description: str, assignee: str, source_id: str) -> str:
    """
    Creates a new action item or task in the database.
    Args:
        description: The task description.
        assignee: The person responsible for the task.
        source_id: The ID of the document, video, or meeting this task originated from (if any).
    """
    db = get_mongo_db()
    collection = db["action_items"]
    
    doc = {
        "description": description,
        "assignee": assignee,
        "source_id": source_id,
        "status": "open",
        "created_at": datetime.datetime.utcnow()
    }
    
    result = collection.insert_one(doc)
    new_id = str(result.inserted_id)
    
    output_msg = f"Task created successfully with ID: {new_id}"
    
    log_tool_call(
        tool_name="create_task",
        tool_input={"description": description, "assignee": assignee, "source_id": source_id},
        tool_output=output_msg,
        timestamp=datetime.datetime.utcnow()
    )
    
    return output_msg

@tool
def web_search(query: str) -> str:
    """
    Use only when rag_search and mongo_lookup don't have relevant information, or the question is about general/current topics outside the user's own data.
    Searches the web using DuckDuckGo and returns a summarized answer.
    """
    result = web_search_answer(query)
    answer = result.get("answer", "")
    sources = result.get("sources", [])
    if sources:
        return f"{answer}\n\nSources: {', '.join(sources)}"
    return answer
