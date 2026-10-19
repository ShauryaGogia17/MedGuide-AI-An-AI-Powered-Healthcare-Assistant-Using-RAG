"""Structured extraction with page/evidence validation; never impute a value."""
import json
import re
from datetime import date
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from dateutil.parser import parse as parse_date
from llm.openai_client import get_client, get_model
from llm.errors import provider_failure
from llm.prompts import LAB_EXTRACTION_PROMPT
from utils.logger import logger

class LabResult(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    test_name: str = Field(min_length=1,max_length=160)
    value: float
    unit: str | None
    reference_range: str | None
    reference_low: float | None
    reference_high: float | None
    low_inclusive: bool | None
    high_inclusive: bool | None
    page: int = Field(ge=1)
    evidence: str = Field(min_length=1,max_length=1500)
    @model_validator(mode='after')
    def valid_range(self):
        if self.reference_low is not None and self.reference_high is not None and self.reference_low > self.reference_high:
            raise ValueError('Reference range is reversed')
        return self

class PageLabs(BaseModel):
    model_config=ConfigDict(extra='forbid')
    report_date: date | None
    date_evidence: str | None
    labs: list[LabResult]

def normalized(text):
    return ' '.join(text.split()).casefold()

def numeric_tokens(text):
    return [Decimal(token.replace(',','')) for token in re.findall(r'(?<![\w.])[-+]?\d+(?:,\d{3})*(?:\.\d+)?(?:[eE][-+]?\d+)?',text)]

def validate_evidence(lab, page):
    content=normalized(page['text']); evidence=normalized(lab.evidence)
    if lab.page!=page['page'] or evidence not in content:
        raise ValueError('Lab evidence was not found on its cited page')
    if normalized(lab.test_name) not in evidence or (lab.unit and normalized(lab.unit) not in evidence):
        raise ValueError('Test name or unit was not found in lab evidence')
    if Decimal(str(lab.value)) not in numeric_tokens(lab.evidence):
        raise ValueError('Lab value was not found in evidence')
    if lab.reference_range:
        if normalized(lab.reference_range) not in content: raise ValueError('Reference interval was not printed on this page')
        for bound in [lab.reference_low,lab.reference_high]:
            if bound is not None and Decimal(str(bound)) not in numeric_tokens(lab.reference_range): raise ValueError('Reference bound was invented')
    elif lab.reference_low is not None or lab.reference_high is not None:
        raise ValueError('Numeric reference bounds need a printed interval')

def extract_labs(pages: list[dict], supplied_date: str = '') -> dict:
    labs=[]; dates=set(); warnings=[]
    for page in pages:
        try:
            response=get_client().responses.parse(model=get_model(),instructions=LAB_EXTRACTION_PROMPT,input=json.dumps(page),text_format=PageLabs)
            if response.output_parsed is None: raise ValueError('No validated lab extraction returned')
            parsed=PageLabs.model_validate(response.output_parsed)
            for lab in parsed.labs: validate_evidence(lab,page)
            if parsed.report_date:
                if not parsed.date_evidence or re.search(r'\b(dob|birth|print|printed|appointment)\b',parsed.date_evidence,re.I) or normalized(parsed.date_evidence) not in normalized(page['text']) or parse_date(parsed.date_evidence,fuzzy=True).date()!=parsed.report_date:
                    raise ValueError('Report date evidence is invalid')
                dates.add(parsed.report_date.isoformat())
            labs.extend(lab.model_dump() for lab in parsed.labs)
        except Exception as error:
            if provider_failure(error):
                raise
            logger.warning('lab_extraction_failed page=%s type=%s',page['page'],type(error).__name__)
            warnings.append(f'Lab extraction could not be validated on page {page["page"]}. Review the original report; no unverified values were saved for that page.')
    report_date=supplied_date or (next(iter(dates)) if len(dates)==1 else None)
    if len(dates)>1 and not supplied_date: warnings.append('Multiple report dates were found. Supply a report date to include this report in the timeline.')
    if not report_date: warnings.append('No unambiguous report date was found. Supply a date to include these values in the timeline.')
    # Collapse repeated printed copies of the same result, without combining tests across units.
    unique={}
    for lab in labs: unique[(normalized(lab['test_name']),lab['unit'],lab['value'],lab['reference_range'])]=lab
    return {'labs':list(unique.values()),'report_date':report_date,'date_source':'user' if supplied_date else 'report' if report_date else 'unknown','warnings':warnings}
