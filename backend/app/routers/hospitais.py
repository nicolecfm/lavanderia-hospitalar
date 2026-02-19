from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.hospital import Hospital
from app.schemas.hospital import HospitalCreate, HospitalUpdate, HospitalResponse
from app.utils.dependencies import get_current_active_user
from app.models.user import Usuario

router = APIRouter(prefix="/api/v1/hospitais", tags=["hospitais"])


@router.get("/", response_model=List[HospitalResponse])
def list_hospitais(
    skip: int = 0,
    limit: int = 100,
    ativo: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    query = db.query(Hospital)
    if ativo is not None:
        query = query.filter(Hospital.ativo == ativo)
    return query.offset(skip).limit(limit).all()


@router.post("/", response_model=HospitalResponse, status_code=201)
def create_hospital(
    hospital: HospitalCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    if hospital.cnpj:
        existing = db.query(Hospital).filter(Hospital.cnpj == hospital.cnpj).first()
        if existing:
            raise HTTPException(status_code=400, detail="CNPJ já cadastrado")
    db_hospital = Hospital(**hospital.model_dump())
    db.add(db_hospital)
    db.commit()
    db.refresh(db_hospital)
    return db_hospital


@router.get("/{hospital_id}", response_model=HospitalResponse)
def get_hospital(
    hospital_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    hospital = db.query(Hospital).filter(Hospital.id == hospital_id).first()
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital não encontrado")
    return hospital


@router.put("/{hospital_id}", response_model=HospitalResponse)
def update_hospital(
    hospital_id: str,
    hospital_update: HospitalUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    hospital = db.query(Hospital).filter(Hospital.id == hospital_id).first()
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital não encontrado")
    update_data = hospital_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(hospital, key, value)
    db.commit()
    db.refresh(hospital)
    return hospital


@router.delete("/{hospital_id}")
def delete_hospital(
    hospital_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    hospital = db.query(Hospital).filter(Hospital.id == hospital_id).first()
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital não encontrado")
    hospital.ativo = False
    db.commit()
    return {"message": "Hospital desativado com sucesso"}
