from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.transporte import Transporte, TipoTransporte, StatusTransporte
from app.models.gaiola import Gaiola, StatusGaiola
from app.schemas.transporte import TransporteCreate, TransporteUpdate, TransporteResponse
from app.utils.dependencies import get_current_active_user
from app.models.user import Usuario

router = APIRouter(prefix="/api/v1/transportes", tags=["transportes"])


def _build_response(t: Transporte) -> dict:
    return {
        "id": t.id,
        "gaiola_id": t.gaiola_id,
        "tipo": t.tipo,
        "motorista": t.motorista,
        "veiculo": t.veiculo,
        "data_saida": t.data_saida,
        "data_chegada": t.data_chegada,
        "status": t.status,
        "gaiola_codigo": t.gaiola.codigo if t.gaiola else None,
    }


@router.get("/", response_model=List[TransporteResponse])
def list_transportes(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    return [_build_response(t) for t in db.query(Transporte).offset(skip).limit(limit).all()]


@router.post("/", response_model=TransporteResponse, status_code=201)
def create_transporte(
    transporte: TransporteCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    gaiola = db.query(Gaiola).filter(Gaiola.id == transporte.gaiola_id).first()
    if not gaiola:
        raise HTTPException(status_code=404, detail="Gaiola não encontrada")
    db_transporte = Transporte(**transporte.model_dump())
    db.add(db_transporte)
    if transporte.tipo == TipoTransporte.IDA:
        gaiola.status = StatusGaiola.EM_TRANSPORTE_IDA
    elif transporte.tipo == TipoTransporte.VOLTA:
        gaiola.status = StatusGaiola.EM_TRANSPORTE_VOLTA
    db.commit()
    db.refresh(db_transporte)
    return _build_response(db_transporte)


@router.put("/{transporte_id}", response_model=TransporteResponse)
def update_transporte(
    transporte_id: str,
    update: TransporteUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    transporte = db.query(Transporte).filter(Transporte.id == transporte_id).first()
    if not transporte:
        raise HTTPException(status_code=404, detail="Transporte não encontrado")
    update_data = update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(transporte, key, value)
    if update.status == StatusTransporte.ENTREGUE and transporte.gaiola:
        if transporte.tipo == TipoTransporte.VOLTA:
            transporte.gaiola.status = StatusGaiola.ENTREGUE
        if not transporte.data_chegada:
            transporte.data_chegada = datetime.now(timezone.utc)
    db.commit()
    db.refresh(transporte)
    return _build_response(transporte)


@router.get("/{transporte_id}", response_model=TransporteResponse)
def get_transporte(
    transporte_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    t = db.query(Transporte).filter(Transporte.id == transporte_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Transporte não encontrado")
    return _build_response(t)
