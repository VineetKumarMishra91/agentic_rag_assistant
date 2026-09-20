from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from backend import config

def web_search_answer(query: str) -> dict:
    search = DuckDuckGoSearchAPIWrapper(max_results=5)
    results = search.results(query, max_results=5)
    
    if not results:
        return {
            "status": "not_found",
            "message": "No web search results found.",
            "sources": []
        }
        
    context = "\n\n".join([f"Source ({r['link']}): {r['snippet']}" for r in results])
    
    prompt = PromptTemplate.from_template(
        "Answer the following question based on the web search results provided.\n\n"
        "Search Results:\n{context}\n\n"
        "Question: {query}\n"
        "Answer:"
    )
    
    llm = ChatGoogleGenerativeAI(model=config.GEMINI_CHAT_MODEL, google_api_key=config.GEMINI_API_KEY)
    chain = prompt | llm
    response = chain.invoke({"context": context, "query": query})
    
    answer_text = response.content
    if isinstance(answer_text, list):
        answer_text = "".join([b.get("text", "") for b in answer_text if isinstance(b, dict) and "text" in b])
    
    return {
        "status": "web_answer",
        "answer": answer_text,
        "sources": [r['link'] for r in results]
    }
