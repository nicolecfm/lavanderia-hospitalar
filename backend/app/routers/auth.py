from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import Usuario
from app.schemas.user import LoginRequest, Token, UsuarioCreate, UsuarioResponse
from app.utils.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from app.utils.dependencies import get_current_active_user
from app.config import settings

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
templates = Jinja2Templates(directory="frontend/templates")


@router.post("/token", response_model=Token)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.email == login_data.email).first()
    if not user or not verify_password(login_data.senha, user.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
        )
    if not user.ativo:
        raise HTTPException(status_code=400, detail="Usuário inativo")
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.post("/usuarios", response_model=UsuarioResponse)
def create_usuario(
    usuario: UsuarioCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    if current_user.tipo_usuario.value != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores podem criar usuários")
    existing = db.query(Usuario).filter(Usuario.email == usuario.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    db_user = Usuario(
        nome=usuario.nome,
        email=usuario.email,
        senha_hash=get_password_hash(usuario.senha),
        tipo_usuario=usuario.tipo_usuario,
        ativo=usuario.ativo,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.get("/me", response_model=UsuarioResponse)
def get_me(current_user: Usuario = Depends(get_current_active_user)):
    return current_user
