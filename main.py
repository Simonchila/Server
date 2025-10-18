from fastapi import FastAPI
from routers import users, trips, passengers, auth
from database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="BusFare Splitter")

app.include_router(users.router)
app.include_router(trips.router)
app.include_router(passengers.router)
app.include_router(auth.router)

