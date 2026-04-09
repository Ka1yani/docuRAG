from sqlalchemy.orm import Session
from sqlalchemy import text
from app.schemas import ChunkResponse, Citation
from app.services.llm_service import get_embedding
from app.logger import logger

def retrieve_context(query: str, db: Session, top_k: int = 5, similarity_threshold: float = 0.5, embedded_query: list[float] = None) -> list[ChunkResponse]:
    """
    Uses DuckDB array_cosine_similarity to retrieve semantically similar chunks.
    """
    if not embedded_query:
        embedded_query = get_embedding(query)
        
    if not embedded_query:
        logger.error("Failed to embed query, returning empty results.")
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
    
    # We cast the python list into a string which DuckDB automatically parses back into an array
    results = db.execute(sql_query, {
        "query_embedding": str(embedded_query), 
        "top_k": top_k
    }).fetchall()
    
    logger.info(f"DuckDB retrieved {len(results)} chunks for query.")
    if results and results[0].sim_score < similarity_threshold:
        logger.warning(f"Very low vector confidence detected! Top score: {results[0].sim_score:.4f}")

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
