from fastapi import APIRouter, Depends,  HTTPException
from sqlalchemy.orm import Session
from database import get_db
from utils.fare import compute_split
from models import Trip, Passenger
from schemas.trip_schema import TripCreate, TripOut

router = APIRouter(prefix="/trips", tags=["trips"])

@router.post("/", response_model=TripOut)
def create_trip(trip: TripCreate, db: Session = Depends(get_db)):
    db_trip = Trip(
        start=trip.start,
        destination=trip.destination,
        date=trip.date,
        total_cost=trip.total_cost,
        user_id=trip.user_id or 1
    )
    db.add(db_trip)
    db.commit()
    db.refresh(db_trip)

    # Save passengers
    for p in trip.passengers:
        db_passenger = Passenger(
            name=p.name,
            share_amount=p.surcharge,
            trip_id=db_trip.id
        )
        db.add(db_passenger)
    db.commit()

    # Compute share_amounts
    compute_split(db_trip)
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

@router.get("/{trip_id}", response_model=TripOut)
def get_trip(trip_id: int, db: Session = Depends(get_db)):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    # Compute shares before returning
    compute_split(trip)
    return trip


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

@router.delete("/{trip_id}/passengers/{passenger_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_passenger(
    trip_id: int,
    passenger_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict, Depends(get_current_user)]
):
    """
    Deletes a specific passenger from a trip.
    
    Returns:
        HTTP 204 No Content on successful deletion.
    """
    
    # 1. Authorize User and Retrieve Trip
    # In a real app, you would check if current_user.id owns the trip_id
    trip = db.query(Trip).filter(Trip.id == trip_id).first()

    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )

    # Security check: Ensure the user owns the trip (essential)
    if trip.owner_id != current_user['id']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete passengers from this trip"
        )

    # 2. Find the Passenger
    # This assumes a 'passengers' relationship in your Trip model or a separate query
    passenger = db.query(Passenger).filter(
        Passenger.id == passenger_id,
        Passenger.trip_id == trip_id
    ).first()

    if not passenger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Passenger not found in this trip"
        )
        
    # 3. Perform Deletion
    try:
        db.delete(passenger)
        db.commit()
    except Exception as e:
        db.rollback()
        # Log the error for debugging
        print(f"Database error during passenger deletion: {e}") 
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not delete passenger due to a server error."
        )

    # 4. Return Success (No Content is standard for DELETE)
    return