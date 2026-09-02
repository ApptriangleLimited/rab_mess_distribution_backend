from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.member_serialize import member_public
from app.core.deps import get_db
from app.core.envelope import ok
from app.schemas.member import MemberEntryIn
from app.services.member_register import register_public_member

router = APIRouter(prefix="/api/v1/public", tags=["public"])


@router.post("/register")
def register_member(body: MemberEntryIn, db: Session = Depends(get_db)):
    member = register_public_member(db, body)
    return ok(member_public(member), status=201)
