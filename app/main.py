from fastapi import FastAPI
from app.database import engine, Base
from sqlalchemy import text
from app.routes import admin, auth, forall, booking
from fastapi.middleware.cors import CORSMiddleware


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
app.include_router(booking.router)

@app.on_event("startup")
def startup():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("DB connect")
 
@app.get("/")
def read_root():
    return {"message": "Connected to SQL Server!"}

from firebase_admin import auth as firebase_auth

# @app.get("/debug/user/{uid}")
# def debug_user(uid: str):
#     user = firebase_auth.get_user(uid)
#     return {"claims": user.custom_claims}