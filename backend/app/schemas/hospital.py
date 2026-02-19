from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
import uuid


class HospitalBase(BaseModel):
    nome: str
    cnpj: Optional[str] = None
    endereco: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[EmailStr] = None
    ativo: bool = True


class HospitalCreate(HospitalBase):
    pass


class HospitalUpdate(BaseModel):
    nome: Optional[str] = None
    cnpj: Optional[str] = None
    endereco: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[EmailStr] = None
    ativo: Optional[bool] = None


class HospitalResponse(HospitalBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
