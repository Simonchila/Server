from pydantic import BaseModel
from typing import Optional

class PassengerCreate(BaseModel):
    name: str
    trip_id: int

class PassengerOut(BaseModel):
    id: int
    name: str
    # shareAmount: float = Field(..., alias="share_amount")
    shareAmount: Optional[float] = 0.0 
    trip_id: int

    class Config:
        orm_mode = True
        allow_population_by_field_name = True

