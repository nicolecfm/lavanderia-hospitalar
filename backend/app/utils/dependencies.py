from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import Usuario
from app.utils.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Usuario:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception
    user = db.query(Usuario).filter(Usuario.email == email, Usuario.ativo == True).first()  # noqa: E712
    if user is None:
        raise credentials_exception
    return user


def get_current_active_user(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    if not current_user.ativo:
        raise HTTPException(status_code=400, detail="Usuário inativo")
    return current_user


def get_optional_user(request: Request, db: Session = Depends(get_db)) -> Usuario | None:
    """Get user from session cookie for web routes."""
    token = request.cookies.get("access_token")
    if not token:
        return None
    payload = decode_token(token)
    if payload is None:
        return None
    email: str = payload.get("sub")
    if email is None:
        return None
    return db.query(Usuario).filter(Usuario.email == email, Usuario.ativo == True).first()  # noqa: E712


def require_web_user(request: Request, db: Session = Depends(get_db)) -> Usuario:
    """Require authenticated user via cookie for web routes."""
    user = get_optional_user(request, db)
    if user is None:
        from fastapi.responses import RedirectResponse
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, detail="Não autenticado",
                            headers={"Location": "/login"})
    return user
