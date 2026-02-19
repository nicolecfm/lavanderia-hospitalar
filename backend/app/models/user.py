import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
from app.database import Base


class TipoUsuario(str, enum.Enum):
    ADMIN = "admin"
    OPERADOR_HOSPITAL = "operador_hospital"
    OPERADOR_LAVANDERIA = "operador_lavanderia"
    MOTORISTA = "motorista"


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = Column(String(200), nullable=False)
    email = Column(String(200), unique=True, nullable=False, index=True)
    senha_hash = Column(String(255), nullable=False)
    tipo_usuario = Column(SAEnum(TipoUsuario), nullable=False, default=TipoUsuario.OPERADOR_LAVANDERIA)
    ativo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    pesagens = relationship("Pesagem", back_populates="usuario")
    processos = relationship("Processo", back_populates="usuario")
