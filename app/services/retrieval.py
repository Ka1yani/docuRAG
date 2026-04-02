from sqlalchemy.orm import Session
from sqlalchemy import text
from app.schemas import ChunkResponse, Citation

def retrieve_context(query: str, db: Session, top_k: int = 5, similarity_threshold: float = 0.1) -> list[ChunkResponse]:
    """
    Combines Full-Text Search (tsvector) and Trigram similarity (pg_trgm) to retrieve the best chunks.
    """
    
    # We query the database using raw SQL to leverage PostgreSQL specific functions cleanly.
    # We will compute a combined score:
    # TS_RANK for exact semantic match + SIMILARITY for fuzzy keyword block matching
    
    sql_query = text("""
        SELECT 
            id,
            document_id,
            file_name,
            page_number,
            content,
            ts_rank(content_vector, plainto_tsquery('english', :query)) AS rank,
            similarity(content, :query) AS sim_score
        FROM document_chunks
        WHERE 
            content_vector @@ plainto_tsquery('english', :query)
            OR similarity(content, :query) > :threshold
        ORDER BY (ts_rank(content_vector, plainto_tsquery('english', :query)) + similarity(content, :query)) DESC
        LIMIT :top_k
    """)
    
    results = db.execute(sql_query, {
        "query": query, 
        "threshold": similarity_threshold,
        "top_k": top_k
    }).fetchall()
    
    retrieved_chunks = []
    for row in results:
        # Calculate combined score for our records
        score = (row.rank or 0) + (row.sim_score or 0)
        
        # Don't add chunks that have an extremely low score despite passing the OR condition
        if score < similarity_threshold:
            continue
            
        retrieved_chunks.append(
            ChunkResponse(
                content=row.content,
                citation=Citation(file_name=row.file_name, page_number=row.page_number),
                similarity_score=score
            )
        )
        
    return retrieved_chunks
