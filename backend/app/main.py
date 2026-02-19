import logging
import os
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.config import settings
from app.database import get_db
from app.models.gaiola import Gaiola, StatusGaiola
from app.models.pesagem import Pesagem, TipoPesagem
from app.models.hospital import Hospital
from app.models.user import Usuario
from app.utils.dependencies import get_optional_user, require_web_user
from app.utils.security import verify_password, create_access_token, create_refresh_token
from app.routers import auth, hospitais, gaiolas, pesagens, transportes, processos, relatorios

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Sistema de gerenciamento de lavanderia hospitalar",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Determine base directory for static/template files
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_STATIC_DIR = os.path.join(_BASE_DIR, "frontend", "static")
_TEMPLATES_DIR = os.path.join(_BASE_DIR, "frontend", "templates")

if os.path.isdir(_STATIC_DIR):
    app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")
templates = Jinja2Templates(directory=_TEMPLATES_DIR)

# Register API routers
app.include_router(auth.router)
app.include_router(hospitais.router)
app.include_router(gaiolas.router)
app.include_router(pesagens.router)
app.include_router(transportes.router)
app.include_router(processos.router)
app.include_router(relatorios.router)


# ─── Notifications API ─────────────────────────────────────────────────────────

from fastapi import APIRouter as _APIRouter
from app.services import notificacao_service as _ns
from app.utils.dependencies import get_current_active_user as _get_user

_notif_router = _APIRouter(prefix="/api/v1/notificacoes", tags=["notificacoes"])


@_notif_router.get("/")
def get_notificacoes(limite: int = 50, current_user=Depends(_get_user)):
    """Retorna as últimas notificações de mudança de status."""
    return _ns.get_notificacoes_recentes(limite)


app.include_router(_notif_router)


# ─── Web Routes ────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    user = get_optional_user(request, next(get_db()))
    if user:
        return RedirectResponse(url="/dashboard")
    return RedirectResponse(url="/login")


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login", response_class=HTMLResponse)
async def login_submit(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    email = form.get("email", "")
    senha = form.get("senha", "")
    user = db.query(Usuario).filter(Usuario.email == email).first()
    if not user or not verify_password(senha, user.senha_hash) or not user.ativo:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Email ou senha incorretos"},
            status_code=401
        )
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie("access_token", access_token, httponly=True, samesite="lax")
    response.set_cookie("refresh_token", refresh_token, httponly=True, samesite="lax")
    return response


@app.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    user = _get_user_or_redirect(request, db)
    if isinstance(user, RedirectResponse):
        return user

    today = datetime.now(timezone.utc).date()
    total_peso_hoje = 0.0
    pesagens_hoje = db.query(Pesagem).filter(
        Pesagem.timestamp >= datetime(today.year, today.month, today.day, tzinfo=timezone.utc)
    ).all()
    for p in pesagens_hoje:
        total_peso_hoje += float(p.peso)

    stats = {
        "em_transito": db.query(Gaiola).filter(
            Gaiola.status.in_([StatusGaiola.EM_TRANSPORTE_IDA, StatusGaiola.EM_TRANSPORTE_VOLTA])
        ).count(),
        "em_processamento": db.query(Gaiola).filter(
            Gaiola.status.in_([StatusGaiola.EM_SEPARACAO, StatusGaiola.EM_LAVAGEM,
                                StatusGaiola.EM_SECAGEM, StatusGaiola.EM_DOBRA])
        ).count(),
        "prontas_expedicao": db.query(Gaiola).filter(
            Gaiola.status == StatusGaiola.PRONTA_EXPEDICAO
        ).count(),
        "peso_hoje": round(total_peso_hoje, 2),
    }

    gaiolas_recentes = db.query(Gaiola).order_by(Gaiola.data_criacao.desc()).limit(10).all()

    # Divergências > 5%
    alertas = []
    for g in db.query(Gaiola).all():
        peso_saida = None
        peso_exp = None
        for p in g.pesagens:
            if p.tipo_pesagem == TipoPesagem.SAIDA_HOSPITAL:
                peso_saida = float(p.peso)
            elif p.tipo_pesagem == TipoPesagem.EXPEDICAO:
                peso_exp = float(p.peso)
        if peso_saida and peso_exp:
            div = abs(peso_saida - peso_exp) / peso_saida * 100
            if div > 5:
                alertas.append({"gaiola": g.codigo, "divergencia": round(div, 2)})

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "stats": stats,
        "gaiolas_recentes": gaiolas_recentes,
        "alertas": alertas,
    })


@app.get("/gaiolas", response_class=HTMLResponse)
def gaiolas_page(request: Request, db: Session = Depends(get_db)):
    user = _get_user_or_redirect(request, db)
    if isinstance(user, RedirectResponse):
        return user
    all_gaiolas = db.query(Gaiola).order_by(Gaiola.data_criacao.desc()).all()
    hospitais = db.query(Hospital).filter(Hospital.ativo == True).all()  # noqa: E712
    return templates.TemplateResponse("gaiolas/list.html", {
        "request": request,
        "user": user,
        "gaiolas": all_gaiolas,
        "hospitais": hospitais,
        "status_list": [s.value for s in StatusGaiola],
    })


@app.get("/gaiolas/nova", response_class=HTMLResponse)
def gaiola_create_page(request: Request, db: Session = Depends(get_db)):
    user = _get_user_or_redirect(request, db)
    if isinstance(user, RedirectResponse):
        return user
    hospitais = db.query(Hospital).filter(Hospital.ativo == True).all()  # noqa: E712
    return templates.TemplateResponse("gaiolas/create.html", {
        "request": request,
        "user": user,
        "hospitais": hospitais,
    })


@app.get("/gaiolas/{gaiola_id}", response_class=HTMLResponse)
def gaiola_detail_page(request: Request, gaiola_id: str, db: Session = Depends(get_db)):
    user = _get_user_or_redirect(request, db)
    if isinstance(user, RedirectResponse):
        return user
    gaiola = db.query(Gaiola).filter(Gaiola.id == gaiola_id).first()
    if not gaiola:
        raise HTTPException(status_code=404, detail="Gaiola não encontrada")
    return templates.TemplateResponse("gaiolas/detail.html", {
        "request": request,
        "user": user,
        "gaiola": gaiola,
        "status_list": [s.value for s in StatusGaiola],
    })


@app.get("/hospitais", response_class=HTMLResponse)
def hospitais_page(request: Request, db: Session = Depends(get_db)):
    user = _get_user_or_redirect(request, db)
    if isinstance(user, RedirectResponse):
        return user
    all_hospitais = db.query(Hospital).order_by(Hospital.nome).all()
    return templates.TemplateResponse("hospitais/list.html", {
        "request": request,
        "user": user,
        "hospitais": all_hospitais,
    })


@app.get("/hospitais/novo", response_class=HTMLResponse)
def hospital_create_page(request: Request, db: Session = Depends(get_db)):
    user = _get_user_or_redirect(request, db)
    if isinstance(user, RedirectResponse):
        return user
    return templates.TemplateResponse("hospitais/form.html", {
        "request": request,
        "user": user,
        "hospital": None,
    })


@app.get("/hospitais/{hospital_id}", response_class=HTMLResponse)
def hospital_detail_page(request: Request, hospital_id: str, db: Session = Depends(get_db)):
    user = _get_user_or_redirect(request, db)
    if isinstance(user, RedirectResponse):
        return user
    hospital = db.query(Hospital).filter(Hospital.id == hospital_id).first()
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital não encontrado")
    return templates.TemplateResponse("hospitais/detail.html", {
        "request": request,
        "user": user,
        "hospital": hospital,
        "gaiolas": hospital.gaiolas,
    })


@app.get("/hospitais/{hospital_id}/editar", response_class=HTMLResponse)
def hospital_edit_page(request: Request, hospital_id: str, db: Session = Depends(get_db)):
    user = _get_user_or_redirect(request, db)
    if isinstance(user, RedirectResponse):
        return user
    hospital = db.query(Hospital).filter(Hospital.id == hospital_id).first()
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital não encontrado")
    return templates.TemplateResponse("hospitais/form.html", {
        "request": request,
        "user": user,
        "hospital": hospital,
    })


@app.get("/pesagens", response_class=HTMLResponse)
def pesagens_page(request: Request, db: Session = Depends(get_db)):
    user = _get_user_or_redirect(request, db)
    if isinstance(user, RedirectResponse):
        return user
    all_pesagens = db.query(Pesagem).order_by(Pesagem.timestamp.desc()).limit(100).all()
    return templates.TemplateResponse("pesagens/list.html", {
        "request": request,
        "user": user,
        "pesagens": all_pesagens,
    })


@app.get("/transportes", response_class=HTMLResponse)
def transportes_page(request: Request, db: Session = Depends(get_db)):
    from app.models.transporte import Transporte
    user = _get_user_or_redirect(request, db)
    if isinstance(user, RedirectResponse):
        return user
    all_transportes = db.query(Transporte).order_by(Transporte.data_saida.desc()).limit(100).all()
    return templates.TemplateResponse("transportes/list.html", {
        "request": request,
        "user": user,
        "transportes": all_transportes,
    })


@app.get("/relatorios", response_class=HTMLResponse)
def relatorios_page(request: Request, db: Session = Depends(get_db)):
    user = _get_user_or_redirect(request, db)
    if isinstance(user, RedirectResponse):
        return user
    hospitais = db.query(Hospital).filter(Hospital.ativo == True).all()  # noqa: E712
    return templates.TemplateResponse("relatorios/index.html", {
        "request": request,
        "user": user,
        "hospitais": hospitais,
    })


def _get_user_or_redirect(request: Request, db: Session):
    user = get_optional_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    return user
