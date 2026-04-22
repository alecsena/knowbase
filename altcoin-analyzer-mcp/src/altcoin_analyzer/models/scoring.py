from pydantic import BaseModel, Field


class CriterionScore(BaseModel):
    name: str
    score: float = Field(ge=0, le=10)
    weight: float = Field(ge=0, le=1)
    source: str
    note: str = ""


class CategoryScore(BaseModel):
    name: str
    score: float = Field(ge=0, le=10)
    weight: float = Field(ge=0, le=1)
    criteria: list[CriterionScore]


class ScoringResult(BaseModel):
    symbol: str
    fundamentals: CategoryScore
    on_chain: CategoryScore
    market: CategoryScore
    risk: CategoryScore
    overall: float = Field(ge=0, le=10)
    red_flags: list[str]
    green_flags: list[str]
