from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid
from app.models.transporte import TipoTransporte, StatusTransporte


class TransporteBase(BaseModel):
    gaiola_id: uuid.UUID
    tipo: TipoTransporte
    motorista: Optional[str] = None
    veiculo: Optional[str] = None


class TransporteCreate(TransporteBase):
    pass


class TransporteUpdate(BaseModel):
    motorista: Optional[str] = None
    veiculo: Optional[str] = None
    data_chegada: Optional[datetime] = None
    status: Optional[StatusTransporte] = None


class TransporteResponse(TransporteBase):
    id: uuid.UUID
    data_saida: datetime
    data_chegada: Optional[datetime] = None
    status: StatusTransporte
    gaiola_codigo: Optional[str] = None

    model_config = {"from_attributes": True}
