from fastapi import FastAPI
from app.database import engine, Base
from sqlalchemy import text
from app.routes import admin, auth
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


@app.on_event("startup")
def startup():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("DB connect")
 
@app.get("/")
def read_root():
    return {"message": "Connected to SQL Server!"}

