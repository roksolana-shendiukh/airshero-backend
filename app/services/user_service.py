from firebase_admin import auth
from firebase_admin.exceptions import FirebaseError
from fastapi import HTTPException
from sqlalchemy.orm import Session
import re
import secrets
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from app.config import settings
from app.models.airline_model import Airline
from app.controllers.airline_controller import get_airline_logo_url
from app.database import SessionLocal


ID_TO_ROLE = {
    1: "salesAgent",
    2: "checkInAgent",
    3: "flightOperator",
    4: "planningManager",
    5: "systemAdmin",
}

ROLE_TO_ID = {v: k for k, v in ID_TO_ROLE.items()}

ROLE_DISPLAY = {
    "salesAgent": "Sales Agent",
    "checkInAgent": "Check-In Agent",
    "flightOperator": "Flight Operator",
    "planningManager": "Planning Manager",
    "systemAdmin": "System Admin",
}

def _generate_temp_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def _send_welcome_email(email: str, first_name: str, role: str, temp_password: str):
    smtp_email = settings.smtp_email
    smtp_password = settings.smtp_password

    if not smtp_email or not smtp_password:
        raise HTTPException(status_code=500, detail="SMTP not configured")

    role_display = ROLE_DISPLAY.get(role, role)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Welcome to AirShero — Your Account Details"
    msg["From"] = smtp_email
    msg["To"] = email

    body = f"""
Hello {first_name},

Your AirShero account has been created.

Role: {role_display}
Email: {email}
Temporary password: {temp_password}

Please log in and change your password within 40 minutes.
After that, this password will expire.

Login: {settings.frontend_url}/login

Best regards,
AirShero Team
    """.strip()

    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(smtp_email, smtp_password)
            server.sendmail(smtp_email, email, msg.as_string())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

def get_all_users():
    users = []
    page = auth.list_users()
    while page:
        for user in page.users:
            claims = user.custom_claims or {}
            role_str = claims.get("role")
            users.append({
                "uid": user.uid,
                "email": user.email,
                "firstName": claims.get("firstName", ""),
                "lastName": claims.get("lastName", ""),
                "airlineName": claims.get("airlineName", ""),
                "roleId": ROLE_TO_ID.get(role_str, 0),
                "status": claims.get("status", "pendingActivation"),
            })
        page = page.get_next_page()
    return users

def _validate_name(value: str, field: str) -> str:
    value = value.strip()
    if not re.match(r"^[A-Za-z'-]+$", value):
        raise HTTPException(status_code=422, detail=[{
            "loc": ["body", field],
            "msg": "Only Latin letters are allowed"
        }])
    if len(value) < 2:
        raise HTTPException(status_code=422, detail=[{
            "loc": ["body", field],
            "msg": "Must be at least 2 characters"
        }])
    if len(value) > 30:
        raise HTTPException(status_code=422, detail=[{
            "loc": ["body", field],
            "msg": "Must be at most 30 characters"
        }])
    return value

def create_user(
    email: str,
    first_name: str,
    last_name: str,
    airline_name: str,
    role_id: int,
    agent_id: int | None = None, 
    airline_id: int | None = None,
):
    role = ID_TO_ROLE.get(role_id)
    if not role or role == "systemAdmin":
        raise HTTPException(status_code=422, detail=[{
            "loc": ["body", "roleId"],
            "msg": "Invalid role"
        }])

    if role == "checkInAgent" and not agent_id:
        raise HTTPException(status_code=422, detail=[{
            "loc": ["body", "agentId"],
            "msg": "agentId is required for checkInAgent role"
        }])

    first_name = _validate_name(first_name, "firstName")
    last_name = _validate_name(last_name, "lastName")

    email = email.strip()
    if len(email) > 45:
        raise HTTPException(status_code=422, detail=[{
            "loc": ["body", "email"],
            "msg": "Email must be at most 45 characters"
        }])

    try:
        auth.get_user_by_email(email)
        raise HTTPException(status_code=422, detail=[{
            "loc": ["body", "email"],
            "msg": "User with this email already exists"
        }])
    except auth.UserNotFoundError:
        pass

    temp_password = _generate_temp_password()
    temp_password_created_at = datetime.now().isoformat()

    logo_url = None
    if airline_id:
        db = SessionLocal() 
        try:
            airline = db.query(Airline).filter(Airline.airline_id == airline_id).first()
            if airline:
                logo_url = get_airline_logo_url(airline.airline_url)
        finally:
            db.close()

    try:
        user = auth.create_user(
            email=email,
            password=temp_password,
            display_name=f"{first_name} {last_name}"
        )

        claims = {
            "firstName": first_name,
            "lastName": last_name,
            "airlineName": airline_name.strip(),
            "airlineLogoUrl": logo_url,
            "role": role,
            "status": "pendingPasswordChange",
            "tempPasswordCreatedAt": temp_password_created_at,
        }

        if role == "checkInAgent" and agent_id:
            claims["agentId"] = agent_id
        
        if airline_id:                         
            claims["airlineId"] = airline_id 

        auth.set_custom_user_claims(user.uid, claims)
        print(f"DEBUG: Created user with logo: {logo_url}")

        _send_welcome_email(email, first_name, role, temp_password)

        return {"uid": user.uid, "email": user.email}

    except auth.EmailAlreadyExistsError:
        raise HTTPException(status_code=422, detail=[{
            "loc": ["body", "email"],
            "msg": "User with this email already exists"
        }])
    except auth.InvalidArgumentError:
        raise HTTPException(status_code=422, detail=[{
            "loc": ["body", "email"],
            "msg": "Invalid email format"
        }])
    except FirebaseError as e:
        raise HTTPException(status_code=503, detail=f"Firebase service unavailable: {str(e)}")

def set_role(uid: str, role_id: int):
    role = ID_TO_ROLE.get(role_id)
    if not role:
        raise HTTPException(status_code=422, detail="Invalid role")
    user = auth.get_user(uid)
    claims = user.custom_claims or {}
    claims["role"] = role
    auth.set_custom_user_claims(uid, claims)

def set_status(uid: str, status: str):
    user = auth.get_user(uid)
    claims = user.custom_claims or {}
    claims["status"] = status
    if status == "locked":
        auth.update_user(uid, disabled=True)
    else:
        auth.update_user(uid, disabled=False)
    auth.set_custom_user_claims(uid, claims)

def check_temp_password_expired(uid: str):
    user = auth.get_user(uid)
    claims = user.custom_claims or {}
    if claims.get("status") != "pendingPasswordChange":
        return False
    created_at_str = claims.get("tempPasswordCreatedAt")
    if not created_at_str:
        return True
    created_at = datetime.fromisoformat(created_at_str)
    elapsed = (datetime.now() - created_at).total_seconds()
    if elapsed > 40 * 60:
        auth.update_user(uid, disabled=True)
        claims["status"] = "tempPasswordExpired"
        auth.set_custom_user_claims(uid, claims)
        return True
    return False

def _validate_password(password: str) -> str:
    if len(password) < 8:
        raise HTTPException(status_code=422, detail=[{
            "loc": ["body", "password"],
            "msg": "Password must be at least 8 characters"
        }])
    if len(password) > 64:
        raise HTTPException(status_code=422, detail=[{
            "loc": ["body", "password"],
            "msg": "Password must be at most 64 characters"
        }])
    if not re.search(r"[A-Z]", password):
        raise HTTPException(status_code=422, detail=[{
            "loc": ["body", "password"],
            "msg": "Password must contain at least one uppercase letter"
        }])
    if not re.search(r"[a-z]", password):
        raise HTTPException(status_code=422, detail=[{
            "loc": ["body", "password"],
            "msg": "Password must contain at least one lowercase letter"
        }])
    if not re.search(r"\d", password):
        raise HTTPException(status_code=422, detail=[{
            "loc": ["body", "password"],
            "msg": "Password must contain at least one digit"
        }])
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise HTTPException(status_code=422, detail=[{
            "loc": ["body", "password"],
            "msg": "Password must contain at least one special character"
        }])
    return password

def set_operation(uid: str, operation_id: int | None) -> None:
    user = auth.get_user(uid)
    claims = user.custom_claims or {}
    if operation_id is not None:
        claims["operationId"] = operation_id
    else:
        claims.pop("operationId", None)
    auth.set_custom_user_claims(uid, claims)

def update_user_claims_with_airline(uid: str, airline_id: int, db: Session):
    airline = db.query(Airline).filter(Airline.airline_id == airline_id).first()
    
    if not airline:
        return

    logo_url = get_airline_logo_url(airline.airline_url)
    
    user = auth.get_user(uid)
    current_claims = user.custom_claims or {}

    new_claims = {
        **current_claims,
        "airlineId": airline_id,
        "airlineName": airline.airline_name,
        "airlineLogoUrl": logo_url
    }

    auth.set_custom_user_claims(uid, new_claims)
