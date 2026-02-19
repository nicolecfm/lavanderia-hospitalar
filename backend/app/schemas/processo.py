from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid
from app.models.processo import EtapaProcesso


class ProcessoBase(BaseModel):
    gaiola_id: uuid.UUID
    etapa: EtapaProcesso
    maquina_id: Optional[str] = None
    observacoes: Optional[str] = None


class ProcessoCreate(ProcessoBase):
    pass


class ProcessoUpdate(BaseModel):
    data_fim: Optional[datetime] = None
    maquina_id: Optional[str] = None
    observacoes: Optional[str] = None


class ProcessoResponse(ProcessoBase):
    id: uuid.UUID
    data_inicio: datetime
    data_fim: Optional[datetime] = None
    usuario_id: Optional[uuid.UUID] = None

    model_config = {"from_attributes": True}
