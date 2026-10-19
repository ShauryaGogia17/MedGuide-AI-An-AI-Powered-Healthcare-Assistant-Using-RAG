from functools import lru_cache
import chromadb
from chromadb.config import Settings
from config import VECTOR_DB_PATH

@lru_cache
def get_collections():
    client = chromadb.PersistentClient(path=str(VECTOR_DB_PATH), settings=Settings(anonymized_telemetry=False))
    # Existing unowned legacy entries are deliberately excluded from these collections.
    return (
        client.get_or_create_collection(name='medguide_personal', metadata={'hnsw:space': 'cosine'}, embedding_function=None),
        client.get_or_create_collection(name='medguide_knowledge', metadata={'hnsw:space': 'cosine'}, embedding_function=None),
    )
