from datetime import date as Date
from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from ml.predict import analyze_labs
from utils.validators import require_gateway,require_user
router=APIRouter(prefix='/ml',tags=['trends'],dependencies=[Depends(require_gateway),Depends(require_user)])
class Observation(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
    test_name:str=Field(min_length=1,max_length=160)
    value:float
    unit:str|None=None
    date:Date|None=None
    reference_range:str|None=None
    reference_low:float|None=None
    reference_high:float|None=None
    low_inclusive:bool|None=True
    high_inclusive:bool|None=True
    filename:str
    report_id:str
    page:int=Field(ge=1)
class AnalysisRequest(BaseModel):
    observations:list[Observation]=Field(max_length=5000)
@router.post('/analyze')
def analyze(request:AnalysisRequest):
    return analyze_labs([entry.model_dump(mode='json') for entry in request.observations])
