from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from apscheduler.schedulers.background import BackgroundScheduler
from app.interfaces.api.v1.routes import admin_controller, airfleet_controller, airfleet_crud_controller, airline_controller, airport_controller, analytics_controller, auth_controller, baggage_controller, booking_controller, checkin_controller, city_controller, crew_controller, flight_controller, flight_crew_controller, flight_operation_controller, gate_controller, object_crud_controller, passenger_controller, planning_controller, reference_controller, reference_crud_controller, route_controller
from app.core.services.system_service import record_snapshot
from contextlib import asynccontextmanager



from app.database import engine
from app.interfaces.api.v1.routes import (
    user_controller
)

scheduler = BackgroundScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    record_snapshot()  
    scheduler.add_job(record_snapshot, 'interval', minutes=5)
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

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
app.include_router(flight_crew_controller.router)
app.include_router(planning_controller.router)
app.include_router(airline_controller.router)
app.include_router(analytics_controller.router)
app.include_router(user_controller.router)
app.include_router(crew_controller.router)
app.include_router(object_crud_controller.router)
app.include_router(reference_controller.router)
app.include_router(airfleet_crud_controller.router)


@app.on_event("startup")
def startup():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("DB connected")


@app.get("/")
def read_root():
    return {"message": "Connected to SQL Server!"}