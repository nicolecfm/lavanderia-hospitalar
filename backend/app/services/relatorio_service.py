"""
Serviço de relatórios.

Centraliza a lógica de:
- Montar linhas de dados para exportação (Excel / CSV)
- Calcular métricas de produtividade por período
- Relatório de divergências de peso
"""
import io
import csv
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.gaiola import Gaiola, StatusGaiola
from app.models.pesagem import TipoPesagem
from app.models.processo import Processo
from app.services.balanca_service import calcular_divergencia


def _get_peso(pesagens, tipo: TipoPesagem) -> Optional[float]:
    for p in pesagens:
        if p.tipo_pesagem == tipo:
            return float(p.peso)
    return None


def _query_gaiolas(
    db: Session,
    hospital_id: Optional[str] = None,
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
) -> list[Gaiola]:
    query = db.query(Gaiola)
    if hospital_id:
        query = query.filter(Gaiola.hospital_id == hospital_id)
    if data_inicio:
        query = query.filter(
            Gaiola.data_criacao >= datetime(data_inicio.year, data_inicio.month, data_inicio.day, tzinfo=timezone.utc)
        )
    if data_fim:
        query = query.filter(
            Gaiola.data_criacao <= datetime(data_fim.year, data_fim.month, data_fim.day, 23, 59, 59, tzinfo=timezone.utc)
        )
    return query.all()


def build_rows_expedicao(gaiolas: list[Gaiola]) -> list[dict]:
    """Monta linhas para o relatório de expedição."""
    rows = []
    for g in gaiolas:
        peso_saida = _get_peso(g.pesagens, TipoPesagem.SAIDA_HOSPITAL)
        peso_rec = _get_peso(g.pesagens, TipoPesagem.RECEBIMENTO_LAVANDERIA)
        peso_exp = _get_peso(g.pesagens, TipoPesagem.EXPEDICAO)
        divergencia = calcular_divergencia(g.pesagens)
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


def gerar_excel(rows: list[dict]) -> io.BytesIO:
    """Gera um arquivo Excel em memória a partir das linhas fornecidas."""
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Relatório Expedição"
    if rows:
        ws.append(list(rows[0].keys()))
        for row in rows:
            ws.append(list(row.values()))
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


def gerar_csv(rows: list[dict]) -> io.BytesIO:
    """Gera um arquivo CSV em memória a partir das linhas fornecidas."""
    buf = io.StringIO()
    if rows:
        writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    buf.seek(0)
    return io.BytesIO(buf.getvalue().encode("utf-8-sig"))


def relatorio_expedicao_excel(
    db: Session,
    hospital_id: Optional[str] = None,
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
) -> io.BytesIO:
    gaiolas = _query_gaiolas(db, hospital_id, data_inicio, data_fim)
    rows = build_rows_expedicao(gaiolas)
    return gerar_excel(rows)


def relatorio_expedicao_csv(
    db: Session,
    hospital_id: Optional[str] = None,
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
) -> io.BytesIO:
    gaiolas = _query_gaiolas(db, hospital_id, data_inicio, data_fim)
    rows = build_rows_expedicao(gaiolas)
    return gerar_csv(rows)


def relatorio_divergencias(
    db: Session,
    limite_percentual: float = 5.0,
) -> list[dict]:
    """Retorna gaiolas com divergência de peso acima do limite."""
    resultado = []
    for g in db.query(Gaiola).all():
        div = calcular_divergencia(g.pesagens)
        if div is not None and div >= limite_percentual:
            peso_saida = _get_peso(g.pesagens, TipoPesagem.SAIDA_HOSPITAL)
            peso_exp = _get_peso(g.pesagens, TipoPesagem.EXPEDICAO)
            resultado.append({
                "gaiola_codigo": g.codigo,
                "hospital": g.hospital.nome if g.hospital else "",
                "peso_saida": peso_saida,
                "peso_expedicao": peso_exp,
                "divergencia_percentual": div,
            })
    return resultado


def relatorio_produtividade(
    db: Session,
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
) -> dict:
    """
    Relatório de produtividade por período.

    Retorna:
    - total de gaiolas processadas (status ENTREGUE)
    - total de gaiolas em cada status
    - peso total expedido
    - número de processos concluídos por etapa
    - tempo médio de processamento por etapa (em minutos)
    """
    gaiola_query = db.query(Gaiola)
    processo_query = db.query(Processo)

    if data_inicio:
        dt_ini = datetime(data_inicio.year, data_inicio.month, data_inicio.day, tzinfo=timezone.utc)
        gaiola_query = gaiola_query.filter(Gaiola.data_criacao >= dt_ini)
        processo_query = processo_query.filter(Processo.data_inicio >= dt_ini)
    if data_fim:
        dt_fim = datetime(data_fim.year, data_fim.month, data_fim.day, 23, 59, 59, tzinfo=timezone.utc)
        gaiola_query = gaiola_query.filter(Gaiola.data_criacao <= dt_fim)
        processo_query = processo_query.filter(Processo.data_inicio <= dt_fim)

    gaiolas = gaiola_query.all()
    processos = processo_query.all()

    # Contagem por status
    por_status: dict[str, int] = {}
    peso_total_expedido = 0.0
    for g in gaiolas:
        s = g.status.value
        por_status[s] = por_status.get(s, 0) + 1
        peso_exp = _get_peso(g.pesagens, TipoPesagem.EXPEDICAO)
        if peso_exp:
            peso_total_expedido += peso_exp

    # Tempo médio por etapa (processos concluídos)
    etapa_tempos: dict[str, list[float]] = {}
    for p in processos:
        if p.data_inicio and p.data_fim:
            duracao = (p.data_fim - p.data_inicio).total_seconds() / 60.0
            etapa = p.etapa.value
            etapa_tempos.setdefault(etapa, []).append(duracao)

    tempo_medio_por_etapa = {
        etapa: round(sum(tempos) / len(tempos), 1)
        for etapa, tempos in etapa_tempos.items()
    }
    processos_por_etapa = {etapa: len(tempos) for etapa, tempos in etapa_tempos.items()}

    return {
        "total_gaiolas": len(gaiolas),
        "entregues": por_status.get("ENTREGUE", 0),
        "peso_total_expedido_kg": round(peso_total_expedido, 3),
        "por_status": por_status,
        "processos_concluidos_por_etapa": processos_por_etapa,
        "tempo_medio_min_por_etapa": tempo_medio_por_etapa,
    }
