import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, Enum as SAEnum, ForeignKey, Numeric, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class TipoPesagem(str, enum.Enum):
    SAIDA_HOSPITAL = "saida_hospital"
    RECEBIMENTO_LAVANDERIA = "recebimento_lavanderia"
    EXPEDICAO = "expedicao"


class Pesagem(Base):
    __tablename__ = "pesagens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    gaiola_id = Column(UUID(as_uuid=True), ForeignKey("gaiolas.id"), nullable=False)
    tipo_pesagem = Column(SAEnum(TipoPesagem), nullable=False)
    peso = Column(Numeric(10, 3), nullable=False)
    balanca_id = Column(String(100), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)
    divergencia_percentual = Column(Numeric(5, 2), nullable=True)
    alerta_divergencia = Column(Boolean, default=False, nullable=False)
    observacoes = Column(Text, nullable=True)

    gaiola = relationship("Gaiola", back_populates="pesagens")
    usuario = relationship("Usuario", back_populates="pesagens")
