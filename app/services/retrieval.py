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
        
    # We query the database using raw SQL to leverage PostgreSQL specific functions cleanly.
    # pgvector '<=>' calculates cosine distance. Lower distance = higher similarity.
    # We invert it (1 - distance) for a standard "similarity score" where 1 is perfect match.
    sql_query = text("""
        SELECT 
            id,
            document_id,
            file_name,
            page_number,
            content,
            1 - (content_vector <=> :query_embedding) AS sim_score
        FROM document_chunks
        WHERE content_vector IS NOT NULL
        ORDER BY content_vector <=> :query_embedding ASC
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
