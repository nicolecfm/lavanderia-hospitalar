import io
import uuid as _uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.gaiola import Gaiola, StatusGaiola
from app.models.hospital import Hospital
from app.schemas.gaiola import GaiolaCreate, GaiolaUpdate, GaiolaResponse
from app.utils.dependencies import get_current_active_user
from app.models.user import Usuario
from app.services import notificacao_service, qrcode_service

router = APIRouter(prefix="/api/v1/gaiolas", tags=["gaiolas"])


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
    request: Request,
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
    db.add(db_gaiola)
    db.flush()
    base_url = str(request.base_url).rstrip("/")
    db_gaiola.qr_code_url = qrcode_service.salvar_qrcode(
        codigo=db_gaiola.codigo,
        gaiola_id=str(db_gaiola.id),
        base_url=base_url,
    )
    db.commit()
    db.refresh(db_gaiola)
    return _build_response(db_gaiola)


@router.get("/{gaiola_id}", response_model=GaiolaResponse)
def get_gaiola(
    gaiola_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    gaiola = db.query(Gaiola).filter(Gaiola.id == _uuid.UUID(gaiola_id)).first()
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
    gaiola = db.query(Gaiola).filter(Gaiola.id == _uuid.UUID(gaiola_id)).first()
    if not gaiola:
        raise HTTPException(status_code=404, detail="Gaiola não encontrada")
    status_anterior = gaiola.status.value
    update_data = gaiola_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(gaiola, key, value)
    db.commit()
    db.refresh(gaiola)
    if gaiola.status.value != status_anterior:
        notificacao_service.notificar_mudanca_status(
            gaiola_codigo=gaiola.codigo,
            status_anterior=status_anterior,
            status_novo=gaiola.status.value,
            usuario=current_user.email,
        )
    return _build_response(gaiola)


@router.get("/{gaiola_id}/qrcode")
def get_qrcode(
    gaiola_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    gaiola = db.query(Gaiola).filter(Gaiola.id == _uuid.UUID(gaiola_id)).first()
    if not gaiola:
        raise HTTPException(status_code=404, detail="Gaiola não encontrada")
    try:
        data = qrcode_service.gerar_qrcode_bytes(
            codigo=gaiola.codigo,
            gaiola_id=str(gaiola.id),
        )
        return StreamingResponse(io.BytesIO(data), media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar QR Code: {str(e)}")
