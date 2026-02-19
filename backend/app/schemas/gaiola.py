from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid
from app.models.gaiola import StatusGaiola


class GaiolaBase(BaseModel):
    codigo: str
    hospital_id: uuid.UUID
    observacoes: Optional[str] = None


class GaiolaCreate(GaiolaBase):
    pass


class GaiolaUpdate(BaseModel):
    codigo: Optional[str] = None
    hospital_id: Optional[uuid.UUID] = None
    status: Optional[StatusGaiola] = None
    observacoes: Optional[str] = None


class GaiolaResponse(GaiolaBase):
    id: uuid.UUID
    qr_code_url: Optional[str] = None
    status: StatusGaiola
    data_criacao: datetime
    hospital_nome: Optional[str] = None

    model_config = {"from_attributes": True}
