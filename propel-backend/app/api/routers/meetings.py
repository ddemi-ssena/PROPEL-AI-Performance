from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_manager_or_admin
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.meeting import MeetingListItemResponse, TeamMeetingCreateRequest, TeamMeetingCreateResponse
from app.services.meeting_service import MeetingService

router = APIRouter()


@router.get("/", response_model=list[MeetingListItemResponse])
def list_meetings(
    team: Optional[str] = Query(None, description="Takıma göre filtrele"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_manager_or_admin),
):
    return MeetingService.list_meetings(db=db, team=team, limit=limit)


@router.post("/team-risk", response_model=TeamMeetingCreateResponse, status_code=status.HTTP_201_CREATED)
def create_team_risk_meeting(
    payload: TeamMeetingCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_manager_or_admin),
):
    return MeetingService.create_team_meeting(
        db=db,
        payload=payload,
        current_user=current_user,
    )
