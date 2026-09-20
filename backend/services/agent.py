from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from backend import config
from backend.services.agent_tools import rag_search, mongo_lookup, create_task, web_search

def run_agent(query: str) -> dict:
    llm = ChatGoogleGenerativeAI(model=config.GEMINI_LITE_MODEL, google_api_key=config.GEMINI_API_KEY)
    
    tools = [rag_search, mongo_lookup, create_task, web_search]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", 
         "You are a helpful assistant. You have four tools: rag_search (for searching content of documents/videos/meetings), "
         "mongo_lookup (for finding metadata about uploaded files, like dates, names, or meeting summaries), "
         "create_task (for creating action items in the database), and "
         "web_search (for general knowledge and current topics outside the knowledge base).\n\n"
         "Bias towards using rag_search first for information retrieval. Only reach for web_search when the knowledge base search comes back empty or insufficient. "
         "IMPORTANT: ONLY call create_task when the user's request clearly and explicitly asks for a task or action item to be created. Do not create tasks speculatively based on meeting notes.\n\n"
         "When you answer, clearly state which tool you used to find the information or perform the action."),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])
    
    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, return_intermediate_steps=True)
    
    response = agent_executor.invoke({"input": query})
    
    tools_used = []
    for action, _ in response.get("intermediate_steps", []):
        tools_used.append(action.tool)
        
    answer_text = response.get("output", "")
    if isinstance(answer_text, list):
        answer_text = "".join([b.get("text", "") for b in answer_text if isinstance(b, dict) and "text" in b])
        
    return {
        "answer": answer_text,
        "tools_used": list(set(tools_used))
    }
