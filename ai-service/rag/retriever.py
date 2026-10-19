from rag.embeddings import create_embedding
from rag.vector_store import get_collections

def retrieve(query: str, user_id: str, n_results: int = 5):
    if not query.strip(): return []
    personal, knowledge = get_collections()
    # Count only this user's records, never the size of the shared collection.
    owned = personal.get(where={'user_id': user_id}, include=[])['ids']
    knowledge_count = knowledge.count()
    if not owned and not knowledge_count: return []
    vector = create_embedding(query)
    evidence = []
    for collection, count, filters in [(personal, len(owned), {'user_id': user_id}), (knowledge, knowledge_count, None)]:
        if not count: continue
        options = {'query_embeddings': [vector], 'n_results': min(n_results, count), 'include': ['documents', 'metadatas', 'distances']}
        if filters: options['where'] = filters
        results = collection.query(**options)
        for document, metadata, distance in zip(results['documents'][0], results['metadatas'][0], results['distances'][0]):
            # Low-similarity passages should not become evidence just because top-k asks for them.
            if distance <= 1.2:
                evidence.append((document, metadata))
    return evidence
