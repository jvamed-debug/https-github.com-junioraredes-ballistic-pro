"""Testes da API de balistica (FastAPI). Cobrem catalogo, trajetoria e a
inclusao opcional do cartao de DOPE — a fatia stateless da API."""

import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_list_calibers_is_nonempty_and_excludes_removed_ones():
    r = client.get("/api/catalog/calibers")
    assert r.status_code == 200
    names = r.json()
    assert isinstance(names, list) and names
    #  Os calibres sem respaldo removidos no PR #42 nao voltam pela API.
    assert ".357 MAGNUM" not in names
    assert ".44 REM. MAGNUM" not in names


def test_caliber_details_404_for_unknown():
    assert client.get("/api/catalog/caliber/NAO_EXISTE").status_code == 404


def test_full_catalog_has_calibers_key():
    r = client.get("/api/catalog")
    assert r.status_code == 200
    assert "calibers" in r.json()


def _traj_body(**over):
    body = {
        "projectile": {
            "weight_grains": 168,
            "bc_g1": 0.462,
            "muzzle_velocity_fps": 2650,
        },
        "zero_range_m": 100,
        "max_range_m": 300,
        "step_m": 100,
    }
    body.update(over)
    return body


def test_trajectory_returns_points():
    r = client.post("/api/trajectory", json=_traj_body())
    assert r.status_code == 200
    data = r.json()
    assert data["points"]
    assert data["dope_card"] is None  # sem bloco dope, nao vem cartao
    ranges = [p["range_m"] for p in data["points"]]
    assert ranges == sorted(ranges)


def test_trajectory_with_dope_includes_card_in_clicks():
    body = _traj_body(dope={"unit": "MIL", "click_value": 0.1, "incline_deg": 0})
    r = client.post("/api/trajectory", json=body)
    assert r.status_code == 200
    card = r.json()["dope_card"]
    assert card is not None and len(card) == len(r.json()["points"])
    for e in card:
        assert e["unit"] == "MIL"
        assert isinstance(e["elevation_clicks"], int)
    #  Alem do zero a elevacao (come-up) nao pode ser negativa.
    past_zero = [e for e in card if e["range_m"] > 100]
    assert all(e["elevation"] >= 0 for e in past_zero)


def test_incline_reduces_come_up():
    flat = client.post("/api/trajectory", json=_traj_body(
        max_range_m=400, step_m=100,
        dope={"unit": "MIL", "click_value": 0.1, "incline_deg": 0},
    )).json()["dope_card"][-1]["elevation"]
    steep = client.post("/api/trajectory", json=_traj_body(
        max_range_m=400, step_m=100,
        dope={"unit": "MIL", "click_value": 0.1, "incline_deg": 40},
    )).json()["dope_card"][-1]["elevation"]
    assert flat > 0 and steep < flat


def test_trajectory_rejects_max_below_zero():
    r = client.post("/api/trajectory", json=_traj_body(zero_range_m=300, max_range_m=100))
    assert r.status_code == 422


def test_trajectory_validates_projectile():
    r = client.post("/api/trajectory", json=_traj_body(
        projectile={"weight_grains": -5, "muzzle_velocity_fps": 2650}
    ))
    assert r.status_code == 422
