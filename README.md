# Lavanderia Hospitalar 🏥

Sistema web completo para gerenciar o fluxo operacional de lavanderia hospitalar, desde a separação das roupas no hospital até o retorno ao cliente.

## Funcionalidades

- **Rastreamento completo de gaiolas** com 10 status diferentes
- **Integração com balança** via API REST
- **Dashboard em tempo real** com estatísticas e alertas de divergência de peso
- **Gestão de hospitais/clientes** com CRUD completo
- **Controle de pesagens** (saída, recebimento, expedição)
- **Gestão de transportes** (ida e volta)
- **Controle de processos** (separação, lavagem, secagem, dobra)
- **Geração de QR Code** para identificação de gaiolas
- **Relatórios** em Excel e CSV com alertas de divergência
- **Autenticação JWT** com 4 níveis de acesso
- **Interface responsiva** em português (PT-BR)

## Pré-requisitos

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Instalação e Execução

### 1. Clonar o repositório

```bash
git clone <url-do-repositorio>
cd lavanderia-hospitalar
```

### 2. Configurar variáveis de ambiente

```bash
cp .env.example .env
# Edite o .env se necessário (opcional para ambiente de desenvolvimento)
```

### 3. Subir os containers

```bash
docker-compose up --build
```

O sistema irá automaticamente:
1. Iniciar o banco de dados PostgreSQL
2. Executar as migrations do Alembic
3. Carregar dados de exemplo (seed)
4. Iniciar o servidor FastAPI

### 4. Acessar a aplicação

- **Interface Web:** http://localhost:8000
- **Documentação API (Swagger):** http://localhost:8000/api/docs
- **Documentação API (ReDoc):** http://localhost:8000/api/redoc

## Credenciais Padrão

| Campo | Valor |
|-------|-------|
| Email | `admin@lavanderia.com` |
| Senha | `admin123` |

## Dados de Exemplo (Seed)

O sistema cria automaticamente:
- 1 usuário administrador
- 2 hospitais: Hospital São Lucas e Clínica Santa Maria
- 3 gaiolas em diferentes status: GAI-001 (Em Lavagem), GAI-002 (Pronta Expedição), GAI-003 (Em Transporte Volta)

## API de Integração com Balança

### Endpoint

```
POST /api/v1/pesagens/balanca
```

### Formato da requisição

```json
{
  "gaiola_codigo": "GAI-001",
  "peso": 45.500,
  "tipo_pesagem": "saida_hospital",
  "balanca_id": "BALANCA-001",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Valores para `tipo_pesagem`

| Valor | Descrição |
|-------|-----------|
| `saida_hospital` | Pesagem na saída do hospital |
| `recebimento_lavanderia` | Pesagem no recebimento na lavanderia |
| `expedicao` | Pesagem na expedição da lavanderia |

## Principais Endpoints da API

### Autenticação
- `POST /api/v1/auth/token` - Login (retorna access_token e refresh_token)
- `GET /api/v1/auth/me` - Dados do usuário logado

### Gaiolas
- `GET /api/v1/gaiolas/` - Listar gaiolas
- `POST /api/v1/gaiolas/` - Criar gaiola
- `GET /api/v1/gaiolas/{id}` - Detalhes da gaiola
- `PUT /api/v1/gaiolas/{id}` - Atualizar gaiola
- `GET /api/v1/gaiolas/{id}/qrcode` - Download QR Code

### Hospitais
- `GET /api/v1/hospitais/` - Listar hospitais
- `POST /api/v1/hospitais/` - Criar hospital
- `PUT /api/v1/hospitais/{id}` - Atualizar hospital

### Pesagens
- `GET /api/v1/pesagens/` - Listar pesagens
- `POST /api/v1/pesagens/` - Registrar pesagem manual
- `POST /api/v1/pesagens/balanca` - Receber dados da balança (sem autenticação)

### Transportes
- `GET /api/v1/transportes/` - Listar transportes
- `POST /api/v1/transportes/` - Registrar transporte
- `PUT /api/v1/transportes/{id}` - Atualizar transporte

### Processos
- `GET /api/v1/processos/` - Listar processos
- `POST /api/v1/processos/` - Iniciar processo
- `PUT /api/v1/processos/{id}` - Finalizar processo

### Relatórios
- `GET /api/v1/relatorios/expedicao/excel` - Relatório em Excel
- `GET /api/v1/relatorios/expedicao/csv` - Relatório em CSV
- `GET /api/v1/relatorios/divergencias` - Relatório de divergências

## Status da Gaiola

| Status | Descrição |
|--------|-----------|
| `CRIADA` | Gaiola registrada no sistema |
| `EM_TRANSPORTE_IDA` | Em transporte para a lavanderia |
| `RECEBIDA_LAVANDERIA` | Recebida na lavanderia |
| `EM_SEPARACAO` | Em processo de separação |
| `EM_LAVAGEM` | Em lavagem |
| `EM_SECAGEM` | Em secagem |
| `EM_DOBRA` | Em dobra |
| `PRONTA_EXPEDICAO` | Pronta para expedição |
| `EM_TRANSPORTE_VOLTA` | Em transporte de retorno |
| `ENTREGUE` | Entregue ao hospital |

## Executar Migrations Manualmente

```bash
cd backend
alembic upgrade head
```

## Executar Testes

```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v
```

## Níveis de Acesso

| Tipo | Descrição |
|------|-----------|
| `admin` | Acesso total ao sistema |
| `operador_hospital` | Operações no hospital |
| `operador_lavanderia` | Operações na lavanderia |
| `motorista` | Registro de transportes |

## Estrutura do Projeto

```
lavanderia-hospitalar/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI app principal
│   │   ├── config.py         # Configurações
│   │   ├── database.py       # Conexão com banco
│   │   ├── models/           # Modelos SQLAlchemy
│   │   ├── schemas/          # Schemas Pydantic
│   │   ├── routers/          # Rotas da API
│   │   ├── services/         # Serviços
│   │   └── utils/            # Utilitários
│   ├── migrations/           # Migrações Alembic
│   ├── tests/                # Testes pytest
│   ├── seed.py               # Dados de exemplo
│   └── requirements.txt
├── frontend/
│   ├── static/               # CSS, JS, imagens
│   └── templates/            # Templates Jinja2
├── docker-compose.yml
├── Dockerfile
└── .env.example
```

## Alertas de Divergência

O sistema alerta automaticamente quando a divergência de peso entre a saída do hospital e a expedição da lavanderia ultrapassa **5%**.

## Tecnologias

- **Backend:** Python 3.11 + FastAPI
- **Frontend:** Jinja2 + Bootstrap 5
- **Banco de Dados:** PostgreSQL 15
- **ORM:** SQLAlchemy 2.0
- **Autenticação:** JWT (python-jose)
- **Senhas:** bcrypt (passlib)
- **Migrações:** Alembic
- **Exportação:** openpyxl (Excel), CSV nativo
- **QR Code:** qrcode[pil]
- **Containerização:** Docker + Docker Compose
