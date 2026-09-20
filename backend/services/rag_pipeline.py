import os
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import PromptTemplate

from backend import config

def ingest_document(file_path: str, source_id: str, original_filename: str = None) -> int:
    if original_filename is None:
        original_filename = os.path.basename(file_path)
    
    ext = os.path.splitext(original_filename)[1].lower()
    
    if ext == '.pdf':
        loader = PyPDFLoader(file_path)
    elif ext in ['.docx', '.doc']:
        loader = Docx2txtLoader(file_path)
    elif ext == '.txt':
        loader = TextLoader(file_path)
    else:
        raise ValueError(f"Unsupported file extension: {ext}")
        
    docs = loader.load()
    return _chunk_and_embed(docs, source_id, "document", original_filename)

def _chunk_and_embed(docs, source_id: str, source_type: str, source_name: str) -> int:
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    splits = text_splitter.split_documents(docs)
    
    for i, split in enumerate(splits):
        split.metadata.update({
            "source_id": source_id,
            "source_type": source_type,
            "source_name": source_name,
            "chunk_index": i
        })
        
    embeddings = GoogleGenerativeAIEmbeddings(model=config.GEMINI_EMBEDDING_MODEL, google_api_key=config.GEMINI_API_KEY)
    
    Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        collection_name="knowledge_base",
        persist_directory=config.CHROMA_PERSIST_DIR
    )
    
    return len(splits)

def ingest_media_transcript(transcript_text: str, source_id: str, source_type: str, source_name: str) -> None:
    from langchain_core.documents import Document
    docs = [Document(page_content=transcript_text)]
    _chunk_and_embed(docs, source_id, source_type, source_name)

RELEVANCE_SCORE_THRESHOLD = 0.5  # Cosine distance threshold; lower is more similar. May need empirical tuning.

def get_vectorstore():
    embeddings = GoogleGenerativeAIEmbeddings(model=config.GEMINI_EMBEDDING_MODEL, google_api_key=config.GEMINI_API_KEY)
    return Chroma(
        collection_name="knowledge_base",
        persist_directory=config.CHROMA_PERSIST_DIR,
        embedding_function=embeddings
    )

def get_source_retriever(source_id: str = None):
    vectorstore = get_vectorstore()
    search_kwargs = {
        "k": 6,
        "fetch_k": 20,
        "lambda_mult": 0.5,
    }
    if source_id:
        search_kwargs["filter"] = {"source_id": source_id}
        
    return vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs=search_kwargs
    )

def answer_from_source(query: str, source_id: str) -> dict:
    vectorstore = get_vectorstore()
    
    # Check absolute relevance first before falling back to MMR relative diversity
    search_kwargs = {"k": 6}
    if source_id:
        search_kwargs["filter"] = {"source_id": source_id}
        
    score_results = vectorstore.similarity_search_with_score(query, **search_kwargs)
    
    # Chroma default is L2/cosine distance where a lower score = more similar
    has_relevant = any(score <= RELEVANCE_SCORE_THRESHOLD for _, score in score_results)
    
    if not has_relevant or not score_results:
        return {
            "status": "not_found",
            "message": "No relevant information found in the document.",
            "offer_web_search": True
        }
        
    base_retriever = get_source_retriever(source_id)
    docs = base_retriever.invoke(query)
        
    context = "\n\n".join([d.page_content for d in docs])
    
    prompt = PromptTemplate.from_template(
        "Answer the question based ONLY on the following context:\n\n{context}\n\nQuestion: {query}\nAnswer:"
    )
    
    llm = ChatGoogleGenerativeAI(model=config.GEMINI_CHAT_MODEL, google_api_key=config.GEMINI_API_KEY)
    chain = prompt | llm
    response = chain.invoke({"context": context, "query": query})
    
    answer_text = response.content
    if isinstance(answer_text, list):
        answer_text = "".join([b.get("text", "") for b in answer_text if isinstance(b, dict) and "text" in b])
    
    return {
        "status": "found",
        "answer": answer_text,
        "sources": [d.page_content for d in docs]
    }
