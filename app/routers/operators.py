from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.operator import Operator
from app.schemas.operator import OperatorRead

router = APIRouter(prefix="/operators", tags=["operators"])


@router.get("", response_model=list[OperatorRead])
def list_operators(db: Session = Depends(get_db)) -> list[Operator]:
    return db.query(Operator).order_by(Operator.name.asc()).all()
