import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, Enum as SAEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class StatusGaiola(str, enum.Enum):
    CRIADA = "CRIADA"
    EM_TRANSPORTE_IDA = "EM_TRANSPORTE_IDA"
    RECEBIDA_LAVANDERIA = "RECEBIDA_LAVANDERIA"
    EM_SEPARACAO = "EM_SEPARACAO"
    EM_LAVAGEM = "EM_LAVAGEM"
    EM_SECAGEM = "EM_SECAGEM"
    EM_DOBRA = "EM_DOBRA"
    PRONTA_EXPEDICAO = "PRONTA_EXPEDICAO"
    EM_TRANSPORTE_VOLTA = "EM_TRANSPORTE_VOLTA"
    ENTREGUE = "ENTREGUE"


class Gaiola(Base):
    __tablename__ = "gaiolas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codigo = Column(String(100), unique=True, nullable=False, index=True)
    qr_code_url = Column(String(500), nullable=True)
    hospital_id = Column(UUID(as_uuid=True), ForeignKey("hospitais.id"), nullable=False)
    status = Column(SAEnum(StatusGaiola), nullable=False, default=StatusGaiola.CRIADA)
    data_criacao = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    observacoes = Column(Text, nullable=True)

    hospital = relationship("Hospital", back_populates="gaiolas")
    pesagens = relationship("Pesagem", back_populates="gaiola")
    transportes = relationship("Transporte", back_populates="gaiola")
    processos = relationship("Processo", back_populates="gaiola")
