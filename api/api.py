from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_community.embeddings import OllamaEmbeddings
from typing import List, Optional
import os
from dotenv import load_dotenv
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="RAG Chatbot API",
    description="API for RAG-based chatbot using LangChain and Deepseek",
    version="1.0.0"
)

app.mount("/static", StaticFiles(directory="api/static"), name="static")

# Serve HTML UI
@app.get("/", include_in_schema=False)
def serve_ui():
    return FileResponse("api/static/chat_web.html")

# Constants
CHROMA_PATH = os.getenv("CHROMA_PATH", "/app/chroma_langchain_db")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")

PROMPT_TEMPLATE = """
Answer the question based only on the following context:

{context}

---

Answer the question based on the above context: {question}
"""

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Trong production, nên chỉ định domain cụ thể
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class QueryRequest(BaseModel):
    question: str
    k: Optional[int] = 5  # Số lượng documents để retrieve

class Source(BaseModel):
    id: str
    content: str
    score: float

class QueryResponse(BaseModel):
    answer: str
    sources: List[Source]
    success: bool
    message: Optional[str] = None

# Initialize embedding function and database (lazy loading)
embedding_function = None
db = None

def get_db():
    """Initialize database connection if not already done"""
    global embedding_function, db
    if db is None:
        embedding_function = OllamaEmbeddings(
            model="embeddinggemma:latest",
            base_url=OLLAMA_HOST
        )
        db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
    return db

@app.on_event("startup")
async def startup():
    try:
        get_db()
        print("✅ ChromaDB ready")
    except Exception as e:
        print("❌ DB init failed:", e)



@app.get("/health")
def health_check():
    get_db()
    return {
        "status": "ok"
        }
    

@app.post("/query", response_model=QueryResponse)
async def query_chatbot(request: QueryRequest):
    """
    Query the RAG chatbot
    
    - **question**: The question to ask
    - **k**: Number of similar documents to retrieve (default: 10)
    """
    try:
        if not request.question or request.question.strip() == "":
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        # Get database
        db = get_db()
        
        # Search similar documents
        results = db.similarity_search_with_score(request.question, k=request.k)
        
        # Log top results for debugging
        print(f"🔍 Top retrieval results for query '{request.question}':")
        for i, (doc, score) in enumerate(results[:5]):
            print(f"  {i+1}. Source: {doc.metadata.get('source', 'unknown')}, Page: {doc.metadata.get('page', 'unknown')}, Score: {score:.4f}")
            print(f"      Content preview: {doc.page_content[:100]}...")
        
        if not results:
            return QueryResponse(
                answer="Không tìm thấy thông tin liên quan trong cơ sở dữ liệu.",
                sources=[],
                success=True,
                message="No relevant documents found"
            )
        
        # Prepare context
        context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
        
        # Create prompt
        prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
        prompt = prompt_template.format(context=context_text, question=request.question)
        
        # Get response from LLM
        deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        if not deepseek_api_key:
            raise HTTPException(status_code=400, detail="DEEPSEEK_API_KEY environment variable not set")
        
        model = ChatOpenAI(
            model="deepseek-chat",
            api_key=deepseek_api_key,
            base_url="https://api.deepseek.com",
            temperature=0.0,
            timeout=60,
            max_retries=2
        )
        response = model.invoke(prompt)
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        # Format sources
        sources = [
            Source(
                id=doc.metadata.get("id", "unknown"),
                content=doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                score=float(score)
            )
            for doc, score in results
        ]
        
        return QueryResponse(
            answer=response_text,
            sources=sources,
            success=True
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.post("/query/simple")
async def query_simple(request: QueryRequest):
    """
    Simplified query endpoint that returns only the answer
    """
    try:
        response = await query_chatbot(request)
        return {
            "answer": response.answer,
            "success": response.success
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    """Get database statistics"""
    try:
        db = get_db()
        collection = db._collection
        count = collection.count()
        
        return {
            "total_documents": count,
            "database_path": CHROMA_PATH,
            "embedding_model": "embeddinggemma:latest",
            "llm_model": "deepseek-chat"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")

