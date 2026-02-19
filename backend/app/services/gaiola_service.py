"""
Serviço de negócio para gaiolas.

Centraliza a lógica de:
- Geração automática de códigos sequenciais
- Criação de gaiolas com QR code
- Transições de status
"""
import logging
from sqlalchemy.orm import Session

from app.models.gaiola import Gaiola, StatusGaiola
from app.services import qrcode_service

logger = logging.getLogger(__name__)

_CODIGO_PREFIX = "GAIOL"


def _proximo_codigo(db: Session) -> str:
    """Gera o próximo código sequencial (ex.: GAIOL-001, GAIOL-002, ...)."""
    ultimo = (
        db.query(Gaiola)
        .filter(Gaiola.codigo.like(f"{_CODIGO_PREFIX}-%"))
        .order_by(Gaiola.codigo.desc())
        .first()
    )
    if ultimo:
        try:
            num = int(ultimo.codigo.split("-")[-1]) + 1
        except (ValueError, IndexError):
            num = 1
    else:
        num = 1
    return f"{_CODIGO_PREFIX}-{num:03d}"


def criar_gaiola(
    db: Session,
    hospital_id,
    codigo: str | None = None,
    observacoes: str | None = None,
    base_url: str = "http://localhost:8000",
) -> Gaiola:
    """
    Cria uma nova gaiola com código único e QR code.

    Se *codigo* não for fornecido, gera um automaticamente.
    Levanta ValueError se o código já existir.
    """
    if not codigo:
        codigo = _proximo_codigo(db)
    else:
        if db.query(Gaiola).filter(Gaiola.codigo == codigo).first():
            raise ValueError(f"Código '{codigo}' já cadastrado")

    gaiola = Gaiola(
        codigo=codigo,
        hospital_id=hospital_id,
        status=StatusGaiola.CRIADA,
        observacoes=observacoes,
    )
    db.add(gaiola)
    db.flush()  # obtém o UUID antes de gerar o QR code

    gaiola.qr_code_url = qrcode_service.salvar_qrcode(
        codigo=codigo,
        gaiola_id=str(gaiola.id),
        base_url=base_url,
    )
    db.commit()
    db.refresh(gaiola)
    logger.info("Gaiola criada: %s (id=%s)", codigo, gaiola.id)
    return gaiola


def atualizar_status(db: Session, gaiola: Gaiola, novo_status: StatusGaiola) -> Gaiola:
    """Atualiza o status de uma gaiola e persiste a mudança."""
    gaiola.status = novo_status
    db.commit()
    db.refresh(gaiola)
    logger.info("Status da gaiola %s atualizado para %s", gaiola.codigo, novo_status.value)
    return gaiola
