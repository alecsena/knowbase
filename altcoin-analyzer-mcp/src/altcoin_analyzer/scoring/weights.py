from pydantic import BaseModel, Field, model_validator


class CategoryWeights(BaseModel):
    fundamentals: float = Field(default=0.25, ge=0, le=1)
    on_chain: float = Field(default=0.25, ge=0, le=1)
    market: float = Field(default=0.25, ge=0, le=1)
    risk: float = Field(default=0.25, ge=0, le=1)

    @model_validator(mode="after")
    def weights_sum_to_one(self) -> "CategoryWeights":
        total = self.fundamentals + self.on_chain + self.market + self.risk
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Category weights must sum to 1.0, got {total:.3f}")
        return self


DEFAULT_WEIGHTS = CategoryWeights()
