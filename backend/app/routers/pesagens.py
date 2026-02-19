from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.pesagem import Pesagem, TipoPesagem
from app.models.gaiola import Gaiola, StatusGaiola
from app.schemas.pesagem import PesagemCreate, PesagemBalanca, PesagemResponse
from app.utils.dependencies import get_current_active_user
from app.models.user import Usuario

router = APIRouter(prefix="/api/v1/pesagens", tags=["pesagens"])

STATUS_MAP = {
    TipoPesagem.SAIDA_HOSPITAL: StatusGaiola.EM_TRANSPORTE_IDA,
    TipoPesagem.RECEBIMENTO_LAVANDERIA: StatusGaiola.RECEBIDA_LAVANDERIA,
    TipoPesagem.EXPEDICAO: StatusGaiola.PRONTA_EXPEDICAO,
}


def _build_response(p: Pesagem) -> dict:
    return {
        "id": p.id,
        "gaiola_id": p.gaiola_id,
        "tipo_pesagem": p.tipo_pesagem,
        "peso": float(p.peso),
        "balanca_id": p.balanca_id,
        "timestamp": p.timestamp,
        "usuario_id": p.usuario_id,
        "observacoes": p.observacoes,
        "gaiola_codigo": p.gaiola.codigo if p.gaiola else None,
    }


@router.get("/", response_model=List[PesagemResponse])
def list_pesagens(
    skip: int = 0,
    limit: int = 100,
    gaiola_id: Optional[str] = None,
    tipo: Optional[TipoPesagem] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    query = db.query(Pesagem)
    if gaiola_id:
        query = query.filter(Pesagem.gaiola_id == gaiola_id)
    if tipo:
        query = query.filter(Pesagem.tipo_pesagem == tipo)
    return [_build_response(p) for p in query.offset(skip).limit(limit).all()]


@router.post("/", response_model=PesagemResponse, status_code=201)
def create_pesagem(
    pesagem: PesagemCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    gaiola = db.query(Gaiola).filter(Gaiola.id == pesagem.gaiola_id).first()
    if not gaiola:
        raise HTTPException(status_code=404, detail="Gaiola não encontrada")
    db_pesagem = Pesagem(
        gaiola_id=pesagem.gaiola_id,
        tipo_pesagem=pesagem.tipo_pesagem,
        peso=pesagem.peso,
        balanca_id=pesagem.balanca_id,
        observacoes=pesagem.observacoes,
        usuario_id=current_user.id,
    )
    db.add(db_pesagem)
    new_status = STATUS_MAP.get(pesagem.tipo_pesagem)
    if new_status:
        gaiola.status = new_status
    db.commit()
    db.refresh(db_pesagem)
    return _build_response(db_pesagem)


@router.post("/balanca", response_model=PesagemResponse, status_code=201)
def pesagem_balanca(
    pesagem_data: PesagemBalanca,
    db: Session = Depends(get_db)
):
    """Endpoint para receber dados direto da balança."""
    gaiola = db.query(Gaiola).filter(Gaiola.codigo == pesagem_data.gaiola_codigo).first()
    if not gaiola:
        raise HTTPException(status_code=404, detail=f"Gaiola '{pesagem_data.gaiola_codigo}' não encontrada")
    ts = pesagem_data.timestamp or datetime.now(timezone.utc)
    db_pesagem = Pesagem(
        gaiola_id=gaiola.id,
        tipo_pesagem=pesagem_data.tipo_pesagem,
        peso=pesagem_data.peso,
        balanca_id=pesagem_data.balanca_id,
        timestamp=ts,
    )
    db.add(db_pesagem)
    new_status = STATUS_MAP.get(pesagem_data.tipo_pesagem)
    if new_status:
        gaiola.status = new_status
    db.commit()
    db.refresh(db_pesagem)
    return _build_response(db_pesagem)


@router.get("/{pesagem_id}", response_model=PesagemResponse)
def get_pesagem(
    pesagem_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    p = db.query(Pesagem).filter(Pesagem.id == pesagem_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Pesagem não encontrada")
    return _build_response(p)
