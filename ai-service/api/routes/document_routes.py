"""Bounded PDF ingestion; temporary files are always removed."""
import tempfile
from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, Depends
from starlette.concurrency import run_in_threadpool
from config import MAX_UPLOAD_BYTES
from extraction.pdf_extractor import extract_pages
from rag.chunker import chunk_pages
from utils.validators import require_gateway, require_user
from datetime import date
from uuid import UUID
from rag.embeddings import store_chunks
from rag.vector_store import get_collections
from extraction.lab_parser import extract_labs
from llm.errors import provider_failure

router = APIRouter(prefix='/documents', tags=['documents'], dependencies=[Depends(require_gateway)])

def index_pdf(path, source, user_id, report_id, report_date):
    pages = extract_pages(str(path))
    chunks = chunk_pages(pages)
    lab_data = extract_labs(pages, report_date)
    count = store_chunks(chunks, source, user_id, report_id, lab_data['report_date'] or '')
    return {'chunks': count, **lab_data}

@router.post('/upload', status_code=201)
async def upload_document(file: UploadFile = File(...), report_id: str = Form(''), report_date: str = Form(''), user_id: str = Depends(require_user)):
    path = None
    try:
        if file.content_type not in {'application/pdf', 'application/x-pdf'}:
            raise HTTPException(415, 'Only PDF files are supported')
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as destination:
            path = Path(destination.name)
            size = 0
            while block := await file.read(64 * 1024):
                size += len(block)
                if size > MAX_UPLOAD_BYTES:
                    raise HTTPException(413, 'PDF exceeds the upload size limit')
                if size == len(block) and not block.startswith(b'%PDF-'):
                    raise HTTPException(415, 'The uploaded file is not a valid PDF')
                destination.write(block)
        if not size:
            raise HTTPException(400, 'The PDF is empty')
        report_id = report_id or str(uuid4())
        try:
            UUID(report_id)
            if report_date: date.fromisoformat(report_date)
        except ValueError:
            raise HTTPException(422, 'Invalid report ID or date; use YYYY-MM-DD')
        source = Path((file.filename or 'report.pdf').replace('\\', '/')).name
        result = await run_in_threadpool(index_pdf, path, source, user_id, report_id, report_date)
        return {'message': 'Report indexed', 'report_id': report_id, 'source': source, 'chunks': result['chunks'], 'labs': result.get('labs', []), 'report_date': result.get('report_date'), 'date_source': result.get('date_source', 'unknown'), 'warnings': result.get('warnings', [])}
    except HTTPException:
        raise
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    except Exception as error:
        from utils.logger import logger
        logger.error('document_ingestion_failed type=%s', type(error).__name__)
        failure = provider_failure(error)
        if failure:
            raise HTTPException(failure.status, failure.detail()) from error
        raise HTTPException(502, 'Unable to process report; check AI configuration') from error
    finally:
        if path: path.unlink(missing_ok=True)
        await file.close()

@router.delete('/{report_id}', status_code=204)
def delete_vectors(report_id: str, user_id: str = Depends(require_user)):
    personal, _ = get_collections()
    personal.delete(where={'$and': [{'user_id': user_id}, {'report_id': report_id}]})
