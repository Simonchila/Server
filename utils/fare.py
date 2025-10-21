from models import Trip

def compute_split(trip: Trip):
    total_surcharge = sum(p.share_amount for p in trip.passengers)

    base = max(trip.total_cost - total_surcharge, 0)
    equal_share = base / max(len(trip.passengers), 1)

    for p in trip.passengers:
        p.share_amount = equal_share + p.share_amount  # dynamically add share_amount attribute

    return trip.passengers
