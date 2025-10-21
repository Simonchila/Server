from pydantic import BaseModel, Field
from typing import List, Optional
from schemas.passenger_schema import PassengerOut 

class PassengerRequest(BaseModel):
    name: str
    surcharge: float = 0.0


class TripCreate(BaseModel):
    start: str
    destination: str
    date: str
    total_cost: float = Field(..., alias="totalCost")
    passengers: List[PassengerRequest]
    user_id: Optional[int] = None  # optional if you’ll pull from auth later

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class TripOut(BaseModel):
    id: int
    start: str
    destination: str
    date: str
    total_cost: float
    passengers: List[PassengerOut]

    class Config:
        orm_mode = True