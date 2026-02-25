"""initial tables

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "usuarios",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("nome", sa.String(200), nullable=False),
        sa.Column("email", sa.String(200), nullable=False, unique=True),
        sa.Column("senha_hash", sa.String(255), nullable=False),
        sa.Column("tipo_usuario", sa.Enum(
            "admin", "operador_hospital", "operador_lavanderia", "motorista",
            name="tipousuario"
        ), nullable=False),
        sa.Column("ativo", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "hospitais",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("nome", sa.String(300), nullable=False),
        sa.Column("cnpj", sa.String(20), unique=True, nullable=True),
        sa.Column("endereco", sa.String(500), nullable=True),
        sa.Column("telefone", sa.String(20), nullable=True),
        sa.Column("email", sa.String(200), nullable=True),
        sa.Column("ativo", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "gaiolas",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("codigo", sa.String(100), nullable=False, unique=True),
        sa.Column("qr_code_url", sa.String(500), nullable=True),
        sa.Column("hospital_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("hospitais.id"), nullable=False),
        sa.Column("status", sa.Enum(
            "CRIADA", "EM_TRANSPORTE_IDA", "RECEBIDA_LAVANDERIA", "EM_SEPARACAO",
            "EM_LAVAGEM", "EM_SECAGEM", "EM_DOBRA", "PRONTA_EXPEDICAO",
            "EM_TRANSPORTE_VOLTA", "ENTREGUE", name="statusgaiola"
        ), nullable=False),
        sa.Column("data_criacao", sa.DateTime(timezone=True)),
        sa.Column("observacoes", sa.Text, nullable=True),
    )

    op.create_table(
        "pesagens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("gaiola_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("gaiolas.id"), nullable=False),
        sa.Column("tipo_pesagem", sa.Enum(
            "saida_hospital", "recebimento_lavanderia", "expedicao",
            name="tipopesagem"
        ), nullable=False),
        sa.Column("peso", sa.Numeric(10, 3), nullable=False),
        sa.Column("balanca_id", sa.String(100), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True)),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("usuarios.id"), nullable=True),
        sa.Column("divergencia_percentual", sa.Numeric(5, 2), nullable=True),
        sa.Column("alerta_divergencia", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("observacoes", sa.Text, nullable=True),
    )

    op.create_table(
        "transportes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("gaiola_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("gaiolas.id"), nullable=False),
        sa.Column("tipo", sa.Enum("ida", "volta", name="tipotransporte"), nullable=False),
        sa.Column("motorista", sa.String(200), nullable=True),
        sa.Column("veiculo", sa.String(100), nullable=True),
        sa.Column("data_saida", sa.DateTime(timezone=True)),
        sa.Column("data_chegada", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.Enum("em_transporte", "entregue", name="statustransporte"), nullable=False),
    )

    op.create_table(
        "processos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("gaiola_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("gaiolas.id"), nullable=False),
        sa.Column("etapa", sa.Enum("separacao", "lavagem", "secagem", "dobra", name="etapaprocesso"), nullable=False),
        sa.Column("data_inicio", sa.DateTime(timezone=True)),
        sa.Column("data_fim", sa.DateTime(timezone=True), nullable=True),
        sa.Column("maquina_id", sa.String(100), nullable=True),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("usuarios.id"), nullable=True),
        sa.Column("observacoes", sa.Text, nullable=True),
    )


def downgrade() -> None:
    op.drop_table("processos")
    op.drop_table("transportes")
    op.drop_table("pesagens")
    op.drop_table("gaiolas")
    op.drop_table("hospitais")
    op.drop_table("usuarios")
    op.execute("DROP TYPE IF EXISTS tipousuario")
    op.execute("DROP TYPE IF EXISTS statusgaiola")
    op.execute("DROP TYPE IF EXISTS tipopesagem")
    op.execute("DROP TYPE IF EXISTS tipotransporte")
    op.execute("DROP TYPE IF EXISTS statustransporte")
    op.execute("DROP TYPE IF EXISTS etapaprocesso")
