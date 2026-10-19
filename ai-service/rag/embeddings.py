from llm.openai_client import get_client, get_embedding_model
from rag.vector_store import get_collections

def create_embeddings(texts: list[str]) -> list[list[float]]:
    if not texts: return []
    model = get_embedding_model()
    result = []
    for start in range(0, len(texts), 64):
        batch = texts[start:start + 64]
        response = get_client().embeddings.create(model=model, input=batch)
        result.extend(item.embedding for item in sorted(response.data, key=lambda item: item.index))
    if len(result) != len(texts): raise RuntimeError('Embedding provider returned an incomplete batch')
    return result

def create_embedding(text: str) -> list[float]:
    return create_embeddings([text])[0]

def store_chunks(chunks: list[dict], source: str, user_id: str, report_id: str, report_date: str = '') -> int:
    collection, _ = get_collections()
    existing = collection.get(where={'$and': [{'user_id': user_id}, {'report_id': report_id}]}, include=[])
    if existing['ids']:
        return len(existing['ids'])
    if not chunks: return 0
    vectors = create_embeddings([chunk['text'] for chunk in chunks])
    collection.upsert(
        ids=[f'{user_id}:{report_id}:{chunk["chunk_index"]}' for chunk in chunks],
        embeddings=vectors,
        documents=[chunk['text'] for chunk in chunks],
        metadatas=[{'user_id': user_id, 'report_id': report_id, 'filename': source, 'source': source, 'page': chunk['page'], 'report_date': report_date, 'chunk_index': chunk['chunk_index'], 'kind': 'personal', 'extraction_method': chunk['extraction_method']} for chunk in chunks],
    )
    return len(chunks)
