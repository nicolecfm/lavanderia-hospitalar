import uuid
from app.models.user import Usuario, TipoUsuario
from app.models.hospital import Hospital
from app.models.gaiola import Gaiola, StatusGaiola
from app.utils.security import get_password_hash, create_access_token


def create_test_admin(db):
    user = Usuario(
        id=uuid.uuid4(),
        nome="Test Admin",
        email="test@test.com",
        senha_hash=get_password_hash("test123"),
        tipo_usuario=TipoUsuario.ADMIN,
        ativo=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_auth_token(user):
    return create_access_token(data={"sub": user.email})


def test_login_success(client, db):
    user = create_test_admin(db)
    response = client.post("/api/v1/auth/token", json={
        "email": "test@test.com",
        "senha": "test123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client, db):
    create_test_admin(db)
    response = client.post("/api/v1/auth/token", json={
        "email": "test@test.com",
        "senha": "wrongpassword"
    })
    assert response.status_code == 401


def test_get_me(client, db):
    user = create_test_admin(db)
    token = get_auth_token(user)
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@test.com"


def test_create_hospital(client, db):
    user = create_test_admin(db)
    token = get_auth_token(user)
    response = client.post("/api/v1/hospitais/", json={
        "nome": "Hospital Teste",
        "cnpj": "00.000.000/0001-00",
        "telefone": "(11) 1234-5678",
        "email": "teste@hospital.com"
    }, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 201
    data = response.json()
    assert data["nome"] == "Hospital Teste"


def test_list_hospitais(client, db):
    user = create_test_admin(db)
    token = get_auth_token(user)
    hospital = Hospital(id=uuid.uuid4(), nome="H. Listagem", ativo=True)
    db.add(hospital)
    db.commit()
    response = client.get("/api/v1/hospitais/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_gaiola(client, db):
    user = create_test_admin(db)
    token = get_auth_token(user)
    hospital = Hospital(id=uuid.uuid4(), nome="Hospital QR", ativo=True)
    db.add(hospital)
    db.commit()
    db.refresh(hospital)
    response = client.post("/api/v1/gaiolas/", json={
        "codigo": "TEST-001",
        "hospital_id": str(hospital.id),
    }, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 201
    data = response.json()
    assert data["codigo"] == "TEST-001"
    assert data["status"] == "CRIADA"


def test_create_gaiola_duplicate_code(client, db):
    user = create_test_admin(db)
    token = get_auth_token(user)
    hospital = Hospital(id=uuid.uuid4(), nome="H. Dup", ativo=True)
    db.add(hospital)
    db.commit()
    db.refresh(hospital)
    gaiola = Gaiola(id=uuid.uuid4(), codigo="DUP-001", hospital_id=hospital.id, status=StatusGaiola.CRIADA)
    db.add(gaiola)
    db.commit()
    response = client.post("/api/v1/gaiolas/", json={
        "codigo": "DUP-001",
        "hospital_id": str(hospital.id),
    }, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 400


def test_pesagem_balanca_endpoint(client, db):
    """Test the scale integration endpoint."""
    hospital = Hospital(id=uuid.uuid4(), nome="H. Balanca", ativo=True)
    db.add(hospital)
    db.commit()
    db.refresh(hospital)
    gaiola = Gaiola(id=uuid.uuid4(), codigo="BAL-001", hospital_id=hospital.id, status=StatusGaiola.CRIADA)
    db.add(gaiola)
    db.commit()
    response = client.post("/api/v1/pesagens/balanca", json={
        "gaiola_codigo": "BAL-001",
        "peso": 45.500,
        "tipo_pesagem": "saida_hospital",
        "balanca_id": "BALANCA-1",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["peso"] == 45.5
