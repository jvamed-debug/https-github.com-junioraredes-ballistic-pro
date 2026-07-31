"""Especificacoes dimensionais e de pressao por cartucho.

Fonte: Revista Magnum, Manual de Recarga de Municoes, Edicao Especial no 44
(Sicurezza Editora, dez/2011). Cada cartucho traz a pressao maxima de
trabalho, o comprimento total maximo, o diametro do projetil e o tamanho de
espoleta.

A pressao aparece em C.U.P. e, quando o manual informa, tambem em p.s.i. As
duas escalas medem coisas diferentes e nao se convertem uma na outra: C.U.P.
vem do esmagamento de um cilindro de cobre, p.s.i. de um transdutor
piezoeletrico. Guardamos as duas separadas em vez de escolher uma e fingir
equivalencia.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CartridgeSpec:
    name: str
    max_pressure_cup: int | None
    max_pressure_psi: int | None
    max_oal_mm: float
    primer: str
    bullet_diameter_in: tuple[float, ...]
    #  Limite separado para cargas +P, quando o cartucho admite.
    max_pressure_cup_plus_p: int | None = None
    max_pressure_psi_plus_p: int | None = None

    @property
    def accepts_plus_p(self) -> bool:
        return (
            self.max_pressure_cup_plus_p is not None
            or self.max_pressure_psi_plus_p is not None
        )


SMALL_PISTOL = "Small Pistol"
LARGE_PISTOL = "Large Pistol"


_SPECS = [
    CartridgeSpec(".25 AUTO", 18_000, 25_000, 23.11, SMALL_PISTOL, (0.251,)),
    CartridgeSpec(".32 AUTO", 15_000, 20_500, 24.99, SMALL_PISTOL, (0.309, 0.313)),
    CartridgeSpec(".32 S&W", 12_000, None, 23.62, SMALL_PISTOL, (0.309, 0.312)),
    CartridgeSpec(".32 S&W L", 12_000, 15_000, 32.51, SMALL_PISTOL, (0.309, 0.313)),
    CartridgeSpec(".357 MAGNUM", 45_000, 35_000, 40.39, SMALL_PISTOL, (0.357, 0.358)),
    CartridgeSpec(".38 S&W", 13_000, None, 31.50, SMALL_PISTOL, (0.354, 0.360)),
    CartridgeSpec(
        ".38 SPL", 17_000, None, 39.37, SMALL_PISTOL, (0.357, 0.358),
        max_pressure_cup_plus_p=20_000,
    ),
    CartridgeSpec(".380 AUTO", 17_000, None, 24.99, SMALL_PISTOL, (0.355, 0.356)),
    CartridgeSpec(".40 S&W", 35_700, None, 28.83, SMALL_PISTOL, (0.400, 0.401)),
    CartridgeSpec(".44 REM. MAGNUM", 40_000, None, 40.89, LARGE_PISTOL, (0.429, 0.430)),
    CartridgeSpec(".45 AUTO", 18_000, 22_000, 32.39, LARGE_PISTOL, (0.450, 0.452)),
    CartridgeSpec(
        "9mm Luger", 33_000, 35_000, 29.69, SMALL_PISTOL, (0.355, 0.356),
        max_pressure_psi_plus_p=38_500,
    ),
    CartridgeSpec(
        ".38 SUPER AUTO", 33_000, None, 32.51, SMALL_PISTOL, (0.355, 0.356),
        max_pressure_cup_plus_p=33_000,
    ),
]

SPECS: dict[str, CartridgeSpec] = {s.name: s for s in _SPECS}


def get_spec(caliber: str | None) -> CartridgeSpec | None:
    if not caliber:
        return None
    key = " ".join(str(caliber).split()).upper()
    for name, spec in SPECS.items():
        if name.upper() == key:
            return spec
    return None


def check_overall_length(caliber: str | None, oal_mm: float | None) -> str | None:
    """Avisa quando o cartucho montado passa do comprimento maximo.

    Um cartucho longo demais encosta no inicio do raiamento e o projetil
    comeca a se mover ja engastado, o que eleva a pressao de camara — e em
    pistola tambem impede a alimentacao pelo carregador.
    """
    spec = get_spec(caliber)
    if spec is None or not oal_mm or oal_mm <= 0:
        return None
    if oal_mm <= spec.max_oal_mm:
        return None
    return (
        f"Comprimento total de {oal_mm:.2f} mm passa do maximo de "
        f"{spec.max_oal_mm:.2f} mm para {spec.name}. Cartucho longo demais "
        "encosta no raiamento e eleva a pressao de camara."
    )


def check_primer_size(caliber: str | None, primer: str | None) -> str | None:
    """Confere o tamanho de espoleta contra a tabela do cartucho."""
    spec = get_spec(caliber)
    if spec is None or not primer:
        return None

    text = str(primer).lower()
    mentions_small = "small" in text or "pequen" in text
    mentions_large = "large" in text or "grand" in text
    if not (mentions_small or mentions_large):
        return None

    wanted_small = spec.primer == SMALL_PISTOL
    if wanted_small and mentions_large:
        return f"{spec.name} usa espoleta {SMALL_PISTOL}, nao Large."
    if not wanted_small and mentions_small:
        return f"{spec.name} usa espoleta {LARGE_PISTOL}, nao Small."
    return None
