from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.database import engine
from app.controllers import (
    auth_controller,
    admin_controller,
    passenger_controller,
    booking_controller,
    baggage_controller,
    city_controller,
    flight_controller,
    reference_controller,
    checkin_controller,
    airport_controller,
    route_controller,
    flight_operation_controller,
    gate_controller,
    airfleet_controller
)
import app.models

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_controller.router)
app.include_router(admin_controller.router)
app.include_router(passenger_controller.router)
app.include_router(booking_controller.router)
app.include_router(baggage_controller.router)
app.include_router(city_controller.router)
app.include_router(flight_controller.router)
app.include_router(reference_controller.router)
app.include_router(checkin_controller.router)
app.include_router(airport_controller.router)
app.include_router(route_controller.router)
app.include_router(flight_operation_controller.router)
app.include_router(gate_controller.router)
app.include_router(airfleet_controller.router)


@app.on_event("startup")
def startup():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("DB connected")


@app.get("/")
def read_root():
    return {"message": "Connected to SQL Server!"}