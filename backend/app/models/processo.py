import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, Enum as SAEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class EtapaProcesso(str, enum.Enum):
    SEPARACAO = "separacao"
    LAVAGEM = "lavagem"
    SECAGEM = "secagem"
    DOBRA = "dobra"


class Processo(Base):
    __tablename__ = "processos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    gaiola_id = Column(UUID(as_uuid=True), ForeignKey("gaiolas.id"), nullable=False)
    etapa = Column(SAEnum(EtapaProcesso), nullable=False)
    data_inicio = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    data_fim = Column(DateTime(timezone=True), nullable=True)
    maquina_id = Column(String(100), nullable=True)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)
    observacoes = Column(Text, nullable=True)

    gaiola = relationship("Gaiola", back_populates="processos")
    usuario = relationship("Usuario", back_populates="processos")
