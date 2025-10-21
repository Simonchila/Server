from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated
from sqlalchemy.orm import Session
from database import get_db
from utils.fare import compute_split
from models import Trip, Passenger
from schemas.trip_schema import TripCreate, TripOut
from utils.auth import get_current_user # authentication dependency

router = APIRouter(prefix="/trips", tags=["trips"])


# ------------------------- CREATE TRIP -------------------------
@router.post("/", response_model=TripOut)
def create_trip(
    trip: TripCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    db_trip = Trip(
        start=trip.start,
        destination=trip.destination,
        date=trip.date,
        total_cost=trip.total_cost,
        owner_id=current_user["id"]
    )
    db.add(db_trip)
    db.commit()
    db.refresh(db_trip)

    # Save passengers
    for p in trip.passengers:
        db_passenger = Passenger(
            name=p.name,
            surcharge=p.surcharge,
            share_amount=0.0,
            trip_id=db_trip.id
        )
        db.add(db_passenger)
    db.commit()

    # Compute final fare splits
    compute_split(db_trip)
    db.refresh(db_trip)

    return db_trip


# ------------------------- SPLIT -------------------------
@router.post("/{trip_id}/split")
def split_trip(trip_id: int, db: Session = Depends(get_db)):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    passengers = compute_split(trip)
    db.commit()

    return [{"name": p.name, "share_amount": p.share_amount} for p in passengers]


# ------------------------- GET ALL -------------------------
@router.get("/", response_model=list[TripOut])
def get_trips(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    return db.query(Trip).filter(Trip.owner_id == current_user["id"]).all()


# ------------------------- GET SINGLE -------------------------
@router.get("/{trip_id}", response_model=TripOut)
def get_trip(
    trip_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    trip = db.query(Trip).filter(
        Trip.id == trip_id,
        Trip.owner_id == current_user["id"]
    ).first()

    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    compute_split(trip)
    return trip

# ------------------------- SPLIT SUMMARY -------------------------
@router.get("/{trip_id}/split")
def get_split(
    trip_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    trip = db.query(Trip).filter(
        Trip.id == trip_id,
        Trip.owner_id == current_user["id"]
    ).first()

    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    split = compute_split(trip)
    return {
        "trip_id": trip.id,
        "passenger_breakdown": [
            {"name": p.name, "total": p.share_amount} for p in split
        ]
    }


# ------------------------- DELETE PASSENGER -------------------------
@router.delete("/{trip_id}/passengers/{passenger_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_passenger(
    trip_id: int,
    passenger_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    trip = db.query(Trip).filter(Trip.id == trip_id, Trip.owner_id == current_user['id']).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    passenger = db.query(Passenger).filter(
        Passenger.id == passenger_id, Passenger.trip_id == trip_id
    ).first()
    if not passenger:
        raise HTTPException(status_code=404, detail="Passenger not found")

    db.delete(passenger)
    db.commit()

    # --- Recompute fare split ---
    from utils.fare import compute_split
    compute_split(trip)
    db.commit()

    return {"message": "Passenger deleted and fares updated"}



# ------------------------- DELETE TRIP -------------------------
@router.delete("/{trip_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trip(
    trip_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    if trip.owner_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to delete this trip")

    # Delete passengers linked to trip first (due to FK constraint)
    db.query(Passenger).filter(Passenger.trip_id == trip_id).delete()

    try:
        db.delete(trip)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting trip: {e}")

    return
