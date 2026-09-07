"""Organization and Team Management API routes."""

from __future__ import annotations
from typing import Optional, List
from pydantic import BaseModel, EmailStr
from fastapi import APIRouter, HTTPException, status
from src.database.db import get_db
from src.database.models import User, Organization
from src.database.repository import OrganizationRepository, UserRepository, AuditLogRepository
from src.security.auth import seed_default_data, hash_password

router = APIRouter(prefix="/organization", tags=["Organization"])


class InviteMemberRequest(BaseModel):
    email: str
    role: str = "analyst"  # owner, admin, analyst, viewer
    password: Optional[str] = None


class UpdateMemberRequest(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UpdateOrgRequest(BaseModel):
    name: Optional[str] = None


@router.get("")
def get_organization():
    with get_db() as session:
        org, _ = seed_default_data(session)
        return org.to_dict()


@router.patch("")
def update_organization(req: UpdateOrgRequest):
    with get_db() as session:
        org, _ = seed_default_data(session)
        if req.name:
            org.name = req.name.strip()
            session.flush()
        return org.to_dict()


@router.get("/members")
def list_organization_members():
    with get_db() as session:
        org, _ = seed_default_data(session)
        users = session.query(User).filter(User.organization_id == org.id).order_by(User.id).all()
        return [u.to_dict() for u in users]


@router.post("/members")
def invite_organization_member(req: InviteMemberRequest):
    email_clean = req.email.strip().lower()
    if req.role not in ["owner", "admin", "analyst", "viewer"]:
        raise HTTPException(status_code=400, detail="Invalid role specified")

    with get_db() as session:
        org, _ = seed_default_data(session)
        existing = UserRepository.get_by_email(session, email_clean)
        if existing:
            raise HTTPException(status_code=409, detail="User already exists with this email")

        pwd = req.password or "TempPass123!"
        user = UserRepository.create_user(
            session=session,
            organization_id=org.id,
            email=email_clean,
            password=pwd,
            role=req.role,
        )

        AuditLogRepository.create_log(
            session=session,
            action="member.invited",
            resource_type="user",
            resource_id=str(user.id),
            organization_id=org.id,
            details={"email": user.email, "role": user.role},
        )

        return user.to_dict()


@router.patch("/members/{user_id}")
def update_organization_member(user_id: int, req: UpdateMemberRequest):
    with get_db() as session:
        org, _ = seed_default_data(session)
        user = UserRepository.get_by_id(session, user_id, organization_id=org.id)
        if not user:
            raise HTTPException(status_code=404, detail="Member not found in organization")

        if req.role is not None:
            if req.role not in ["owner", "admin", "analyst", "viewer"]:
                raise HTTPException(status_code=400, detail="Invalid role specified")
            user.role = req.role

        if req.is_active is not None:
            user.is_active = req.is_active

        session.flush()

        AuditLogRepository.create_log(
            session=session,
            action="member.updated",
            resource_type="user",
            resource_id=str(user.id),
            organization_id=org.id,
            details={"role": user.role, "is_active": user.is_active},
        )

        return user.to_dict()


@router.delete("/members/{user_id}")
def remove_organization_member(user_id: int):
    with get_db() as session:
        org, admin = seed_default_data(session)
        user = UserRepository.get_by_id(session, user_id, organization_id=org.id)
        if not user:
            raise HTTPException(status_code=404, detail="Member not found")

        if user.id == admin.id:
            raise HTTPException(status_code=400, detail="Cannot delete primary organization administrator")

        session.delete(user)
        session.flush()

        AuditLogRepository.create_log(
            session=session,
            action="member.removed",
            resource_type="user",
            resource_id=str(user_id),
            organization_id=org.id,
        )

        return {"status": "SUCCESS", "deleted_user_id": user_id}
