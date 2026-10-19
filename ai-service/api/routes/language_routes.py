from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator
from llm.translator import translate_texts
from llm.errors import provider_failure
from utils.validators import require_gateway, require_user
from utils.logger import logger

router = APIRouter(prefix='/language', dependencies=[Depends(require_gateway)], tags=['language'])

class TranslationRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    texts: list[str] = Field(min_length=1, max_length=32)

    @field_validator('texts')
    @classmethod
    def bounded_texts(cls, texts):
        if any(not text.strip() or len(text) > 4000 for text in texts) or sum(len(text) for text in texts) > 32000:
            raise ValueError('Translation texts exceed the supported limits')
        return texts

@router.post('/translate')
def translate(request: TranslationRequest, user_id: str = Depends(require_user)):
    try:
        return {'translations': translate_texts(request.texts)}
    except Exception as error:
        logger.error('translation_failed type=%s', type(error).__name__)
        failure = provider_failure(error)
        if failure:
            raise HTTPException(failure.status, failure.detail()) from error
        raise HTTPException(502, 'Hindi translation could not be validated. Please try again.') from error
