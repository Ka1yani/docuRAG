import os
import requests
from app.schemas import ChunkResponse

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL_NAME = os.getenv("MODEL_NAME", "mistral:7b")

def generate_answer(query: str, context_chunks: list[ChunkResponse]) -> str:
    if not context_chunks:
        return "Answer not found in provided documents."

    # Build Context String
    context_text = "\n\n".join(
        [f"Source [{chunk.citation.file_name} - Page {chunk.citation.page_number}]: {chunk.content}" 
         for chunk in context_chunks]
    )

    prompt = f"""You are a question-answering system.
Answer ONLY from the provided context.
Do NOT use outside knowledge.
If the answer is not present, say:
'Answer not found in provided documents.'

Context:
{context_text}

Question:
{query}

Answer:"""

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=300)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "").strip()
    except Exception as e:
        print(f"Error calling Ollama API: {e}")
        return "An error occurred while generating the answer. Make sure Ollama is running."
