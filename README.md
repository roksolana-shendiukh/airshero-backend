# AirShero – Backend

REST API for airline operations management system built with FastAPI.
Follows a layered architecture: Controllers → Services → Repositories → ORM Models.

## Tech Stack

- **FastAPI** – REST API framework
- **SQLAlchemy** – ORM
- **Alembic** – database migrations
- **MS SQL Server** – database
- **Firebase Admin** – authentication & storage
- **Pydantic** – data validation
- **Uvicorn** – ASGI server
- **APScheduler** – background tasks
- **OpenWeatherMap API** – weather data
- **SMTP** – email notifications

## Features

- Role-based access control (Sales Agent, Check-in Agent, Flight Operator, Planning Manager, Admin)
- Flight booking with 30-minute expiration and payment processing
- Dynamic baggage pricing based on flight class and luggage type
- Passenger check-in with interactive seat map
- Automated PDF boarding passes with email delivery
- Flight operations management and crew assignment
- Flight planning and dynamic pricing
- Admin analytics and audit logging

## Architecture

<details>
<summary>Deployment Diagram</summary>

![Deployment Diagram](https://github.com/user-attachments/assets/90ab48ee-408d-4896-b4ca-a7485d49106e)

</details>

<details>
<summary>Component Diagram</summary>

![Component Diagram](https://github.com/user-attachments/assets/b4bc5bca-dcd0-448f-8f48-5ddd2e96500d)

</details>


## Related Repositories

- [AirShero Frontend](https://github.com/roksolana-shendiukh/airshero-frontend)
- [AirShero Database](https://github.com/roksolana-shendiukh/airshero-db)
