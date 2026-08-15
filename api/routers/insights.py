"""Painel de insights: agrega os dados do usuario (logbook + estoque) em
metricas prontas para o dashboard — sem pedir nada de fora.

Stateless e no escopo do usuario. O custo por municao reusa o
ReloadingService (mesmo calculo do resto do app, sobre o preco de estoque).
"""

from types import SimpleNamespace

from fastapi import APIRouter, Depends

from api.security import get_current_user
from core.models import InventoryItem, ReloadSession, managed_session
from services.reloading_service import ReloadingService

router = APIRouter(prefix="/api", tags=["insights"])

#  Mesmos limites de "estoque baixo" do app (por categoria; padrao 20).
_LOW_STOCK = {"Pólvora": 100, "Espoleta": 100, "Projétil": 50, "Estojo": 50}


def _low_threshold(category: str) -> float:
    return _LOW_STOCK.get(category, 20)


def _session_ns(s: ReloadSession) -> SimpleNamespace:
    return SimpleNamespace(
        powder=s.powder, charge=s.charge, projectile=s.projectile,
        primer=s.primer, case=s.case, quantity=s.quantity,
    )


@router.get("/insights")
def insights(current=Depends(get_current_user)) -> dict:
    uid = current["id"]
    with managed_session() as db:
        sessions = (
            db.query(ReloadSession).filter_by(user_id=uid).order_by(ReloadSession.date.asc()).all()
        )
        rows = [{
            "id": s.id,
            "date": s.date.isoformat() if s.date else None,
            "caliber": s.caliber,
            "powder": s.powder,
            "charge": s.charge,
            "projectile": s.projectile,
            "quantity": s.quantity or 0,
            "velocity_avg": s.velocity_avg,
            "velocity_sd": s.velocity_sd,
            "grouping_mm": s.grouping_mm,
        } for s in sessions]

        #  Custo unitario por sessao (so quando ha polvora + carga).
        costs = {}
        for s in sessions:
            if s.powder and s.charge:
                try:
                    c = ReloadingService.calculate_unit_cost(_session_ns(s), uid)
                    if c and c > 0:
                        costs[s.id] = round(c, 2)
                except Exception:
                    pass

        inv = db.query(InventoryItem).filter_by(user_id=uid).all()
        inventory_value = round(sum((i.quantity or 0) * (i.price_unit or 0) for i in inv), 2)
        low_stock = sum(
            1 for i in inv
            if 0 < (i.quantity or 0) <= _low_threshold(i.category)
        )
        zero_stock = sum(1 for i in inv if (i.quantity or 0) <= 0)

    rounds = sum(r["quantity"] for r in rows)
    groups = [r["grouping_mm"] for r in rows if r["grouping_mm"]]
    sds = [r["velocity_sd"] for r in rows if r["velocity_sd"]]

    def _rank(key, reverse=False):
        picked = [r for r in rows if r[key]]
        picked.sort(key=lambda r: r[key], reverse=reverse)
        return [{
            "date": r["date"], "caliber": r["caliber"], "powder": r["powder"],
            "charge": r["charge"], "value": round(r[key], 2),
            "velocity_avg": r["velocity_avg"],
        } for r in picked[:5]]

    return {
        "totals": {
            "sessions": len(rows),
            "rounds": rounds,
            "best_group_mm": round(min(groups), 2) if groups else None,
            "avg_sd": round(sum(sds) / len(sds), 1) if sds else None,
            "inventory_value": inventory_value,
            "low_stock_count": low_stock,
            "zero_stock_count": zero_stock,
        },
        #  Series temporais para os graficos (ordem cronologica).
        "velocity_trend": [
            {"date": r["date"], "velocity_avg": r["velocity_avg"], "velocity_sd": r["velocity_sd"]}
            for r in rows if r["velocity_avg"]
        ],
        "cost_trend": [
            {"date": r["date"], "caliber": r["caliber"], "unit_cost": costs[r["id"]]}
            for r in rows if r["id"] in costs
        ],
        "best_by_group": _rank("grouping_mm"),   # menor agrupamento
        "best_by_sd": _rank("velocity_sd"),      # menor desvio-padrao
    }
