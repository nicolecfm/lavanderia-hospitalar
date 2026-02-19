"""
Script de inicialização com dados de exemplo.
Cria usuário admin, 2 hospitais e 3 gaiolas em diferentes status.
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
from app.utils.security import get_password_hash
from datetime import datetime, timezone
import uuid

def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Admin user
        if not db.query(Usuario).filter(Usuario.email == "admin@lavanderia.com").first():
            admin = Usuario(
                id=uuid.uuid4(),
                nome="Administrador",
                email="admin@lavanderia.com",
                senha_hash=get_password_hash("admin123"),
                tipo_usuario=TipoUsuario.ADMIN,
                ativo=True,
            )
            db.add(admin)
            print("✓ Usuário admin criado: admin@lavanderia.com / admin123")
        else:
            print("- Usuário admin já existe")

        # Hospital 1
        h1 = db.query(Hospital).filter(Hospital.cnpj == "12.345.678/0001-90").first()
        if not h1:
            h1 = Hospital(
                id=uuid.uuid4(),
                nome="Hospital São Lucas",
                cnpj="12.345.678/0001-90",
                endereco="Av. Brasil, 1000 - Centro",
                telefone="(11) 3456-7890",
                email="contato@saolucas.com.br",
                ativo=True,
            )
            db.add(h1)
            print("✓ Hospital 1 criado: Hospital São Lucas")
        else:
            print("- Hospital São Lucas já existe")

        # Hospital 2
        h2 = db.query(Hospital).filter(Hospital.cnpj == "98.765.432/0001-10").first()
        if not h2:
            h2 = Hospital(
                id=uuid.uuid4(),
                nome="Clínica Santa Maria",
                cnpj="98.765.432/0001-10",
                endereco="Rua das Flores, 500 - Jardim América",
                telefone="(11) 9876-5432",
                email="contato@santamaria.com.br",
                ativo=True,
            )
            db.add(h2)
            print("✓ Hospital 2 criado: Clínica Santa Maria")
        else:
            print("- Clínica Santa Maria já existe")

        db.commit()
        db.refresh(h1)
        db.refresh(h2)

        # Gaiola 1 - Em Lavagem
        if not db.query(Gaiola).filter(Gaiola.codigo == "GAI-001").first():
            g1 = Gaiola(
                id=uuid.uuid4(),
                codigo="GAI-001",
                hospital_id=h1.id,
                status=StatusGaiola.EM_LAVAGEM,
                data_criacao=datetime.now(timezone.utc),
                observacoes="Roupas cirúrgicas",
            )
            db.add(g1)
            db.flush()
            # Pesagens
            db.add(Pesagem(
                id=uuid.uuid4(), gaiola_id=g1.id,
                tipo_pesagem=TipoPesagem.SAIDA_HOSPITAL, peso=45.500,
                balanca_id="BAL-001", timestamp=datetime.now(timezone.utc),
            ))
            db.add(Pesagem(
                id=uuid.uuid4(), gaiola_id=g1.id,
                tipo_pesagem=TipoPesagem.RECEBIMENTO_LAVANDERIA, peso=45.200,
                balanca_id="BAL-002", timestamp=datetime.now(timezone.utc),
            ))
            print("✓ Gaiola 1 criada: GAI-001 (Em Lavagem)")
        else:
            print("- Gaiola GAI-001 já existe")

        # Gaiola 2 - Pronta para Expedição
        if not db.query(Gaiola).filter(Gaiola.codigo == "GAI-002").first():
            g2 = Gaiola(
                id=uuid.uuid4(),
                codigo="GAI-002",
                hospital_id=h2.id,
                status=StatusGaiola.PRONTA_EXPEDICAO,
                data_criacao=datetime.now(timezone.utc),
                observacoes="Uniformes e lençóis",
            )
            db.add(g2)
            db.flush()
            db.add(Pesagem(
                id=uuid.uuid4(), gaiola_id=g2.id,
                tipo_pesagem=TipoPesagem.SAIDA_HOSPITAL, peso=62.000,
                balanca_id="BAL-001", timestamp=datetime.now(timezone.utc),
            ))
            db.add(Pesagem(
                id=uuid.uuid4(), gaiola_id=g2.id,
                tipo_pesagem=TipoPesagem.RECEBIMENTO_LAVANDERIA, peso=61.800,
                balanca_id="BAL-002", timestamp=datetime.now(timezone.utc),
            ))
            db.add(Pesagem(
                id=uuid.uuid4(), gaiola_id=g2.id,
                tipo_pesagem=TipoPesagem.EXPEDICAO, peso=58.500,
                balanca_id="BAL-003", timestamp=datetime.now(timezone.utc),
            ))
            print("✓ Gaiola 2 criada: GAI-002 (Pronta Expedição)")
        else:
            print("- Gaiola GAI-002 já existe")

        # Gaiola 3 - Em Transporte de Volta
        if not db.query(Gaiola).filter(Gaiola.codigo == "GAI-003").first():
            g3 = Gaiola(
                id=uuid.uuid4(),
                codigo="GAI-003",
                hospital_id=h1.id,
                status=StatusGaiola.EM_TRANSPORTE_VOLTA,
                data_criacao=datetime.now(timezone.utc),
                observacoes="Toalhas e avental",
            )
            db.add(g3)
            print("✓ Gaiola 3 criada: GAI-003 (Em Transporte Volta)")
        else:
            print("- Gaiola GAI-003 já existe")

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
