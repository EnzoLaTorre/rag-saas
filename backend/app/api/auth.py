from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlmodel import Session, select

from ..core.deps import get_current_user
from ..core.security import create_access_token, hash_password, verify_password
from ..database import get_session
from ..models import Role, Tenant, User

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    tenant_name: str
    email: str
    full_name: str
    password: str


@router.post("/register")
def register(req: RegisterRequest, session: Session = Depends(get_session)):
    existing = session.exec(select(User).where(User.email == req.email)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email ya registrado",
        )

    tenant = Tenant(name=req.tenant_name)
    session.add(tenant)
    session.flush()  # para que tenant.id exista antes de usarlo

    user = User(
        tenant_id=tenant.id,
        email=req.email,
        hashed_password=hash_password(req.password),
        full_name=req.full_name,
        role=Role.admin,
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    return {
        "access_token": create_access_token(user.id, user.tenant_id),
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
        },
    }


@router.post("/login")
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    user = session.exec(select(User).where(User.email == form.username)).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
        )
    return {
        "access_token": create_access_token(user.id, user.tenant_id),
        "token_type": "bearer",
    }


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "tenant_id": user.tenant_id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
    }