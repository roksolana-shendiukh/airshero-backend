# AirShero – Backend

REST API for airline operations management system built with FastAPI.
Follows a layered architecture: Controllers -> Services -> Repositories -> ORM Models.

## Tech Stack

- **FastAPI** – REST API framework
- **SQLAlchemy** – ORM
- **Alembic** – database migrations
- **MS SQL Server** – database
- **Firebase Admin** – authentication
- **Pydantic** – data validation
- **Uvicorn** – ASGI server
- **APScheduler** – background tasks
- **SMTP** – email notifications

## Features

- Authentication via Firebase
- Passenger and document management
- Flight booking and payment processing
- Baggage management and pricing
- Flight operations and crew assignment
- Flight planning and scheduling
- Dynamic pricing management
- Admin analytics and audit logging
- Email notifications via SMTP
- Background snapshot scheduler

## Architecture

The project follows a layered architecture:

- **controllers/** – route handlers, request/response logic
- **services/** – business logic
- **repositories/** – database queries
- **models/** – ORM models
- **schemas/** – Pydantic schemas for validation
- **dependencies/** – dependency injection
- **middleware/** – CORS, authentication

![Component Diagram](https://github.com/user-attachments/assets/966a94d0-ea51-4387-9489-8019353c1758)


