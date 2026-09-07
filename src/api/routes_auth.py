"""Authentication and User Profile API routes."""

from __future__ import annotations
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Depends, status
from src.database.db import get_db
from src.database.models import User, Organization
from src.database.repository import OrganizationRepository, UserRepository, AuditLogRepository
from src.security.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    seed_default_data,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    email: str
    password: str


class SignupRequest(BaseModel):
    email: str
    password: str
    organization_name: Optional[str] = None
    role: Optional[str] = "admin"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict
    organization: dict


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest):
    email_clean = req.email.strip().lower()
    with get_db() as session:
        seed_default_data(session)

        user = UserRepository.get_by_email(session, email_clean)
        if not user or not verify_password(req.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated",
            )

        org = OrganizationRepository.get_by_id(session, user.organization_id)
        org_dict = org.to_dict() if org else {"id": user.organization_id, "name": "Default Organization"}
        user_dict = user.to_dict()

        token = create_access_token({
            "sub": str(user.id),
            "email": user.email,
            "org_id": user.organization_id,
            "role": user.role,
        })

        AuditLogRepository.create_log(
            session=session,
            action="user.login",
            resource_type="user",
            resource_id=str(user.id),
            organization_id=user.organization_id,
            user_id=user.id,
            details={"email": user.email},
        )

        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user=user_dict,
            organization=org_dict,
        )


@router.post("/signup", response_model=TokenResponse)
def signup(req: SignupRequest):
    email_clean = req.email.strip().lower()
    if len(req.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long",
        )

    with get_db() as session:
        existing = UserRepository.get_by_email(session, email_clean)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists",
            )

        org_name = req.organization_name.strip() if req.organization_name else f"{email_clean.split('@')[0]}'s Team"
        org = OrganizationRepository.create_organization(session, name=org_name)

        user = UserRepository.create_user(
            session=session,
            organization_id=org.id,
            email=email_clean,
            password=req.password,
            role=req.role if req.role in ["owner", "admin", "analyst", "viewer"] else "admin",
        )

        user_dict = user.to_dict()
        org_dict = org.to_dict()

        token = create_access_token({
            "sub": str(user.id),
            "email": user.email,
            "org_id": org.id,
            "role": user.role,
        })

        AuditLogRepository.create_log(
            session=session,
            action="user.signup",
            resource_type="user",
            resource_id=str(user.id),
            organization_id=org.id,
            user_id=user.id,
            details={"email": user.email, "org_name": org.name},
        )

        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user=user_dict,
            organization=org_dict,
        )


@router.get("/me")
def get_current_user_profile():
    with get_db() as session:
        org, user = seed_default_data(session)
        return {
            "user": user.to_dict(),
            "organization": org.to_dict(),
        }
