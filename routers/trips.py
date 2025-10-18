from fastapi import APIRouter, Depends,  HTTPException
from sqlalchemy.orm import Session
from database import get_db
from utils.fare import compute_split
from models import Trip
from schemas.trip_schema import TripCreate, TripOut

router = APIRouter(prefix="/trips", tags=["trips"])

@router.post("/", response_model=TripOut)
def create_trip(trip: TripCreate, db: Session = Depends(get_db)):
    db_trip = Trip(destination=trip.destination, total_cost=trip.total_cost, user_id=trip.user_id)
    db.add(db_trip)
    db.commit()
    db.refresh(db_trip)
    return db_trip

@router.post("/trips/{trip_id}/split")
def split_trip(trip_id: int, db: Session = Depends(get_db)):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    passengers = compute_split(trip)

    # optionally persist share_amount to DB
    db.commit()

    return [{"name": p.name, "share_amount": p.share_amount} for p in passengers]

@router.get("/", response_model=list[TripOut])
def get_trips(db: Session = Depends(get_db)):
    return db.query(Trip).all()

@router.get("/{trip_id}/split")
def get_split(trip_id: int, db: Session = Depends(get_db)):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    split = compute_split(trip)
    return {
        "trip_id": trip.id,
        "passenger_breakdown": [
            {"name": p.name, "total": p.share_amount} for p in split
        ]
    }
