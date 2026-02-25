"""
Serviço de geração de QR codes.

Centraliza a lógica de geração de QR codes para gaiolas,
contendo código, ID e URL de acesso em formato JSON.
"""
import io
import json
import os
import logging

logger = logging.getLogger(__name__)

# Diretório base onde os QR codes são salvos
QR_DIR = os.path.join("frontend", "static", "img", "qrcodes")


def _qr_payload(codigo: str, gaiola_id: str, base_url: str = "http://localhost:8000") -> str:
    """Monta o payload JSON que será codificado no QR code."""
    return json.dumps({
        "codigo": codigo,
        "id": gaiola_id,
        "url": f"{base_url}/gaiolas/{gaiola_id}",
    })


def gerar_qrcode_bytes(codigo: str, gaiola_id: str, base_url: str = "http://localhost:8000") -> bytes:
    """Gera a imagem PNG do QR code e retorna como bytes."""
    import qrcode  # type: ignore

    payload = _qr_payload(codigo, gaiola_id, base_url)
    img = qrcode.make(payload)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def salvar_qrcode(codigo: str, gaiola_id: str, base_url: str = "http://localhost:8000") -> str | None:
    """
    Gera e salva o QR code em disco.

    Retorna o caminho público (URL relativa) do arquivo,
    ou None em caso de falha.
    """
    try:
        os.makedirs(QR_DIR, exist_ok=True)
        filename = f"{codigo.replace('/', '_')}.png"
        path = os.path.join(QR_DIR, filename)
        data = gerar_qrcode_bytes(codigo, gaiola_id, base_url)
        with open(path, "wb") as f:
            f.write(data)
        return f"/static/img/qrcodes/{filename}"
    except Exception as exc:
        logger.warning("Falha ao gerar QR code para %s: %s", codigo, exc)
        return None
