from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.utils.dependencies import get_current_active_user
from app.models.user import Usuario
from app.services import relatorio_service

router = APIRouter(prefix="/api/v1/relatorios", tags=["relatorios"])


@router.get("/expedicao/excel")
def relatorio_expedicao_excel(
    data_inicio: Optional[date] = Query(None),
    data_fim: Optional[date] = Query(None),
    hospital_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    buf = relatorio_service.relatorio_expedicao_excel(db, hospital_id, data_inicio, data_fim)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=relatorio_expedicao.xlsx"}
    )


@router.get("/expedicao/csv")
def relatorio_expedicao_csv(
    data_inicio: Optional[date] = Query(None),
    data_fim: Optional[date] = Query(None),
    hospital_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    buf = relatorio_service.relatorio_expedicao_csv(db, hospital_id, data_inicio, data_fim)
    return StreamingResponse(
        buf,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=relatorio_expedicao.csv"}
    )


@router.get("/divergencias")
def relatorio_divergencias(
    limite_percentual: float = Query(5.0),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    return relatorio_service.relatorio_divergencias(db, limite_percentual)


@router.get("/produtividade")
def relatorio_produtividade(
    data_inicio: Optional[date] = Query(None),
    data_fim: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Relatório de produtividade por período.

    Retorna contagens de gaiolas por status, peso total expedido
    e tempo médio (em minutos) de cada etapa de processamento.
    """
    return relatorio_service.relatorio_produtividade(db, data_inicio, data_fim)

