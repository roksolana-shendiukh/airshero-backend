from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from enum import Enum


class UserStatus(str, Enum):
    pendingActivation  = "pendingActivation"
    active             = "active"
    locked             = "locked"


class CreateUserRequest(BaseModel):
    email:       EmailStr
    firstName:   str
    lastName:    str
    airlineName: str
    roleId:      int
    agentId:     Optional[int] = None
    airlineId:   Optional[int] = None

    @field_validator("firstName", "lastName", "airlineName")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field cannot be empty")
        if len(v) > 50:
            raise ValueError("Field cannot exceed 50 characters")
        return v.strip()


class SetRoleRequest(BaseModel):
    roleId: int


class SetStatusRequest(BaseModel):
    status: UserStatus


class SetOperationRequest(BaseModel):
    operationId: Optional[int] = None