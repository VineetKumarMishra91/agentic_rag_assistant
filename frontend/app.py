import streamlit as st
import requests

st.set_page_config(page_title="Agentic RAG Assistant", layout="wide")

if "sources" not in st.session_state:
    st.session_state.sources = []
if "tab2_chat" not in st.session_state:
    st.session_state.tab2_chat = []
if "tab3_chat" not in st.session_state:
    st.session_state.tab3_chat = []

st.title("Agentic RAG Assistant")

tab1, tab2, tab3 = st.tabs(["Upload", "Document/Video Chat", "Ask Anything"])

# --- TAB 1: UPLOAD ---
with tab1:
    st.header("Upload Document or Video")
    uploaded_file = st.file_uploader("Choose a file (PDF, DOCX, TXT, MP4, MP3, WAV, etc.)")
    if st.button("Upload"):
        if uploaded_file:
            file_name = uploaded_file.name
            ext = file_name.split('.')[-1].lower()
            is_video = ext in ['mp4', 'mov', 'avi', 'mp3', 'wav', 'm4a']
            endpoint = "http://127.0.0.1:8000/upload/video" if is_video else "http://127.0.0.1:8000/upload"
            
            with st.spinner("Uploading and processing..."):
                files = {"file": (file_name, uploaded_file.getvalue())}
                resp = requests.post(endpoint, files=files)
                
                if resp.status_code == 200:
                    data = resp.json()
                    st.success("Upload successful!")
                    source_id = data.get("source_id")
                    st.session_state.sources.append({"source_id": source_id, "name": file_name})
                    
                    if is_video:
                        st.subheader("Summary")
                        st.write(data.get("summary"))
                        st.subheader("Action Items")
                        for item in data.get("action_items", []):
                            st.write(f"- {item}")
                else:
                    st.error(f"Upload failed: {resp.text}")
        else:
            st.warning("Please select a file first.")

# --- TAB 2: DOCUMENT/VIDEO CHAT ---
with tab2:
    st.header("Chat about a specific source")
    
    # Fetch all historical sources from MongoDB via backend API
    try:
        sources_resp = requests.get("http://127.0.0.1:8000/sources")
        if sources_resp.status_code == 200:
            db_sources = sources_resp.json().get("sources", [])
        else:
            db_sources = []
    except Exception:
        db_sources = []
        
    if not db_sources:
        st.info("No sources found in the database. Please upload a source in the Upload tab first.")
    else:
        selected_source = st.selectbox(
            "Select a source", 
            db_sources, 
            format_func=lambda x: f"{x['name']} ({x.get('source_type', 'unknown')})"
        )
        source_id = selected_source["source_id"]
        
        # Display chat history for this source
        for msg in st.session_state.tab2_chat:
            if msg.get("source_id") == source_id:
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])
                    
        # Check if we should offer web search for the LAST message of THIS source
        source_msgs = [m for m in st.session_state.tab2_chat if m.get("source_id") == source_id]
        if source_msgs:
            last_msg = source_msgs[-1]
            if last_msg["role"] == "assistant" and last_msg.get("offer_web_search") and not last_msg.get("web_search_done"):
                if st.button("Search the Web for this query"):
                    with st.spinner("Searching the web..."):
                        resp = requests.post(f"http://127.0.0.1:8000/documents/{source_id}/chat/web-search", json={"query": last_msg["query"]})
                        if resp.status_code == 200:
                            data = resp.json()
                            st.session_state.tab2_chat.append({
                                "role": "assistant", 
                                "content": data.get("answer", ""), 
                                "source_id": source_id
                            })
                            last_msg["web_search_done"] = True
                            st.rerun()
                        else:
                            st.error(f"Web search failed: {resp.text}")

        query2 = st.chat_input("Ask about this document...", key="tab2_input")
        if query2:
            st.session_state.tab2_chat.append({"role": "user", "content": query2, "source_id": source_id})
            with st.chat_message("user"):
                st.write(query2)
                
            with st.spinner("Thinking..."):
                resp = requests.post(f"http://127.0.0.1:8000/documents/{source_id}/chat", json={"query": query2})
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("status") == "not_found":
                        ans = data.get("message", "Not found.")
                        st.session_state.tab2_chat.append({
                            "role": "assistant", 
                            "content": ans, 
                            "source_id": source_id, 
                            "offer_web_search": data.get("offer_web_search"),
                            "query": query2,
                            "web_search_done": False
                        })
                    else:
                        ans = data.get("answer", "")
                        st.session_state.tab2_chat.append({"role": "assistant", "content": ans, "source_id": source_id})
                else:
                    st.error(f"Error: {resp.text}")
            st.rerun()

# --- TAB 3: ASK ANYTHING (AGENT) ---
with tab3:
    st.header("Ask Anything (Agent)")
    for msg in st.session_state.tab3_chat:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if msg.get("tools_used"):
                with st.expander("Tools Used"):
                    st.write(msg["tools_used"])
                    
    query3 = st.chat_input("Ask the agent...", key="tab3_input")
    if query3:
        st.session_state.tab3_chat.append({"role": "user", "content": query3})
        with st.chat_message("user"):
            st.write(query3)
            
        with st.spinner("Agent is thinking..."):
            resp = requests.post("http://127.0.0.1:8000/assistant/chat", json={"query": query3})
            if resp.status_code == 200:
                data = resp.json()
                ans = data.get("answer", "")
                tools = data.get("tools_used", [])
                st.session_state.tab3_chat.append({"role": "assistant", "content": ans, "tools_used": tools})
            else:
                st.error(f"Error: {resp.text}")
        st.rerun()
