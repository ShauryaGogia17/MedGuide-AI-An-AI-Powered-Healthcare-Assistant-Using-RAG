from pydantic import BaseModel, ConfigDict, Field
class Claim(BaseModel):
    model_config = ConfigDict(extra='forbid')
    text: str = Field(min_length=1, max_length=2000)
    source_ids: list[str] = Field(min_length=1)
class GroundedAnswer(BaseModel):
    model_config = ConfigDict(extra='forbid')
    from_report: list[Claim]
    general_information: list[Claim]
