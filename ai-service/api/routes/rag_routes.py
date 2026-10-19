from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from rag.retriever import retrieve
from rag.generator import generate_answer
from llm.safety import guard_question
from llm.errors import provider_failure
from utils.validators import require_gateway, require_user
from utils.logger import logger
router = APIRouter(dependencies=[Depends(require_gateway)], tags=['questions'])
class Question(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    @field_validator('question')
    @classmethod
    def not_blank(cls, value):
        if not value.strip(): raise ValueError('Question cannot be blank')
        return value.strip()
@router.post('/ask')
def ask(question: Question, user_id: str = Depends(require_user)):
    guarded = guard_question(question.question)
    if guarded: return guarded
    try:
        return generate_answer(question.question, retrieve(question.question,user_id))
    except Exception as error:
        logger.error('ask_failed type=%s',type(error).__name__)
        failure = provider_failure(error)
        if failure:
            raise HTTPException(failure.status, failure.detail()) from error
        raise HTTPException(502,'Unable to produce a safe, evidence-backed answer. Check the AI configuration or try again.') from error
