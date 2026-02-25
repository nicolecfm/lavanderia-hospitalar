from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import Usuario
from app.utils.security import decode_token

# auto_error=False so the token is optional – no 401 when the header is absent
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Usuario | None:
    if not token:
        return None
    payload = decode_token(token)
    if payload is None:
        return None
    email: str = payload.get("sub")
    if email is None:
        return None
    return db.query(Usuario).filter(Usuario.email == email, Usuario.ativo == True).first()  # noqa: E712


def get_current_active_user(current_user: Usuario | None = Depends(get_current_user)) -> Usuario | None:
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
