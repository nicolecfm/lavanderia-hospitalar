from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid
from app.models.pesagem import TipoPesagem


class PesagemBase(BaseModel):
    gaiola_id: uuid.UUID
    tipo_pesagem: TipoPesagem
    peso: float
    balanca_id: Optional[str] = None
    observacoes: Optional[str] = None


class PesagemCreate(PesagemBase):
    pass


class PesagemBalanca(BaseModel):
    """Schema para receber dados direto da balança via API"""
    gaiola_codigo: str
    peso: float
    tipo_pesagem: TipoPesagem
    balanca_id: str
    timestamp: Optional[datetime] = None


class PesagemResponse(PesagemBase):
    id: uuid.UUID
    timestamp: datetime
    usuario_id: Optional[uuid.UUID] = None
    divergencia_percentual: Optional[float] = None
    alerta_divergencia: bool = False
    gaiola_codigo: Optional[str] = None

    model_config = {"from_attributes": True}
