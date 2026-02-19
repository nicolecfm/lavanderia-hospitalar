"""
Serviço de integração com a balança.

Centraliza a lógica de:
- Registrar pesagens recebidas via API REST da balança
- Atualizar o status da gaiola de acordo com o tipo de pesagem
- Calcular e registrar divergências automáticas
"""
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.gaiola import Gaiola, StatusGaiola
from app.models.pesagem import Pesagem, TipoPesagem

# Mapeamento: tipo de pesagem → novo status da gaiola
PESAGEM_STATUS_MAP: dict[TipoPesagem, StatusGaiola] = {
    TipoPesagem.SAIDA_HOSPITAL: StatusGaiola.EM_TRANSPORTE_IDA,
    TipoPesagem.RECEBIMENTO_LAVANDERIA: StatusGaiola.RECEBIDA_LAVANDERIA,
    TipoPesagem.EXPEDICAO: StatusGaiola.PRONTA_EXPEDICAO,
}

# Limite padrão de divergência (%) para emitir alerta
LIMITE_DIVERGENCIA_PADRAO = 5.0


def registrar_pesagem(
    db: Session,
    gaiola: Gaiola,
    tipo_pesagem: TipoPesagem,
    peso: float,
    balanca_id: str | None = None,
    timestamp: datetime | None = None,
    usuario_id=None,
    observacoes: str | None = None,
) -> Pesagem:
    """Persiste uma nova pesagem e atualiza o status da gaiola."""
    ts = timestamp or datetime.now(timezone.utc)

    # Calcular divergência em relação à pesagem de saída do hospital
    divergencia: float | None = None
    alerta = False
    if tipo_pesagem != TipoPesagem.SAIDA_HOSPITAL:
        peso_saida = _get_peso_saida(gaiola)
        if peso_saida is not None and peso_saida > 0:
            divergencia = round(((float(peso) - peso_saida) / peso_saida) * 100, 2)
            alerta = abs(divergencia) > LIMITE_DIVERGENCIA_PADRAO

    pesagem = Pesagem(
        gaiola_id=gaiola.id,
        tipo_pesagem=tipo_pesagem,
        peso=peso,
        balanca_id=balanca_id,
        timestamp=ts,
        usuario_id=usuario_id,
        divergencia_percentual=divergencia,
        alerta_divergencia=alerta,
        observacoes=observacoes,
    )
    db.add(pesagem)

    novo_status = PESAGEM_STATUS_MAP.get(tipo_pesagem)
    if novo_status:
        gaiola.status = novo_status

    db.commit()
    db.refresh(pesagem)
    return pesagem


def _get_peso_saida(gaiola: Gaiola) -> float | None:
    """Retorna o peso de saída do hospital para a gaiola, se houver."""
    for p in gaiola.pesagens:
        if p.tipo_pesagem == TipoPesagem.SAIDA_HOSPITAL:
            return float(p.peso)
    return None


def calcular_divergencia(pesagens: list[Pesagem]) -> float | None:
    """Retorna a divergência percentual entre saída do hospital e expedição, ou None."""
    peso_saida = None
    peso_expedicao = None
    for p in pesagens:
        if p.tipo_pesagem == TipoPesagem.SAIDA_HOSPITAL:
            peso_saida = float(p.peso)
        elif p.tipo_pesagem == TipoPesagem.EXPEDICAO:
            peso_expedicao = float(p.peso)
    if peso_saida and peso_expedicao:
        return round(abs(peso_saida - peso_expedicao) / peso_saida * 100, 2)
    return None


def tem_divergencia_critica(
    pesagens: list[Pesagem],
    limite: float = LIMITE_DIVERGENCIA_PADRAO,
) -> bool:
    """Retorna True se a divergência de peso ultrapassar o limite configurado."""
    div = calcular_divergencia(pesagens)
    return div is not None and div > limite
