"""Testes da analise de alvo por foto (visao computacional).

Usam um alvo sintetico (fundo branco com furos pretos) para exercitar o
caminho real: deteccao, agrupamento, imagem anotada e PDF de performance —
sem depender de uma foto de verdade. A afinacao dos filtros de CV tem
cobertura propria em test_cv_utils.
"""

import importlib
import io

import numpy as np
import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

cv2 = pytest.importorskip("cv2")


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'api.db'}")
    monkeypatch.setenv("FERNET_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("JWT_SECRET", "test-secret")

    import core.models as models
    importlib.reload(models)
    import core.auth as auth
    importlib.reload(auth)
    import api.security as security
    importlib.reload(security)
    for mod in ("api.routers.auth", "api.routers.targets", "api.main"):
        importlib.reload(importlib.import_module(mod))
    import api.main as main

    models.Base.metadata.create_all(models.engine)
    models.ensure_schema_compliance(models.engine)
    return TestClient(main.app)


def _auth(client, username="alice"):
    client.post("/api/auth/register", json={"username": username, "password": "senha1234"})
    tok = client.post("/api/auth/login", json={
        "username": username, "password": "senha1234",
    }).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def _target_png(holes=((300, 300), (345, 320), (320, 365))) -> bytes:
    img = np.full((800, 800, 3), 255, np.uint8)
    for (x, y) in holes:
        cv2.circle(img, (x, y), 15, (0, 0, 0), -1)
    ok, buf = cv2.imencode(".png", img)
    return buf.tobytes()


def _blank_png() -> bytes:
    img = np.full((800, 800, 3), 255, np.uint8)
    ok, buf = cv2.imencode(".png", img)
    return buf.tobytes()


class TestAnalyze:
    def test_detects_shots_and_returns_annotated_image(self, client):
        h = _auth(client)
        r = client.post(
            "/api/targets/analyze",
            headers=h,
            files={"file": ("alvo.png", _target_png(), "image/png")},
            data={"target_width_mm": "210", "sensitivity": "155"},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["shot_count"] == 3
        assert len(body["groups"]) == 1
        assert body["groups"][0]["group_size_mm"] > 0
        assert body["annotated_image"].startswith("data:image/png;base64,")

    def test_center_point_yields_poi(self, client):
        h = _auth(client)
        r = client.post(
            "/api/targets/analyze",
            headers=h,
            files={"file": ("alvo.png", _target_png(), "image/png")},
            data={"center_x": "400", "center_y": "400"},
        )
        poi = r.json()["groups"][0]["poi_mm"]
        #  Furos à esquerda/abaixo do centro -> desvio não-nulo.
        assert poi != [0.0, 0.0]

    def test_requires_auth(self, client):
        r = client.post(
            "/api/targets/analyze",
            files={"file": ("alvo.png", _target_png(), "image/png")},
        )
        assert r.status_code == 401

    def test_rejects_non_image(self, client):
        h = _auth(client)
        r = client.post(
            "/api/targets/analyze",
            headers=h,
            files={"file": ("x.txt", b"nao sou imagem", "text/plain")},
        )
        assert r.status_code == 400


class TestReport:
    def test_returns_pdf(self, client):
        h = _auth(client)
        r = client.post(
            "/api/targets/report",
            headers=h,
            files={"file": ("alvo.png", _target_png(), "image/png")},
            data={"center_x": "400", "center_y": "400"},
        )
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/pdf"
        assert r.content[:5] == b"%PDF-"

    def test_422_when_no_impacts(self, client):
        h = _auth(client)
        r = client.post(
            "/api/targets/report",
            headers=h,
            files={"file": ("branco.png", _blank_png(), "image/png")},
        )
        assert r.status_code == 422
