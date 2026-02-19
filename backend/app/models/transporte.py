import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Enum as SAEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class TipoTransporte(str, enum.Enum):
    IDA = "ida"
    VOLTA = "volta"


class StatusTransporte(str, enum.Enum):
    EM_TRANSPORTE = "em_transporte"
    ENTREGUE = "entregue"


class Transporte(Base):
    __tablename__ = "transportes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    gaiola_id = Column(UUID(as_uuid=True), ForeignKey("gaiolas.id"), nullable=False)
    tipo = Column(SAEnum(TipoTransporte), nullable=False)
    motorista = Column(String(200), nullable=True)
    veiculo = Column(String(100), nullable=True)
    data_saida = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    data_chegada = Column(DateTime(timezone=True), nullable=True)
    status = Column(SAEnum(StatusTransporte), nullable=False, default=StatusTransporte.EM_TRANSPORTE)

    gaiola = relationship("Gaiola", back_populates="transportes")
