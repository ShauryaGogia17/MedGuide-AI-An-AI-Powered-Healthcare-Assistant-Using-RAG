"""Explicit, idempotent ingestion of reviewed knowledge-base sources."""
import sys
import json
import hashlib
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'ai-service'))
from rag.vector_store import get_collections
from rag.embeddings import create_embeddings
from rag.chunker import chunk_pages
from extraction.pdf_extractor import extract_pages

def ingest():
    _, collection = get_collections()
    registry = json.loads((ROOT / 'knowledge-base/metadata/sources.json').read_text())
    for entry in registry:
        source_root = (ROOT / 'knowledge-base').resolve()
        path = (source_root / entry['path']).resolve()
        if not path.is_relative_to(source_root) or not path.is_file(): raise ValueError('Invalid knowledge source path')
        if not entry.get('url', '').startswith('https://'): raise ValueError('Knowledge sources need a public HTTPS attribution URL')
        key = hashlib.sha256(entry['path'].encode()).hexdigest()[:24]
        fingerprint = hashlib.sha256(path.read_bytes() + json.dumps(entry, sort_keys=True).encode()).hexdigest()
        existing = collection.get(where={'source_key': key}, include=['metadatas'])
        if existing['ids'] and all(m['fingerprint'] == fingerprint for m in existing['metadatas']):
            print(f'Unchanged: {path.name}')
            continue
        pages = extract_pages(str(path)) if path.suffix.lower() == '.pdf' else [{'page': 1, 'text': path.read_text()}]
        chunks = chunk_pages(pages)
        if not chunks: raise ValueError(f'Knowledge source is empty: {path.name}')
        embeddings = create_embeddings([c['text'] for c in chunks])
        ids = [f'knowledge:{key}:{c["chunk_index"]}' for c in chunks]
        collection.upsert(ids=ids, documents=[c['text'] for c in chunks], embeddings=embeddings, metadatas=[{'source_key': key, 'fingerprint': fingerprint, 'kind': 'knowledge', 'filename': path.name, 'source': entry['title'], 'url': entry['url'], 'page': c['page'], 'chunk_index': c['chunk_index']} for c in chunks])
        stale = [id for id in existing['ids'] if id not in ids]
        if stale: collection.delete(ids=stale)
        print(f'Indexed {len(chunks)} chunks: {path.name}')

if __name__ == '__main__': ingest()
