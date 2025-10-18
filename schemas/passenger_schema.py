from pydantic import BaseModel

class PassengerCreate(BaseModel):
    name: str
    trip_id: int

class PassengerOut(BaseModel):
    id: int
    name: str
    share_amount: float
    trip_id: int

    class Config:
        from_attributes = True
