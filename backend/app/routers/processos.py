from typing import List, Optional
import uuid as _uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.processo import Processo, EtapaProcesso
from app.models.gaiola import Gaiola, StatusGaiola
from app.schemas.processo import ProcessoCreate, ProcessoUpdate, ProcessoResponse
from app.utils.dependencies import get_current_active_user
from app.models.user import Usuario

router = APIRouter(prefix="/api/v1/processos", tags=["processos"])

ETAPA_STATUS_MAP = {
    EtapaProcesso.SEPARACAO: StatusGaiola.EM_SEPARACAO,
    EtapaProcesso.LAVAGEM: StatusGaiola.EM_LAVAGEM,
    EtapaProcesso.SECAGEM: StatusGaiola.EM_SECAGEM,
    EtapaProcesso.DOBRA: StatusGaiola.EM_DOBRA,
}


@router.get("/", response_model=List[ProcessoResponse])
def list_processos(
    skip: int = 0,
    limit: int = 100,
    gaiola_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    query = db.query(Processo)
    if gaiola_id:
        query = query.filter(Processo.gaiola_id == gaiola_id)
    return query.offset(skip).limit(limit).all()


@router.post("/", response_model=ProcessoResponse, status_code=201)
def create_processo(
    processo: ProcessoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    gaiola = db.query(Gaiola).filter(Gaiola.id == processo.gaiola_id).first()
    if not gaiola:
        raise HTTPException(status_code=404, detail="Gaiola não encontrada")
    db_processo = Processo(
        gaiola_id=processo.gaiola_id,
        etapa=processo.etapa,
        maquina_id=processo.maquina_id,
        observacoes=processo.observacoes,
        usuario_id=current_user.id,
    )
    db.add(db_processo)
    new_status = ETAPA_STATUS_MAP.get(processo.etapa)
    if new_status:
        gaiola.status = new_status
    db.commit()
    db.refresh(db_processo)
    return db_processo


@router.put("/{processo_id}", response_model=ProcessoResponse)
def update_processo(
    processo_id: str,
    update: ProcessoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    processo = db.query(Processo).filter(Processo.id == _uuid.UUID(processo_id)).first()
    if not processo:
        raise HTTPException(status_code=404, detail="Processo não encontrado")
    update_data = update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(processo, key, value)
    if "data_fim" not in update_data and not processo.data_fim:
        processo.data_fim = datetime.now(timezone.utc)
    db.commit()
    db.refresh(processo)
    return processo


@router.get("/{processo_id}", response_model=ProcessoResponse)
def get_processo(
    processo_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    p = db.query(Processo).filter(Processo.id == _uuid.UUID(processo_id)).first()
    if not p:
        raise HTTPException(status_code=404, detail="Processo não encontrado")
    return p
