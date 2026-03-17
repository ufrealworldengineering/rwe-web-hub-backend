import uuid
from datetime import date
from enum import Enum as PyEnum
from typing import List, Optional

from sqlalchemy import Column, String, Boolean, ForeignKey, Date, Enum, JSON, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

# --- Enums ---
class UserRole(str, PyEnum):
    president = "president"
    treasurer = "treasurer"
    program_manager = "program_manager"
    member = "member"

class AppYear(str, PyEnum):
    first = "first"
    second = "second"
    third = "third"
    fourth = "fourth"
    other = "other"

class AppStatus(str, PyEnum):
    applied = "applied"
    accepted = "accepted"
    denied = "denied"
    in_review = "in_review"

# --- Tables ---

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)
    first_name: Mapped[Optional[str]] = mapped_column(String)
    last_name: Mapped[Optional[str]] = mapped_column(String)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    year: Mapped[Optional[AppYear]] = mapped_column(Enum(AppYear), nullable=True)

    managed_programs: Mapped[List["Program"]] = relationship("Program", back_populates="manager_rel")

class Program(Base):
    __tablename__ = "programs"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String)
    manager: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    manager_rel: Mapped["User"] = relationship("User", back_populates="managed_programs")
    teams: Mapped[List["Team"]] = relationship("Team", back_populates="program_rel")

class Team(Base):
    __tablename__ = "teams"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String)
    program: Mapped[uuid.UUID] = mapped_column(ForeignKey("programs.id", ondelete="CASCADE"))
    created_at: Mapped[date] = mapped_column(Date, default=date.today)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    application_template: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    program_rel: Mapped["Program"] = relationship("Program", back_populates="teams")
    members: Mapped[List["Member"]] = relationship("Member", back_populates="team_rel")
    applications: Mapped[List["Application"]] = relationship("Application", back_populates="team_rel")

class Member(Base):
    __tablename__ = "members"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"))
    first_name: Mapped[str] = mapped_column(String)
    last_name: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String)

    team_rel: Mapped["Team"] = relationship("Team", back_populates="members")

class Application(Base):
    __tablename__ = "applications"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"))
    first_name: Mapped[str] = mapped_column(String)
    last_name: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String)
    year: Mapped[AppYear] = mapped_column(Enum(AppYear))
    major: Mapped[str] = mapped_column(String)
    status: Mapped[AppStatus] = mapped_column(Enum(AppStatus), default=AppStatus.applied)
    notified: Mapped[bool] = mapped_column(Boolean, default=False)
    resume: Mapped[Optional[str]] = mapped_column(String) # URL to file storage
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB)
    #TODO: add date applied 
    team_rel: Mapped["Team"] = relationship("Team", back_populates="applications")

