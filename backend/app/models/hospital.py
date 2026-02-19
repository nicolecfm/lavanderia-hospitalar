import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Hospital(Base):
    __tablename__ = "hospitais"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = Column(String(300), nullable=False)
    cnpj = Column(String(20), unique=True, nullable=True)
    endereco = Column(String(500), nullable=True)
    telefone = Column(String(20), nullable=True)
    email = Column(String(200), nullable=True)
    ativo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    gaiolas = relationship("Gaiola", back_populates="hospital")
