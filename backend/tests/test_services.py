"""Tests for processos, transportes, relatorios, and service layer."""
import uuid
import pytest
from datetime import datetime, timezone, timedelta

from app.models.user import Usuario, TipoUsuario
from app.models.hospital import Hospital
from app.models.gaiola import Gaiola, StatusGaiola
from app.models.pesagem import Pesagem, TipoPesagem
from app.models.processo import Processo, EtapaProcesso
from app.models.transporte import Transporte, TipoTransporte, StatusTransporte
from app.utils.security import get_password_hash, create_access_token
from app.services import balanca_service, notificacao_service, relatorio_service


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _admin(db):
    u = Usuario(
        id=uuid.uuid4(), nome="Admin", email=f"admin_{uuid.uuid4().hex[:6]}@test.com",
        senha_hash=get_password_hash("pw"), tipo_usuario=TipoUsuario.ADMIN, ativo=True,
    )
    db.add(u); db.commit(); db.refresh(u)
    return u


def _hospital(db, nome="H"):
    h = Hospital(id=uuid.uuid4(), nome=nome, ativo=True)
    db.add(h); db.commit(); db.refresh(h)
    return h


def _gaiola(db, hospital, codigo=None, status=StatusGaiola.CRIADA):
    g = Gaiola(
        id=uuid.uuid4(),
        codigo=codigo or f"G-{uuid.uuid4().hex[:6]}",
        hospital_id=hospital.id,
        status=status,
    )
    db.add(g); db.commit(); db.refresh(g)
    return g


def _tok(user):
    return create_access_token(data={"sub": user.email})


def _auth(user):
    return {"Authorization": f"Bearer {_tok(user)}"}


# ─── Processos ────────────────────────────────────────────────────────────────

def test_create_processo_sets_gaiola_status(client, db):
    user = _admin(db)
    h = _hospital(db)
    g = _gaiola(db, h)

    resp = client.post("/api/v1/processos/", json={
        "gaiola_id": str(g.id),
        "etapa": "lavagem",
    }, headers=_auth(user))
    assert resp.status_code == 201
    data = resp.json()
    assert data["etapa"] == "lavagem"

    db.refresh(g)
    assert g.status == StatusGaiola.EM_LAVAGEM


def test_update_processo_sets_data_fim(client, db):
    user = _admin(db)
    h = _hospital(db)
    g = _gaiola(db, h)

    create_resp = client.post("/api/v1/processos/", json={
        "gaiola_id": str(g.id),
        "etapa": "secagem",
    }, headers=_auth(user))
    processo_id = create_resp.json()["id"]

    update_resp = client.put(f"/api/v1/processos/{processo_id}", json={},
                             headers=_auth(user))
    assert update_resp.status_code == 200
    assert update_resp.json()["data_fim"] is not None


def test_list_processos(client, db):
    user = _admin(db)
    h = _hospital(db)
    g = _gaiola(db, h)

    p = Processo(
        id=uuid.uuid4(), gaiola_id=g.id, etapa=EtapaProcesso.DOBRA,
        data_inicio=datetime.now(timezone.utc),
    )
    db.add(p); db.commit()

    resp = client.get("/api/v1/processos/", headers=_auth(user))
    assert resp.status_code == 200
    assert any(x["etapa"] == "dobra" for x in resp.json())


# ─── Transportes ──────────────────────────────────────────────────────────────

def test_create_transporte_ida_sets_status(client, db):
    user = _admin(db)
    h = _hospital(db)
    g = _gaiola(db, h)

    resp = client.post("/api/v1/transportes/", json={
        "gaiola_id": str(g.id),
        "tipo": "ida",
        "motorista": "João",
        "veiculo": "ABC-1234",
    }, headers=_auth(user))
    assert resp.status_code == 201
    db.refresh(g)
    assert g.status == StatusGaiola.EM_TRANSPORTE_IDA


def test_create_transporte_volta_sets_status(client, db):
    user = _admin(db)
    h = _hospital(db)
    g = _gaiola(db, h, status=StatusGaiola.PRONTA_EXPEDICAO)

    resp = client.post("/api/v1/transportes/", json={
        "gaiola_id": str(g.id),
        "tipo": "volta",
    }, headers=_auth(user))
    assert resp.status_code == 201
    db.refresh(g)
    assert g.status == StatusGaiola.EM_TRANSPORTE_VOLTA


def test_update_transporte_entregue(client, db):
    user = _admin(db)
    h = _hospital(db)
    g = _gaiola(db, h, status=StatusGaiola.EM_TRANSPORTE_VOLTA)

    t = Transporte(
        id=uuid.uuid4(), gaiola_id=g.id,
        tipo=TipoTransporte.VOLTA, status=StatusTransporte.EM_TRANSPORTE,
        data_saida=datetime.now(timezone.utc),
    )
    db.add(t); db.commit()

    resp = client.put(f"/api/v1/transportes/{t.id}", json={"status": "entregue"},
                      headers=_auth(user))
    assert resp.status_code == 200
    db.refresh(g)
    assert g.status == StatusGaiola.ENTREGUE


# ─── Relatorios ───────────────────────────────────────────────────────────────

def test_relatorio_divergencias_empty(client, db):
    user = _admin(db)
    resp = client.get("/api/v1/relatorios/divergencias", headers=_auth(user))
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_relatorio_produtividade(client, db):
    user = _admin(db)
    resp = client.get("/api/v1/relatorios/produtividade", headers=_auth(user))
    assert resp.status_code == 200
    data = resp.json()
    assert "total_gaiolas" in data
    assert "entregues" in data
    assert "peso_total_expedido_kg" in data
    assert "por_status" in data


def test_relatorio_expedicao_csv(client, db):
    user = _admin(db)
    resp = client.get("/api/v1/relatorios/expedicao/csv", headers=_auth(user))
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]


def test_relatorio_expedicao_excel(client, db):
    user = _admin(db)
    resp = client.get("/api/v1/relatorios/expedicao/excel", headers=_auth(user))
    assert resp.status_code == 200
    assert "spreadsheetml" in resp.headers["content-type"]


# ─── Service: balanca_service ─────────────────────────────────────────────────

def test_registrar_pesagem_service(db):
    h = _hospital(db, "H-Svc")
    g = _gaiola(db, h)

    pesagem = balanca_service.registrar_pesagem(
        db=db, gaiola=g,
        tipo_pesagem=TipoPesagem.SAIDA_HOSPITAL,
        peso=50.0,
        balanca_id="B1",
    )
    assert pesagem.id is not None
    assert float(pesagem.peso) == 50.0
    db.refresh(g)
    assert g.status == StatusGaiola.EM_TRANSPORTE_IDA


def test_calcular_divergencia_none_when_missing(db):
    assert balanca_service.calcular_divergencia([]) is None


def test_calcular_divergencia_value(db):
    h = _hospital(db, "H-Div")
    g = _gaiola(db, h)
    p1 = Pesagem(id=uuid.uuid4(), gaiola_id=g.id, tipo_pesagem=TipoPesagem.SAIDA_HOSPITAL,
                 peso=100.0, timestamp=datetime.now(timezone.utc))
    p2 = Pesagem(id=uuid.uuid4(), gaiola_id=g.id, tipo_pesagem=TipoPesagem.EXPEDICAO,
                 peso=90.0, timestamp=datetime.now(timezone.utc))
    db.add_all([p1, p2]); db.commit()
    assert balanca_service.calcular_divergencia([p1, p2]) == 10.0


def test_tem_divergencia_critica(db):
    h = _hospital(db, "H-Crit")
    g = _gaiola(db, h)
    p1 = Pesagem(id=uuid.uuid4(), gaiola_id=g.id, tipo_pesagem=TipoPesagem.SAIDA_HOSPITAL,
                 peso=100.0, timestamp=datetime.now(timezone.utc))
    p2 = Pesagem(id=uuid.uuid4(), gaiola_id=g.id, tipo_pesagem=TipoPesagem.EXPEDICAO,
                 peso=90.0, timestamp=datetime.now(timezone.utc))
    db.add_all([p1, p2]); db.commit()
    assert balanca_service.tem_divergencia_critica([p1, p2], limite=5.0) is True
    assert balanca_service.tem_divergencia_critica([p1, p2], limite=15.0) is False


# ─── Service: notificacao_service ─────────────────────────────────────────────

def test_notificacao_registrada():
    notificacao_service.limpar_notificacoes()
    notificacao_service.notificar_mudanca_status(
        gaiola_codigo="GAI-TEST",
        status_anterior="CRIADA",
        status_novo="EM_TRANSPORTE_IDA",
        usuario="op@test.com",
    )
    notifs = notificacao_service.get_notificacoes_recentes(10)
    assert len(notifs) == 1
    assert notifs[0]["gaiola_codigo"] == "GAI-TEST"
    assert notifs[0]["status_novo"] == "EM_TRANSPORTE_IDA"
    notificacao_service.limpar_notificacoes()


def test_notificacao_limite():
    notificacao_service.limpar_notificacoes()
    for i in range(10):
        notificacao_service.notificar_mudanca_status(f"G-{i}", "A", "B")
    assert len(notificacao_service.get_notificacoes_recentes(5)) == 5
    notificacao_service.limpar_notificacoes()


# ─── Service: relatorio_service ───────────────────────────────────────────────

def test_relatorio_produtividade_service_com_dados(db):
    h = _hospital(db, "H-Prod")
    g = _gaiola(db, h, status=StatusGaiola.ENTREGUE)

    inicio = datetime.now(timezone.utc) - timedelta(minutes=30)
    fim = datetime.now(timezone.utc)
    proc = Processo(
        id=uuid.uuid4(), gaiola_id=g.id, etapa=EtapaProcesso.LAVAGEM,
        data_inicio=inicio, data_fim=fim,
    )
    db.add(proc); db.commit()

    resultado = relatorio_service.relatorio_produtividade(db)
    assert resultado["total_gaiolas"] >= 1
    assert resultado["processos_concluidos_por_etapa"].get("lavagem", 0) >= 1
    assert resultado["tempo_medio_min_por_etapa"]["lavagem"] == pytest.approx(30.0, abs=1.0)


def test_build_rows_expedicao_com_pesagens(db):
    h = _hospital(db, "H-Rows")
    g = _gaiola(db, h)
    p1 = Pesagem(id=uuid.uuid4(), gaiola_id=g.id, tipo_pesagem=TipoPesagem.SAIDA_HOSPITAL,
                 peso=100.0, timestamp=datetime.now(timezone.utc))
    p2 = Pesagem(id=uuid.uuid4(), gaiola_id=g.id, tipo_pesagem=TipoPesagem.EXPEDICAO,
                 peso=94.0, timestamp=datetime.now(timezone.utc))
    db.add_all([p1, p2]); db.commit(); db.refresh(g)
    rows = relatorio_service.build_rows_expedicao([g])
    assert len(rows) == 1
    assert rows[0]["Divergência (%)"] == pytest.approx(6.0, abs=0.01)

