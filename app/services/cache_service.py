import json
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models import SemanticCache
from app.schemas import ChunkResponse, Citation
from app.services.llm_service import get_embedding
from app.logger import logger

def check_semantic_cache(query: str, db: Session, similarity_threshold: float = 0.95):
    """
    Checks DuckDB for mathematically similar queries.
    Returns: (cached_answer, cached_chunks, cached_citations), embedded_query
    """
    embedded_query = get_embedding(query)
    if not embedded_query:
        return (None, None, None), None
        
    sql_query = text("""
        SELECT 
            response_text,
            retrieved_chunks_json,
            citations_json,
            array_cosine_similarity(CAST(query_vector AS FLOAT[768]), CAST(:query_embedding AS FLOAT[768])) AS sim_score
        FROM semantic_cache
        ORDER BY sim_score DESC
        LIMIT 1
    """)
    
    try:
        result = db.execute(sql_query, {"query_embedding": str(embedded_query)}).fetchone()
        
        if result and result.sim_score >= similarity_threshold:
            logger.info(f"[ENTERPRISE CACHE HIT] Similar query found! (Score: {result.sim_score:.4f})")
            
            final_answer = result.response_text
            chunks_data = json.loads(result.retrieved_chunks_json)
            cites_data = json.loads(result.citations_json)
            
            chunks = [ChunkResponse(**c) for c in chunks_data]
            citations = [Citation(**c) for c in cites_data]
            
            return (final_answer, chunks, citations), embedded_query
    except Exception as e:
        # Fails safely if table is missing or structure is wrong
        logger.debug(f"Cache bypass due to exception: {e}")
        pass
            
    return (None, None, None), embedded_query

def store_semantic_cache(query: str, embedded_query: list[float], answer: str, chunks: list, citations: list, db: Session):
    """
    Saves generated mathematical answers to the cache for future users.
    """
    try:
        # Handle dict or model_dump for backwards/forwards pydantic compatibility
        chunks_json = json.dumps([c.dict() if hasattr(c, "dict") else c.model_dump() for c in chunks])
        cites_json = json.dumps([c.dict() if hasattr(c, "dict") else c.model_dump() for c in citations])
        
        cache_entry = SemanticCache(
            query_text=query,
            query_vector=str(embedded_query),
            response_text=answer,
            retrieved_chunks_json=chunks_json,
            citations_json=cites_json
        )
        db.add(cache_entry)
        db.commit()
        logger.debug("Successfully committed query branch to enterprise cache.")
    except Exception as e:
        logger.error(f"Failed to cache generated response: {e}")
