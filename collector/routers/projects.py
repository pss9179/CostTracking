from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from db import get_session
from models import Project, ProjectCreate, ProjectResponse
from clerk_auth import get_current_clerk_user
from models import User

router = APIRouter(
    prefix="/projects",
    tags=["projects"],
    responses={404: {"description": "Not found"}},
)

@router.post("", response_model=ProjectResponse)
def create_project(
    project: ProjectCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_clerk_user),
):
    """
    Create a new project for an organization.
    """
    # Verify user belongs to the organization (basic check for now, ideally check Clerk org permissions)
    # For MVP, we trust the frontend sends the correct org_id and user is part of it
    
    db_project = Project(
        name=project.name,
        organization_id=project.organization_id
    )
    session.add(db_project)
    session.commit()
    session.refresh(db_project)
    return db_project

@router.get("", response_model=List[ProjectResponse])
def list_projects(
    organization_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_clerk_user),
):
    """
    List all projects for a specific organization.
    """
    statement = select(Project).where(Project.organization_id == organization_id)
    projects = session.exec(statement).all()
    return projects
