def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    """Split into fixed character windows; preserve the original overlap."""
    if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
        raise ValueError('Require chunk_size > 0 and 0 <= overlap < chunk_size')
    return [text[start:start + chunk_size].strip() for start in range(0, len(text), chunk_size - overlap) if text[start:start + chunk_size].strip()]

def chunk_pages(pages: list[dict]) -> list[dict]:
    chunks = []
    for page in pages:
        for text in chunk_text(page['text']):
            chunks.append({'text': text, 'page': page['page'], 'chunk_index': len(chunks), 'extraction_method': page.get('extraction_method', 'text')})
    return chunks
