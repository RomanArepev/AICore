from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware  # Import CORSMiddleware
from pydantic import BaseModel
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import TextLoader
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from freshdesk_integration import FreshDeskIntegration
from product_pricing import ProductPricing
import os
import re

# Initialize FastAPI app
app = FastAPI(title="AI Query API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://79.132.143.108:5000"],  # Allow requests from this origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Pydantic models for request validation
class Query(BaseModel):
    text: str

class PriceRequest(BaseModel):
    product_code: str
    quantity: int

# Initialize ProductPricing
product_pricing = ProductPricing("products.csv")

# Set your OpenAI API key
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# Loading documents (the file should be in the same folder as the script)
loader = TextLoader("documents.txt")
documents = loader.load()

# Creating embeddings
embeddings = OpenAIEmbeddings()

# Creating FAISS vector store
vector_store = FAISS.from_documents(documents, embeddings)

# Setting up LLM and chains for processing queries
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.5)
retriever = vector_store.as_retriever()

# Setting up system prompts
system_prompt = (
    "First, determine if the provided context is relevant to the question. "
    "If it's relevant, use the context to answer the question concisely in three sentences maximum. "
    "If the context is not relevant, start your response with 'This is not related to the context, but...' and then provide a general answer based on your knowledge. "
    "If you don't know the answer at all, simply state that you don't know."
)
prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}")
])

# Creating a chain for processing documents and queries
question_answer_chain = create_stuff_documents_chain(llm, prompt)
retrieval_chain = create_retrieval_chain(retriever, question_answer_chain)

# Initialize FreshDesk integration
freshdesk = FreshDeskIntegration(llm=llm)

async def extract_cost_info(query_text: str) -> tuple:
    """Extract product code and quantity from cost query"""
    # Паттерн для поиска только слова "Cost"
    pattern = r"Cost"  # Изменено на просто "Cost"
    match = re.search(pattern, query_text)
    
    if match:
        # Возвращаем None, так как больше ничего не извлекаем
        return None, None
    return None, None

@app.post("/query")
async def process_query(query: Query):
    try:
        # Обработка обычного запроса
        initial_response = retrieval_chain.invoke({"input": query.text})
        first_answer = initial_response["answer"]
        
        # Возвращаем только ответ от API
        return {
            "answer": first_answer,
            "is_cost_query": False
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/calculate-price")
async def calculate_price(request: PriceRequest):
    try:
        result = product_pricing.calculate_price(
            product_code=request.product_code,
            quantity=request.quantity
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/products")
async def get_products():
    """Get list of all available products"""
    return product_pricing.get_all_products()

# For running the API server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)