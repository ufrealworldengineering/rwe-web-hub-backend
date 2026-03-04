from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List
from datetime import date
from uuid import UUID
from enum import Enum

# --- Enums  ---
class UserRole(str, Enum):
    president = "president"
    treasurer = "treasurer"
    program_manager = "program_manager"
    member = "member"

class AppYear(str, Enum):
    first = "first"
    second = "second"
    third = "third"
    fourth = "fourth"
    other = "other"

class AppStatus(str, Enum):
    applied = "applied"
    accepted = "accepted"
    denied = "denied"
    in_review = "in_review"

# --- User Schemas ---
class UserBase(BaseModel):
    email: EmailStr
    role: UserRole
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    year: Optional[AppYear] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    password: Optional[str] = None

class UserResponse(UserBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)

# --- Program Schemas ---
class ProgramBase(BaseModel):
    name: str
    manager: UUID
    active: bool = True

class ProgramCreate(ProgramBase):
    pass

class ProgramUpdate(BaseModel):
    name: Optional[str] = None
    manager: Optional[UUID] = None
    active: Optional[bool] = None

class ProgramResponse(ProgramBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)

class ProgramWithManager(ProgramResponse):
    manager_rel: Optional[UserResponse] = None
    model_config = ConfigDict(from_attributes=True)

# --- Team Schemas ---
class TeamBase(BaseModel):
    name: str
    program: UUID
    active: bool = True

class TeamCreate(TeamBase):
    pass

class TeamUpdate(BaseModel):
    name: Optional[str] = None
    program: Optional[UUID] = None
    active: Optional[bool] = None

class TeamResponse(TeamBase):
    id: UUID
    created_at: date
    model_config = ConfigDict(from_attributes=True)

class TeamWithProgram(TeamResponse):
    program_rel: Optional[ProgramResponse] = None
    model_config = ConfigDict(from_attributes=True)

# --- Member Schemas ---
class MemberBase(BaseModel):
    team: UUID
    first_name: str
    last_name: str
    email: EmailStr

class MemberCreate(MemberBase):
    pass

class MemberUpdate(BaseModel):
    team: Optional[UUID] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None

class MemberResponse(MemberBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)

class MemberWithTeam(MemberResponse):
    team_rel: Optional[TeamResponse] = None
    model_config = ConfigDict(from_attributes=True)

# --- Application Schemas ---
class ApplicationBase(BaseModel):
    team: UUID
    first_name: str
    last_name: str
    email: EmailStr
    year: AppYear
    major: str
    resume: Optional[str] = None
    metadata_json: Optional[dict] = None

class ApplicationCreate(ApplicationBase):
    pass

class ApplicationUpdate(BaseModel):
    team: Optional[UUID] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    year: Optional[AppYear] = None
    major: Optional[str] = None
    status: Optional[AppStatus] = None
    notified: Optional[bool] = None
    resume: Optional[str] = None
    metadata_json: Optional[dict] = None

class ApplicationResponse(ApplicationBase):
    id: UUID
    status: AppStatus
    notified: bool
    model_config = ConfigDict(from_attributes=True)

class ApplicationWithTeam(ApplicationResponse):
    team_rel: Optional[TeamResponse] = None
    model_config = ConfigDict(from_attributes=True)