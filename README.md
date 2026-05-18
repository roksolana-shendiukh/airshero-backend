# ✈️ AirShero Backend

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![SQL Server](https://img.shields.io/badge/MS_SQL_Server-CC292B?style=for-the-badge&logo=microsoft-sql-server&logoColor=white)
![Firebase](https://img.shields.io/badge/Firebase-FFCA28?style=for-the-badge&logo=firebase&logoColor=black)
![Clean Architecture](https://img.shields.io/badge/Architecture-Clean-brightgreen.svg?style=for-the-badge)

---

## 📌 Overview

**AirShero** is a comprehensive backend REST API for an airline operations management system.

It provides a **robust, scalable, and secure foundation** for managing the full lifecycle of airline operations:

- Flight scheduling  
- Booking & payments  
- Passenger check-in  
- Crew assignment  
- Flight dispatch  

---

## 🏗️ Architecture

The project follows **Clean Architecture principles** to ensure:

- separation of concerns  
- high testability  
- maintainability  

### 🔹 Layers

**Controllers (`/controllers`)**
- Entry point for API  
- Handle HTTP requests  
- Validation via Pydantic  
- No business logic  

**Services (`/services`)**
- Core business logic  
- Pricing, seat rules, validation  

**Repositories (`/repositories`)**
- Data access layer  
- SQLAlchemy ORM  
- Isolated DB interaction  

---

## 💻 Tech Stack

### 🔧 Core
- Framework: FastAPI  
- Database: Microsoft SQL Server  

### 🗄️ Data Layer
- SQLAlchemy  
- Alembic  
- pyodbc  

### 🔐 Auth & Storage
- Firebase Admin SDK (JWT)  
- Firebase Storage  

### 📦 Other
- Pydantic  
- APScheduler  
- fpdf2  
- smtplib  

### 🌐 External APIs
- OpenWeatherMap API  
- Google Analytics Data API (GA4)  

---

## ✨ Key Features

### 🎫 Booking & Passenger Management

- **Transactional Booking**
  - Atomic operations  
  - 30-minute expiration  

- **Dynamic Baggage Pricing**
  - Based on distance, class, luggage size  

- **Interactive Seat Map**
  - Real-time availability  
  - Based on passenger attributes  

- **Automated Tickets**
  - PDF boarding passes  
  - Email delivery  

---

### 🛫 Flight Operations & Crew

- Flight scheduling automation  
- Crew assignment  
- Flight timeline tracking  

---

### 🛡️ Security & Data Integrity

- **RBAC (Role-Based Access Control)**
  - Sales Agent  
  - Check-in Agent  
  - Flight Operator  
  - Planning Manager  
  - Admin  

- **Database-level integrity**
  - Stored Procedures  
  - Triggers  
  - Scalar Functions  
  - Normalization to 4NF  

---

## 🚀 Getting Started

### 📋 Prerequisites

- Python 3.10+  
- Microsoft SQL Server  
- ODBC Driver 17  
- Firebase service account  

---

### ⚙️ Installation

#### 1. Clone repository
```bash
git clone https://github.com/yourusername/airshero-backend.git
cd airshero-backend
```

#### 2. Create virtual environment
```bash
python -m venv venv
```

```bash
source venv/bin/activate      # Linux / Mac
venv\Scripts\activate         # Windows
```

#### 3. Install dependencies
```bash
pip install -r requirements.txt
```

---

### 🔑 Environment Variables

```env
DATABASE_URL=mssql+pyodbc://user:password@server/database?driver=ODBC+Driver+17+for+SQL+Server

SMTP_EMAIL=your_email@gmail.com
SMTP_PASSWORD=your_app_password

WEATHER_API_KEY=your_openweathermap_api_key
```

---

### 🔥 Firebase Setup

Place `serviceAccountKey.json` in the project root.

---

### 🗄️ Database Migration

```bash
alembic upgrade head
```

---

### ▶️ Run Server

```bash
uvicorn main:app --reload
```

Swagger docs:  
http://localhost:8000/docs  

---

## 🗺️ System Diagrams

<details>
<summary><b>View Backend Component Diagram</b></summary>

<br>

![diagram](https://via.placeholder.com/800x400.png?text=Upload+Your+Diagram+Here)

</details>

---

## 📦 Project Purpose

Developed as the backend foundation for a full-scale Airline Operations Management System.
