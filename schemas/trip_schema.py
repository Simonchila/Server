from pydantic import BaseModel

class TripCreate(BaseModel):
    destination: str
    total_cost: float
    user_id: int

class TripOut(BaseModel):
    id: int
    destination: str
    total_cost: float
    user_id: int

    class Config:
        from_attributes = True

