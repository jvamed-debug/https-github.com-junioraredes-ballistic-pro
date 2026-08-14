"""Testes da API de dados de recarga (FastAPI): avisos de seguranca e
estimador de carga. A logica de fundo ja tem cobertura em test_cbc_powders,
test_cartridge_specs e test_ballistics_service; aqui garantimos que a camada
HTTP monta a severidade certa e liga os services corretos."""

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def _warnings(**params):
    r = client.get("/api/reloading/warnings", params=params)
    assert r.status_code == 200
    return r.json()["warnings"]


def test_series_swap_is_blocking():
    #  Polvora Serie 200 (arma curta) num cartucho de rifle: o fabricante
    #  proibe expressamente -> severidade "erro".
    ws = _warnings(caliber=".223 REMINGTON", powder="CBC 216")
    assert any(w["severity"] == "erro" for w in ws)


def test_usage_warning_is_surfaced():
    ws = _warnings(caliber=".223 REMINGTON", powder="CBC 216")
    assert any("municao militar" in w["message"].lower() for w in ws)


def test_referenced_combo_has_no_warnings():
    #  .38 SPL com CBC 216 consta nas fontes publicadas -> sem reparos.
    assert _warnings(caliber=".38 SPL", powder="CBC 216") == []


def test_unmapped_caliber_returns_empty_not_error():
    #  Silencio aqui significa "sem base para julgar", nao "aprovado".
    r = client.get("/api/reloading/warnings", params={"caliber": "NAO_EXISTE"})
    assert r.status_code == 200
    assert r.json()["warnings"] == []


def test_primer_size_mismatch_is_caution():
    #  .38 SPL usa Small Pistol; indicar Large gera aviso (nao bloqueio).
    ws = _warnings(caliber=".38 SPL", powder="CBC 216", primer="Large Pistol")
    assert any(w["severity"] == "aviso" and "espoleta" in w["message"].lower() for w in ws)


def test_overall_length_over_max_is_caution():
    ws = _warnings(caliber=".38 SPL", powder="CBC 216", oal_mm=99)
    assert any("comprimento total" in w["message"].lower() for w in ws)


def test_estimate_returns_energy_and_charge():
    r = client.post(
        "/api/reloading/estimate",
        json={
            "projectile_grains": 147,
            "velocity_fps": 1000,
            "calorific_j_per_g": 4000,
            "efficiency_percent": 30,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["energy_j"] > 0
    assert data["energy_ftlbs"] > 0
    assert data["estimated_charge_grains"] > 0


def test_estimate_rejects_nonpositive_velocity():
    r = client.post(
        "/api/reloading/estimate",
        json={"projectile_grains": 147, "velocity_fps": 0},
    )
    assert r.status_code == 422
