import io
import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.gaiola import Gaiola, StatusGaiola
from app.models.hospital import Hospital
from app.schemas.gaiola import GaiolaCreate, GaiolaUpdate, GaiolaResponse
from app.utils.dependencies import get_current_active_user
from app.models.user import Usuario

router = APIRouter(prefix="/api/v1/gaiolas", tags=["gaiolas"])

QR_DIR = "frontend/static/img/qrcodes"


def _generate_qr_code(codigo: str) -> str:
    """Generate QR code image and return URL path."""
    try:
        import qrcode
        os.makedirs(QR_DIR, exist_ok=True)
        img = qrcode.make(codigo)
        filename = f"{codigo.replace('/', '_')}.png"
        path = os.path.join(QR_DIR, filename)
        img.save(path)
        return f"/static/img/qrcodes/{filename}"
    except Exception:
        return None


def _build_response(gaiola: Gaiola) -> dict:
    data = {
        "id": gaiola.id,
        "codigo": gaiola.codigo,
        "qr_code_url": gaiola.qr_code_url,
        "hospital_id": gaiola.hospital_id,
        "status": gaiola.status,
        "data_criacao": gaiola.data_criacao,
        "observacoes": gaiola.observacoes,
        "hospital_nome": gaiola.hospital.nome if gaiola.hospital else None,
    }
    return data


@router.get("/", response_model=List[GaiolaResponse])
def list_gaiolas(
    skip: int = 0,
    limit: int = 100,
    status: Optional[StatusGaiola] = None,
    hospital_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    query = db.query(Gaiola)
    if status:
        query = query.filter(Gaiola.status == status)
    if hospital_id:
        query = query.filter(Gaiola.hospital_id == hospital_id)
    gaiolas = query.offset(skip).limit(limit).all()
    return [_build_response(g) for g in gaiolas]


@router.post("/", response_model=GaiolaResponse, status_code=201)
def create_gaiola(
    gaiola: GaiolaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    existing = db.query(Gaiola).filter(Gaiola.codigo == gaiola.codigo).first()
    if existing:
        raise HTTPException(status_code=400, detail="Código de gaiola já existe")
    hospital = db.query(Hospital).filter(Hospital.id == gaiola.hospital_id).first()
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital não encontrado")
    db_gaiola = Gaiola(**gaiola.model_dump())
    db_gaiola.qr_code_url = _generate_qr_code(gaiola.codigo)
    db.add(db_gaiola)
    db.commit()
    db.refresh(db_gaiola)
    return _build_response(db_gaiola)


@router.get("/{gaiola_id}", response_model=GaiolaResponse)
def get_gaiola(
    gaiola_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    gaiola = db.query(Gaiola).filter(Gaiola.id == gaiola_id).first()
    if not gaiola:
        raise HTTPException(status_code=404, detail="Gaiola não encontrada")
    return _build_response(gaiola)


@router.put("/{gaiola_id}", response_model=GaiolaResponse)
def update_gaiola(
    gaiola_id: str,
    gaiola_update: GaiolaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    gaiola = db.query(Gaiola).filter(Gaiola.id == gaiola_id).first()
    if not gaiola:
        raise HTTPException(status_code=404, detail="Gaiola não encontrada")
    update_data = gaiola_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(gaiola, key, value)
    db.commit()
    db.refresh(gaiola)
    return _build_response(gaiola)


@router.get("/{gaiola_id}/qrcode")
def get_qrcode(
    gaiola_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    gaiola = db.query(Gaiola).filter(Gaiola.id == gaiola_id).first()
    if not gaiola:
        raise HTTPException(status_code=404, detail="Gaiola não encontrada")
    try:
        import qrcode
        img = qrcode.make(gaiola.codigo)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return StreamingResponse(buf, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar QR Code: {str(e)}")
