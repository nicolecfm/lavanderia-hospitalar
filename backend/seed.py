"""
Script de inicialização com dados de exemplo.
Cria usuários, hospitais, gaiolas, pesagens e transportes de exemplo.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine
from app.models import Base
from app.models.user import Usuario, TipoUsuario
from app.models.hospital import Hospital
from app.models.gaiola import Gaiola, StatusGaiola
from app.models.pesagem import Pesagem, TipoPesagem
from app.models.transporte import Transporte, TipoTransporte, StatusTransporte
from app.utils.security import get_password_hash
from datetime import datetime, timezone
import uuid

def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # ── Usuários ───────────────────────────────────────────────────────────

        if not db.query(Usuario).filter(Usuario.email == "admin@lavanderia.com").first():
            db.add(Usuario(
                id=uuid.uuid4(), nome="Administrador",
                email="admin@lavanderia.com",
                senha_hash=get_password_hash("admin123"),
                tipo_usuario=TipoUsuario.ADMIN, ativo=True,
            ))
            print("✓ admin@lavanderia.com / admin123")
        else:
            print("- admin@lavanderia.com já existe")

        if not db.query(Usuario).filter(Usuario.email == "hospital@lavanderia.com").first():
            db.add(Usuario(
                id=uuid.uuid4(), nome="Operador Hospital",
                email="hospital@lavanderia.com",
                senha_hash=get_password_hash("hospital123"),
                tipo_usuario=TipoUsuario.OPERADOR_HOSPITAL, ativo=True,
            ))
            print("✓ hospital@lavanderia.com / hospital123")
        else:
            print("- hospital@lavanderia.com já existe")

        if not db.query(Usuario).filter(Usuario.email == "lavanderia@lavanderia.com").first():
            db.add(Usuario(
                id=uuid.uuid4(), nome="Operador Lavanderia",
                email="lavanderia@lavanderia.com",
                senha_hash=get_password_hash("lavanderia123"),
                tipo_usuario=TipoUsuario.OPERADOR_LAVANDERIA, ativo=True,
            ))
            print("✓ lavanderia@lavanderia.com / lavanderia123")
        else:
            print("- lavanderia@lavanderia.com já existe")

        db.commit()

        # ── Hospitais ──────────────────────────────────────────────────────────

        h1 = db.query(Hospital).filter(Hospital.cnpj == "12.345.678/0001-90").first()
        if not h1:
            h1 = Hospital(
                id=uuid.uuid4(), nome="Hospital São Lucas",
                cnpj="12.345.678/0001-90",
                endereco="Av. Brasil, 1000 - Centro",
                telefone="(11) 3456-7890",
                email="contato@saolucas.com.br", ativo=True,
            )
            db.add(h1)
            print("✓ Hospital São Lucas criado")
        else:
            print("- Hospital São Lucas já existe")

        h2 = db.query(Hospital).filter(Hospital.cnpj == "98.765.432/0001-10").first()
        if not h2:
            h2 = Hospital(
                id=uuid.uuid4(), nome="Hospital Santa Maria",
                cnpj="98.765.432/0001-10",
                endereco="Rua das Flores, 500 - Jardim América",
                telefone="(11) 9876-5432",
                email="contato@santamaria.com.br", ativo=True,
            )
            db.add(h2)
            print("✓ Hospital Santa Maria criado")
        else:
            print("- Hospital Santa Maria já existe")

        db.commit()
        db.refresh(h1)
        db.refresh(h2)

        # ── Gaiolas ────────────────────────────────────────────────────────────

        gaiolas_spec = [
            ("GAI-001", h1, StatusGaiola.EM_LAVAGEM,         "Roupas cirúrgicas"),
            ("GAI-002", h2, StatusGaiola.PRONTA_EXPEDICAO,   "Uniformes e lençóis"),
            ("GAI-003", h1, StatusGaiola.EM_TRANSPORTE_VOLTA, "Toalhas e avental"),
            ("GAI-004", h2, StatusGaiola.RECEBIDA_LAVANDERIA, "Roupas de cama"),
            ("GAI-005", h1, StatusGaiola.ENTREGUE,            "Aventais cirúrgicos"),
        ]

        gaiola_objs: dict[str, Gaiola] = {}
        for codigo, hospital, status, obs in gaiolas_spec:
            g = db.query(Gaiola).filter(Gaiola.codigo == codigo).first()
            if not g:
                g = Gaiola(
                    id=uuid.uuid4(), codigo=codigo,
                    hospital_id=hospital.id, status=status,
                    data_criacao=datetime.now(timezone.utc),
                    observacoes=obs,
                )
                db.add(g)
                db.flush()
                print(f"✓ Gaiola {codigo} criada ({status.value})")
            else:
                print(f"- Gaiola {codigo} já existe")
            gaiola_objs[codigo] = g

        db.commit()

        # ── Pesagens ───────────────────────────────────────────────────────────

        def _add_pesagem(gaiola, tipo, peso, balanca="BAL-001"):
            if not db.query(Pesagem).filter(
                Pesagem.gaiola_id == gaiola.id,
                Pesagem.tipo_pesagem == tipo,
            ).first():
                db.add(Pesagem(
                    id=uuid.uuid4(), gaiola_id=gaiola.id,
                    tipo_pesagem=tipo, peso=peso,
                    balanca_id=balanca, timestamp=datetime.now(timezone.utc),
                ))

        g1 = gaiola_objs["GAI-001"]
        _add_pesagem(g1, TipoPesagem.SAIDA_HOSPITAL,          45.500, "BAL-001")
        _add_pesagem(g1, TipoPesagem.RECEBIMENTO_LAVANDERIA,  45.200, "BAL-002")

        g2 = gaiola_objs["GAI-002"]
        _add_pesagem(g2, TipoPesagem.SAIDA_HOSPITAL,          62.000, "BAL-001")
        _add_pesagem(g2, TipoPesagem.RECEBIMENTO_LAVANDERIA,  61.800, "BAL-002")
        _add_pesagem(g2, TipoPesagem.EXPEDICAO,               58.500, "BAL-003")

        g5 = gaiola_objs["GAI-005"]
        _add_pesagem(g5, TipoPesagem.SAIDA_HOSPITAL,          38.000, "BAL-001")
        _add_pesagem(g5, TipoPesagem.RECEBIMENTO_LAVANDERIA,  37.800, "BAL-002")
        _add_pesagem(g5, TipoPesagem.EXPEDICAO,               36.000, "BAL-003")

        db.commit()

        # ── Transportes ────────────────────────────────────────────────────────

        g3 = gaiola_objs["GAI-003"]
        if not db.query(Transporte).filter(
            Transporte.gaiola_id == g3.id,
            Transporte.tipo == TipoTransporte.VOLTA,
        ).first():
            db.add(Transporte(
                id=uuid.uuid4(), gaiola_id=g3.id,
                tipo=TipoTransporte.VOLTA, motorista="Carlos Silva",
                veiculo="Van Branca", status=StatusTransporte.EM_TRANSPORTE,
                data_saida=datetime.now(timezone.utc),
            ))
            print("✓ Transporte de volta para GAI-003 criado")

        if not db.query(Transporte).filter(
            Transporte.gaiola_id == g5.id,
            Transporte.tipo == TipoTransporte.IDA,
        ).first():
            db.add(Transporte(
                id=uuid.uuid4(), gaiola_id=g5.id,
                tipo=TipoTransporte.IDA, motorista="Roberto Souza",
                veiculo="Caminhão Baú", status=StatusTransporte.ENTREGUE,
                data_saida=datetime.now(timezone.utc),
                data_chegada=datetime.now(timezone.utc),
            ))
            print("✓ Transporte de ida para GAI-005 criado")

        db.commit()
        print("\n✅ Seed concluído com sucesso!")
    except Exception as e:
        db.rollback()
        print(f"❌ Erro durante o seed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
