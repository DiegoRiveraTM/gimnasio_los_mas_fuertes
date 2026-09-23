from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.core.limiter import limiter
from app.db.db import get_session
from app.schemas.membership import MembershipResponse
from app.services.membership import get_membership
from app.deps import get_current_user  # si ahí defines esta dependencia

router = APIRouter()


@router.get("/me", response_model=MembershipResponse)
@limiter.limit("30/minute")
def read_my_membership(
    request: Request,
    db: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    membership = get_membership(db, current_user.id)

    if membership is None:
        raise HTTPException(status_code=404, detail="Membership not found")

    return membership