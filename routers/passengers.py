from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Passenger, Trip
from schemas.passenger_schema import PassengerCreate, PassengerOut

router = APIRouter(prefix="/passengers", tags=["passengers"])

@router.post("/", response_model=PassengerOut)
def create_passenger(passenger: PassengerCreate, db: Session = Depends(get_db)):
    db_passenger = Passenger(name=passenger.name, trip_id=passenger.trip_id)
    db.add(db_passenger)
    db.commit()
    db.refresh(db_passenger)
    return db_passenger

@router.get("/", response_model=list[PassengerOut])
def get_passengers(db: Session = Depends(get_db)):
    return db.query(Passenger).all()

@router.post("/compute_split", response_model=list[PassengerOut])
def compute_split(trip_id: int, db: Session = Depends(get_db)):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip or not trip.passengers:
        return []

    num_passengers = len(trip.passengers)
    base_share = trip.total_cost / num_passengers

    for p in trip.passengers:
        p.share_amount = base_share
        db.add(p)
    db.commit()
    return trip.passengers

