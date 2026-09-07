"""Projects and Lead Lists Management API routes."""

from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.database.models import Project, LeadList, LeadListMember, Lead


router = APIRouter(tags=["Projects & Lists"])


# --- Schemas ---

class ProjectCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    organization_id: Optional[int] = 1


class ProjectUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class LeadListCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    project_id: Optional[int] = None
    organization_id: Optional[int] = 1


class LeadListUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    project_id: Optional[int] = None


class AddLeadToListRequest(BaseModel):
    lead_id: Optional[int] = None
    lead_ids: Optional[List[int]] = None


# --- Project Endpoints ---

@router.get("/projects")
def list_projects(organization_id: Optional[int] = None):
    with get_db() as session:
        q = session.query(Project)
        if organization_id is not None:
            q = q.filter(Project.organization_id == organization_id)
        projects = q.order_by(Project.created_at.desc()).all()
        return [p.to_dict() for p in projects]


@router.post("/projects")
def create_project(req: ProjectCreateRequest):
    with get_db() as session:
        project = Project(
            name=req.name.strip(),
            description=req.description,
            organization_id=req.organization_id or 1,
            created_at=datetime.now(timezone.utc),
        )
        session.add(project)
        session.flush()
        return project.to_dict()


@router.get("/projects/{project_id}")
def get_project(project_id: int):
    with get_db() as session:
        project = session.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        data = project.to_dict()
        data["lists"] = [l.to_dict() for l in project.lead_lists] if project.lead_lists else []
        return data


@router.put("/projects/{project_id}")
def update_project(project_id: int, req: ProjectUpdateRequest):
    with get_db() as session:
        project = session.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        if req.name is not None:
            project.name = req.name.strip()
        if req.description is not None:
            project.description = req.description
        session.flush()
        return project.to_dict()


@router.delete("/projects/{project_id}")
def delete_project(project_id: int):
    with get_db() as session:
        project = session.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        session.delete(project)
        return {"status": "DELETED", "project_id": project_id}


@router.get("/projects/{project_id}/lists")
def get_project_lists(project_id: int):
    with get_db() as session:
        project = session.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return [l.to_dict() for l in project.lead_lists]


@router.post("/projects/{project_id}/lists")
def create_project_list(project_id: int, req: LeadListCreateRequest):
    with get_db() as session:
        project = session.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        lead_list = LeadList(
            name=req.name.strip(),
            description=req.description,
            project_id=project_id,
            organization_id=project.organization_id,
            created_at=datetime.now(timezone.utc),
        )
        session.add(lead_list)
        session.flush()
        return lead_list.to_dict()


# --- Lead List Endpoints ---

@router.get("/lists")
def list_lead_lists(project_id: Optional[int] = None, organization_id: Optional[int] = None):
    with get_db() as session:
        q = session.query(LeadList)
        if project_id is not None:
            q = q.filter(LeadList.project_id == project_id)
        if organization_id is not None:
            q = q.filter(LeadList.organization_id == organization_id)
        lists = q.order_by(LeadList.created_at.desc()).all()
        return [l.to_dict() for l in lists]


@router.post("/lists")
def create_lead_list(req: LeadListCreateRequest):
    with get_db() as session:
        lead_list = LeadList(
            name=req.name.strip(),
            description=req.description,
            project_id=req.project_id,
            organization_id=req.organization_id or 1,
            created_at=datetime.now(timezone.utc),
        )
        session.add(lead_list)
        session.flush()
        return lead_list.to_dict()


@router.get("/lists/{list_id}")
def get_lead_list(list_id: int):
    with get_db() as session:
        lead_list = session.query(LeadList).filter(LeadList.id == list_id).first()
        if not lead_list:
            raise HTTPException(status_code=404, detail="Lead list not found")
        data = lead_list.to_dict()
        data["member_count"] = len(lead_list.members) if lead_list.members else 0
        return data


@router.put("/lists/{list_id}")
def update_lead_list(list_id: int, req: LeadListUpdateRequest):
    with get_db() as session:
        lead_list = session.query(LeadList).filter(LeadList.id == list_id).first()
        if not lead_list:
            raise HTTPException(status_code=404, detail="Lead list not found")
        if req.name is not None:
            lead_list.name = req.name.strip()
        if req.description is not None:
            lead_list.description = req.description
        if req.project_id is not None:
            lead_list.project_id = req.project_id
        session.flush()
        return lead_list.to_dict()


@router.delete("/lists/{list_id}")
def delete_lead_list(list_id: int):
    with get_db() as session:
        lead_list = session.query(LeadList).filter(LeadList.id == list_id).first()
        if not lead_list:
            raise HTTPException(status_code=404, detail="Lead list not found")
        session.delete(lead_list)
        return {"status": "DELETED", "list_id": list_id}


@router.get("/lists/{list_id}/leads")
def get_leads_in_list(list_id: int):
    with get_db() as session:
        lead_list = session.query(LeadList).filter(LeadList.id == list_id).first()
        if not lead_list:
            raise HTTPException(status_code=404, detail="Lead list not found")
        members = session.query(LeadListMember).filter(LeadListMember.list_id == list_id).all()
        leads = [m.lead.to_dict() for m in members if m.lead]
        return {"list_id": list_id, "total": len(leads), "leads": leads}


@router.post("/lists/{list_id}/leads")
def add_leads_to_list(list_id: int, req: AddLeadToListRequest):
    with get_db() as session:
        lead_list = session.query(LeadList).filter(LeadList.id == list_id).first()
        if not lead_list:
            raise HTTPException(status_code=404, detail="Lead list not found")

        target_ids = []
        if req.lead_id is not None:
            target_ids.append(req.lead_id)
        if req.lead_ids:
            target_ids.extend(req.lead_ids)

        added = 0
        now = datetime.now(timezone.utc)
        for lid in set(target_ids):
            lead = session.query(Lead).filter(Lead.id == lid).first()
            if not lead:
                continue
            existing = (
                session.query(LeadListMember)
                .filter(LeadListMember.list_id == list_id, LeadListMember.lead_id == lid)
                .first()
            )
            if not existing:
                member = LeadListMember(
                    list_id=list_id,
                    lead_id=lid,
                    added_at=now,
                )
                session.add(member)
                added += 1

        session.flush()
        return {"status": "SUCCESS", "list_id": list_id, "added_count": added}


@router.delete("/lists/{list_id}/leads/{lead_id}")
def remove_lead_from_list(list_id: int, lead_id: int):
    with get_db() as session:
        member = (
            session.query(LeadListMember)
            .filter(LeadListMember.list_id == list_id, LeadListMember.lead_id == lead_id)
            .first()
        )
        if not member:
            raise HTTPException(status_code=404, detail="Lead not found in list")
        session.delete(member)
        return {"status": "REMOVED", "list_id": list_id, "lead_id": lead_id}
