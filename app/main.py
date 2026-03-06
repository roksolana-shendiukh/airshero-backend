from fastapi import FastAPI
from app.database import engine, Base
from sqlalchemy import text
from app.routes import admin, auth, forall, cities, flights, passengers, references, bookings, baggages
from fastapi.middleware.cors import CORSMiddleware
import app.models  

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(forall.router)
app.include_router(cities.router)
app.include_router(flights.router)
app.include_router(passengers.router)
app.include_router(references.router)
app.include_router(bookings.router)
app.include_router(baggages.router)

@app.on_event("startup")
def startup():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("DB connect")

@app.get("/")
def read_root():
    return {"message": "Connected to SQL Server!"}