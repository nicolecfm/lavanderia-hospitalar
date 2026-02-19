import io
import csv
from datetime import date, datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.gaiola import Gaiola
from app.models.pesagem import Pesagem, TipoPesagem
from app.utils.dependencies import get_current_active_user
from app.models.user import Usuario

router = APIRouter(prefix="/api/v1/relatorios", tags=["relatorios"])


def _get_peso(pesagens, tipo: TipoPesagem):
    for p in pesagens:
        if p.tipo_pesagem == tipo:
            return float(p.peso)
    return None


def _build_rows(gaiolas):
    rows = []
    for g in gaiolas:
        peso_saida = _get_peso(g.pesagens, TipoPesagem.SAIDA_HOSPITAL)
        peso_rec = _get_peso(g.pesagens, TipoPesagem.RECEBIMENTO_LAVANDERIA)
        peso_exp = _get_peso(g.pesagens, TipoPesagem.EXPEDICAO)
        divergencia = None
        if peso_saida and peso_exp:
            divergencia = round(abs(peso_saida - peso_exp) / peso_saida * 100, 2)
        rows.append({
            "ID Gaiola": str(g.id),
            "Código": g.codigo,
            "Hospital": g.hospital.nome if g.hospital else "",
            "Peso Saída (kg)": peso_saida or "",
            "Peso Recebimento (kg)": peso_rec or "",
            "Peso Expedição (kg)": peso_exp or "",
            "Divergência (%)": divergencia or "",
            "Status": g.status.value,
            "Data Criação": g.data_criacao.strftime("%d/%m/%Y %H:%M") if g.data_criacao else "",
        })
    return rows


@router.get("/expedicao/excel")
def relatorio_expedicao_excel(
    data_inicio: Optional[date] = Query(None),
    data_fim: Optional[date] = Query(None),
    hospital_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    try:
        import openpyxl
    except ImportError:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="openpyxl não instalado")

    query = db.query(Gaiola)
    if hospital_id:
        query = query.filter(Gaiola.hospital_id == hospital_id)
    if data_inicio:
        query = query.filter(Gaiola.data_criacao >= datetime(data_inicio.year, data_inicio.month, data_inicio.day, tzinfo=timezone.utc))
    if data_fim:
        query = query.filter(Gaiola.data_criacao <= datetime(data_fim.year, data_fim.month, data_fim.day, 23, 59, 59, tzinfo=timezone.utc))
    gaiolas = query.all()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Relatório Expedição"
    rows = _build_rows(gaiolas)
    if rows:
        ws.append(list(rows[0].keys()))
        for row in rows:
            ws.append(list(row.values()))
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
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
    query = db.query(Gaiola)
    if hospital_id:
        query = query.filter(Gaiola.hospital_id == hospital_id)
    if data_inicio:
        query = query.filter(Gaiola.data_criacao >= datetime(data_inicio.year, data_inicio.month, data_inicio.day, tzinfo=timezone.utc))
    if data_fim:
        query = query.filter(Gaiola.data_criacao <= datetime(data_fim.year, data_fim.month, data_fim.day, 23, 59, 59, tzinfo=timezone.utc))
    gaiolas = query.all()
    rows = _build_rows(gaiolas)

    buf = io.StringIO()
    if rows:
        writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    buf.seek(0)
    return StreamingResponse(
        io.BytesIO(buf.getvalue().encode("utf-8-sig")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=relatorio_expedicao.csv"}
    )


@router.get("/divergencias")
def relatorio_divergencias(
    limite_percentual: float = Query(5.0),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    gaiolas = db.query(Gaiola).all()
    resultado = []
    for g in gaiolas:
        peso_saida = _get_peso(g.pesagens, TipoPesagem.SAIDA_HOSPITAL)
        peso_exp = _get_peso(g.pesagens, TipoPesagem.EXPEDICAO)
        if peso_saida and peso_exp:
            div = abs(peso_saida - peso_exp) / peso_saida * 100
            if div >= limite_percentual:
                resultado.append({
                    "gaiola_codigo": g.codigo,
                    "hospital": g.hospital.nome if g.hospital else "",
                    "peso_saida": peso_saida,
                    "peso_expedicao": peso_exp,
                    "divergencia_percentual": round(div, 2),
                })
    return resultado
