from models import Trip

def compute_split(trip: Trip):
    total_surcharge = sum(p.surcharge for p in trip.passengers)
    base = max(trip.total_cost - total_surcharge, 0)
    equal_share = base / max(len(trip.passengers), 1)

    for p in trip.passengers:
        p.share_amount = equal_share + p.surcharge  # dynamically add share_amount attribute

    return trip.passengers
