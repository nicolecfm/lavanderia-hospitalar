#!/bin/bash
set -e

echo "Aguardando o banco de dados..."
sleep 5

echo "Executando migrations..."
cd /app/backend
alembic upgrade head

echo "Executando seed de dados..."
python seed.py

echo "Iniciando servidor..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
