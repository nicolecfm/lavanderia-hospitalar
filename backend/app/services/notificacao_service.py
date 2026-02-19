"""
Serviço de notificações.

Mantém um log em memória das mudanças de status das gaiolas.
Em produção, este serviço pode ser estendido para enviar e-mails,
webhooks ou mensagens via WebSocket.
"""
from datetime import datetime, timezone
from collections import deque
from threading import Lock
import logging

logger = logging.getLogger(__name__)

# Capacidade máxima do log em memória (evita crescimento ilimitado)
_MAX_NOTIFICACOES = 500
_notificacoes: deque[dict] = deque(maxlen=_MAX_NOTIFICACOES)
_lock = Lock()


def notificar_mudanca_status(
    gaiola_codigo: str,
    status_anterior: str,
    status_novo: str,
    usuario: str | None = None,
    observacoes: str | None = None,
) -> None:
    """
    Registra uma mudança de status de gaiola no log de notificações
    e emite um log de auditoria.
    """
    evento = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "gaiola_codigo": gaiola_codigo,
        "status_anterior": status_anterior,
        "status_novo": status_novo,
        "usuario": usuario,
        "observacoes": observacoes,
    }
    with _lock:
        _notificacoes.appendleft(evento)

    logger.info(
        "STATUS_CHANGE gaiola=%s %s → %s usuario=%s",
        gaiola_codigo,
        status_anterior,
        status_novo,
        usuario or "sistema",
    )


def get_notificacoes_recentes(limite: int = 50) -> list[dict]:
    """Retorna as notificações mais recentes (mais nova primeiro)."""
    with _lock:
        return list(_notificacoes)[:limite]


def limpar_notificacoes() -> None:
    """Limpa o log em memória (útil em testes)."""
    with _lock:
        _notificacoes.clear()
