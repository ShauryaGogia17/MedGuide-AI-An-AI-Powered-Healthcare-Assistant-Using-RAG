"""Authenticated, bounded microscope-image segmentation gateway."""
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from starlette.concurrency import run_in_threadpool

from services.blood_service import (
    MAX_BLOOD_UPLOAD_BYTES, BloodImageError, BloodModelUnavailable, analyze_image, model_status,
)
from utils.validators import require_gateway, require_user

router = APIRouter(prefix='/blood', tags=['blood'], dependencies=[Depends(require_gateway), Depends(require_user)])


@router.get('/status')
async def blood_status():
    return await run_in_threadpool(model_status)


@router.post('/analyze')
async def analyze_blood(file: UploadFile = File(...)):
    try:
        if file.content_type not in {'image/png', 'image/jpeg'}:
            raise HTTPException(415, 'Only PNG and JPEG blood-smear images are supported.')
        payload = bytearray()
        while block := await file.read(64 * 1024):
            payload.extend(block)
            if len(payload) > MAX_BLOOD_UPLOAD_BYTES:
                raise HTTPException(413, 'Blood-smear images must be 5 MB or smaller.')
        return await run_in_threadpool(analyze_image, bytes(payload))
    except BloodImageError as error:
        raise HTTPException(error.status, str(error)) from error
    except BloodModelUnavailable as error:
        raise HTTPException(error.status, {'code': error.code, 'message': error.message}) from error
    finally:
        await file.close()
