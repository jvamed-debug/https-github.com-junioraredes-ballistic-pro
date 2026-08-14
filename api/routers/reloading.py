"""Endpoints de dados de recarga: avisos de seguranca e estimador de carga.

Reexpoe, para o frontend React/PWA, o que a aba "Dados de Recarga" do app
Streamlit oferecia: os avisos de seguranca que cruzam calibre + polvora +
espoleta (services/cbc_powders e services/cartridge_specs) e o estimador de
carga por conservacao de energia (services/ballistics_service).

Sao stateless e puros — nao tocam banco nem exigem autenticacao, como o resto
de api/routers/ballistics. O catalogo em si (calibre -> projetil -> polvora,
com carga min/max/velocidade e dimensoes) ja sai por GET /api/catalog; aqui
ficam so as verificacoes que o catalogo cru nao carrega.
"""

from fastapi import APIRouter, Query

from api.schemas import (
    ChargeEstimateIn,
    ChargeEstimateOut,
    ReloadWarning,
    ReloadWarningsOut,
)
from services.ballistics_service import BallisticsService
from services.cartridge_specs import (
    check_overall_length,
    check_primer_size,
    get_usage_warning,
)
from services.cbc_powders import (
    check_powder_for_caliber,
    check_powder_is_referenced,
)

router = APIRouter(prefix="/api/reloading", tags=["reloading"])

#  Severidades, iguais as do app Streamlit (components/logbook_inventory).
BLOCKING = "erro"
CAUTION = "aviso"

JOULES_TO_FTLBS = 0.737562


def _collect_warnings(
    caliber: str | None,
    powder: str | None,
    primer: str | None,
    oal_mm: float | None,
) -> list[ReloadWarning]:
    """Reune os avisos de seguranca de uma combinacao de recarga.

    Espelha components/logbook_inventory.collect_reload_warnings (que importa
    streamlit e por isso nao da para reusar aqui), acrescido da verificacao de
    comprimento total, que o catalogo do frontend tambem consegue alimentar.
    """
    warnings: list[ReloadWarning] = []

    #  Troca de serie 100/200: o fabricante proibe expressamente. Bloqueante.
    series = check_powder_for_caliber(caliber, powder)
    if series:
        warnings.append(ReloadWarning(severity=BLOCKING, message=series))

    #  Procedencia: a combinacao nao consta em nenhuma fonte publicada. Vira
    #  bloqueante quando a polvora e mais viva que as indicadas ("Nao use sem
    #  confirmar"), caso contrario e so cautela.
    provenance = check_powder_is_referenced(caliber, powder)
    if provenance:
        severity = BLOCKING if "Nao use sem confirmar" in provenance else CAUTION
        warnings.append(ReloadWarning(severity=severity, message=provenance))

    primer_warning = check_primer_size(caliber, primer)
    if primer_warning:
        warnings.append(ReloadWarning(severity=CAUTION, message=primer_warning))

    oal_warning = check_overall_length(caliber, oal_mm)
    if oal_warning:
        warnings.append(ReloadWarning(severity=CAUTION, message=oal_warning))

    usage = get_usage_warning(caliber)
    if usage:
        warnings.append(ReloadWarning(severity=CAUTION, message=usage))

    return warnings


@router.get("/warnings", response_model=ReloadWarningsOut)
def reload_warnings(
    caliber: str | None = Query(None),
    powder: str | None = Query(None),
    primer: str | None = Query(None),
    oal_mm: float | None = Query(None),
) -> ReloadWarningsOut:
    """Avisos de seguranca para a combinacao calibre/polvora/espoleta/OAL.

    Lista vazia significa "nenhum reparo com base nas fontes" — nao e um selo
    de aprovacao: um calibre ou polvora fora do catalogo simplesmente nao tem
    como ser verificado.
    """
    return ReloadWarningsOut(
        caliber=caliber,
        powder=powder,
        warnings=_collect_warnings(caliber, powder, primer, oal_mm),
    )


@router.post("/estimate", response_model=ChargeEstimateOut)
def estimate_charge(body: ChargeEstimateIn) -> ChargeEstimateOut:
    """Estima a carga de polvora por conservacao de energia (ordem de grandeza).

    AVISO (auditoria FUN-001): balistica interna NAO e linear. Ignora a curva
    de pressao, o volume da camara e o tempo de queima. Serve para comparar
    ordens de grandeza — NUNCA para definir uma carga real. Consulte sempre
    tabelas oficiais (SAAMI/CIP) e comece 10% abaixo, com cronografo.
    """
    energy_j = BallisticsService.muzzle_energy_joules(
        body.projectile_grains, body.velocity_fps
    )
    est = BallisticsService.estimate_charge_grains(
        body.projectile_grains,
        body.velocity_fps,
        body.calorific_j_per_g,
        body.efficiency_percent,
    )
    return ChargeEstimateOut(
        energy_j=energy_j,
        energy_ftlbs=energy_j * JOULES_TO_FTLBS,
        estimated_charge_grains=est,
    )
