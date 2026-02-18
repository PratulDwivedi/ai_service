"""API routes for procedure documentation and data insights."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.core.auth import get_user_id_from_token
from app.services.duckdb_service import get_db
from app.services.procedure_service import get_procedure_docs
from typing import Optional, List, Dict, Any

router = APIRouter(prefix="/api/docs", tags=["Documentation"])

class SQLExplanationRequest(BaseModel):
    """Request to explain a SQL query."""
    sql_query: str

class SQLExplanationResponse(BaseModel):
    """Response with SQL explanation."""
    sql_query: str
    explanation: str

class ProcedureDocRequest(BaseModel):
    """Request procedure documentation."""
    rpc_name: Optional[str] = None

class ProcedureDocResponse(BaseModel):
    """Procedure documentation response."""
    markdown: str
    procedures_count: int

class EmbeddingRequest(BaseModel):
    """Request to create an embedding."""
    text: str

class EmbeddingResponse(BaseModel):
    """Embedding response."""
    text: str
    embedding: Optional[List[float]]
    model: str = "text-embedding-3-small"

@router.post("/sql/explain", response_model=SQLExplanationResponse)
async def explain_sql(
    request: SQLExplanationRequest,
    user_id: str = Depends(get_user_id_from_token)
):
    """
    Explain a SQL query in natural language.
    
    Converts SQL queries to human-readable explanations.
    
    Example:
    ```
    SELECT COUNT(*) FROM assets WHERE condition = 'Fair'
    ```
    Becomes:
    ```
    Count the number of records. Filter records where condition = 'Fair'
    ```
    """
    db = get_db(user_id)
    explanation = db.sql_to_natural_language(request.sql_query)
    
    return SQLExplanationResponse(
        sql_query=request.sql_query,
        explanation=explanation
    )

@router.get("/procedures/{rpc_name}", response_model=Dict[str, Any])
async def get_procedure_docs_endpoint(
    rpc_name: str,
    user_id: str = Depends(get_user_id_from_token)
):
    """
    Get detailed documentation for an RPC procedure.
    
    Returns explanation of what the procedure does, parameters, return type,
    use cases, and field descriptions.
    
    Example:
    - GET /api/docs/procedures/fn_get_assets
    """
    proc_docs = get_procedure_docs()
    explanation = proc_docs.get_procedure_explanation(rpc_name)
    
    if not explanation:
        raise HTTPException(
            status_code=404,
            detail=f"No documentation found for procedure '{rpc_name}'"
        )
    
    return {
        "rpc_name": explanation.rpc_name,
        "description": explanation.description,
        "parameters": explanation.parameters,
        "returns": explanation.returns,
        "use_cases": explanation.use_cases,
        "fields_explained": explanation.fields_explained,
        "example_response": explanation.example_response
    }

@router.get("/procedures", response_model=Dict[str, Any])
async def list_all_procedures(
    user_id: str = Depends(get_user_id_from_token)
):
    """
    List all documented RPC procedures.
    
    Returns a summary of all available procedures with their descriptions.
    """
    proc_docs = get_procedure_docs()
    procedures = {}
    
    # Get all registered procedures
    for rpc_name, explanation in proc_docs.procedures_db.items():
        procedures[rpc_name] = {
            "description": explanation.description,
            "returns": explanation.returns,
            "use_cases_count": len(explanation.use_cases)
        }
    
    return {
        "procedures": procedures,
        "total_count": len(procedures)
    }

@router.get("/procedures/{rpc_name}/markdown")
async def get_procedure_markdown(
    rpc_name: str,
    user_id: str = Depends(get_user_id_from_token)
):
    """
    Get procedure documentation as Markdown.
    
    Returns formatted Markdown documentation that can be saved to GitHub.
    """
    proc_docs = get_procedure_docs()
    markdown = proc_docs.generate_markdown_docs(rpc_name)
    
    if "No procedures documented" in markdown:
        raise HTTPException(
            status_code=404,
            detail=f"No documentation found for procedure '{rpc_name}'"
        )
    
    return {
        "rpc_name": rpc_name,
        "markdown": markdown,
        "format": "markdown"
    }

@router.post("/embeddings", response_model=EmbeddingResponse)
async def create_embedding(
    request: EmbeddingRequest,
    user_id: str = Depends(get_user_id_from_token)
):
    """
    Create an embedding for text using OpenAI API.
    
    Converts text to a vector representation for semantic search/similarity.
    Requires OPENAI_API_KEY environment variable.
    
    Example:
    ```
    {
        "text": "4th FLOOR furniture fixture at JW Marriott"
    }
    ```
    
    Response:
    ```
    {
        "text": "4th FLOOR furniture fixture at JW Marriott",
        "embedding": [0.001234, -0.005678, ...],
        "model": "text-embedding-3-small"
    }
    ```
    """
    db = get_db(user_id)
    embedding = db.create_embedding(request.text)
    
    if not embedding:
        raise HTTPException(
            status_code=500,
            detail="Failed to create embedding. Check OPENAI_API_KEY configuration."
        )
    
    return EmbeddingResponse(
        text=request.text,
        embedding=embedding,
        model="text-embedding-3-small"
    )

@router.post("/field/{rpc_name}/{field_name}")
async def get_field_explanation(
    rpc_name: str,
    field_name: str,
    user_id: str = Depends(get_user_id_from_token)
):
    """
    Get explanation for a specific field in a procedure's response.
    
    Example:
    - GET /api/docs/field/fn_get_assets/category
    """
    proc_docs = get_procedure_docs()
    explanation = proc_docs.explain_response_field(rpc_name, field_name)
    
    if not explanation:
        raise HTTPException(
            status_code=404,
            detail=f"No explanation found for field '{field_name}' in procedure '{rpc_name}'"
        )
    
    return {
        "rpc_name": rpc_name,
        "field_name": field_name,
        "explanation": explanation
    }

@router.get("/all-procedures/markdown")
async def get_all_procedures_markdown(
    user_id: str = Depends(get_user_id_from_token)
):
    """
    Get all procedure documentation as Markdown.
    
    Returns complete documentation for all procedures in Markdown format
    suitable for saving to GitHub.
    """
    proc_docs = get_procedure_docs()
    markdown = proc_docs.generate_markdown_docs()
    
    return {
        "markdown": markdown,
        "format": "markdown",
        "note": "Save this markdown content to GitHub as RPC_PROCEDURES.md"
    }

@router.post("/table/{table_name}/embeddings")
async def add_embeddings_to_table(
    table_name: str,
    text_column: str = "name",
    user_id: str = Depends(get_user_id_from_token)
):
    """
    Add embeddings to a text column in a table.
    
    Creates embeddings for text in a column, enabling semantic search.
    This is an expensive operation (API calls per row).
    
    Args:
        table_name: DuckDB table name
        text_column: Column containing text to embed (default: 'name')
    """
    db = get_db(user_id)
    
    # Check if table exists
    tables = db.list_tables()
    if table_name not in tables:
        raise HTTPException(
            status_code=404,
            detail=f"Table '{table_name}' not found"
        )
    
    success = db.add_embeddings_column(table_name, text_column)
    
    if not success:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add embeddings to table '{table_name}'"
        )
    
    return {
        "table_name": table_name,
        "text_column": text_column,
        "embedding_column": "embedding",
        "message": "Embeddings added successfully",
        "note": "Embeddings stored in embedding column as JSON"
    }
