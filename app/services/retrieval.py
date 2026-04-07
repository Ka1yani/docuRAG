from sqlalchemy.orm import Session
from sqlalchemy import text
from app.schemas import ChunkResponse, Citation
from app.services.llm_service import get_embedding

def retrieve_context(query: str, db: Session, top_k: int = 5, similarity_threshold: float = 0.5) -> list[ChunkResponse]:
    """
    Uses pgvector cosine distance to retrieve semantically similar chunks.
    """
    embedded_query = get_embedding(query)
    if not embedded_query:
        print("Failed to embed query, returning empty results.")
        return []
        
    # DuckDB array_cosine_similarity calculates similarity natively (higher is better)
    sql_query = text("""
        SELECT 
            id,
            document_id,
            file_name,
            page_number,
            content,
            array_cosine_similarity(CAST(content_vector AS FLOAT[768]), CAST(:query_embedding AS FLOAT[768])) AS sim_score
        FROM document_chunks
        WHERE content_vector IS NOT NULL
        ORDER BY sim_score DESC
        LIMIT :top_k
    """)
    
    # We cast the python list into a string which pgvector automatically parses
    results = db.execute(sql_query, {
        "query_embedding": str(embedded_query), 
        "top_k": top_k
    }).fetchall()
    
    retrieved_chunks = []
    for row in results:
        # Check against similarity threshold (closer to 1 is better)
        if row.sim_score < similarity_threshold:
            continue
            
        retrieved_chunks.append(
            ChunkResponse(
                content=row.content,
                citation=Citation(file_name=row.file_name, page_number=row.page_number),
                similarity_score=row.sim_score
            )
        )
        
    return retrieved_chunks
