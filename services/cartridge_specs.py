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
    #  Restricao de uso que o manual faz questao de destacar.
    usage_warning: str | None = None

    @property
    def accepts_plus_p(self) -> bool:
        return (
            self.max_pressure_cup_plus_p is not None
            or self.max_pressure_psi_plus_p is not None
        )


SMALL_PISTOL = "Small Pistol"
LARGE_PISTOL = "Large Pistol"
SMALL_PISTOL_MAGNUM = "Small Pistol Magnum"
SMALL_RIFLE = "Small Rifle"
LARGE_RIFLE = "Large Rifle"


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

    #  Armas longas raiadas.
    CartridgeSpec(".22-250 REMINGTON", 53_000, 65_000, 59.69, LARGE_RIFLE, (0.223, 0.224)),
    CartridgeSpec(
        ".223 REMINGTON", 52_000, 55_000, 57.40, SMALL_RIFLE, (0.223, 0.224),
        usage_warning="Nao use municao militar 5,56x45 em arma civil.",
    ),
    CartridgeSpec(
        ".308 WINCHESTER", 52_000, 62_000, 71.12, LARGE_RIFLE, (0.308,),
        usage_warning="Nao use municao militar 7,62x51 em arma civil.",
    ),
    CartridgeSpec(".30-06 SPRING.", 50_000, 60_000, 84.84, LARGE_RIFLE, (0.308,)),
    CartridgeSpec(".30-30 WINCHESTER", 38_000, 42_000, 64.77, LARGE_RIFLE, (0.308,)),
    CartridgeSpec("7X57 MAUSER", 46_000, 51_000, 77.85, LARGE_RIFLE, (0.284,)),
    CartridgeSpec("7MM-08 REMINGTON", 52_000, 61_000, 71.12, LARGE_RIFLE, (0.284,)),
    CartridgeSpec("7-30 WATERS", 40_000, 45_000, 64.77, LARGE_RIFLE, (0.284,)),
    CartridgeSpec("6,5X55 MAUSER", 46_200, None, 80.00, LARGE_RIFLE, (0.264,)),
    CartridgeSpec("30 M1 CARABINA", 40_000, None, 42.67, SMALL_RIFLE, (0.308,)),

    #  Cartuchos de estojo reto usados em carabina de alavanca. Espoleta de
    #  pistola apesar da arma longa, e limites de pressao baixos: sao projetos
    #  do fim do seculo XIX.
    CartridgeSpec(".32-20 WINCHESTER", 16_000, None, 40.39, SMALL_PISTOL, (0.312, 0.313)),
    CartridgeSpec(".38-40 WINCHESTER", 14_000, None, 40.44, LARGE_PISTOL, (0.400,)),
    CartridgeSpec(
        ".44 - 40 WINCHESTER", 13_000, None, 40.44, LARGE_PISTOL, (0.427, 0.430),
        usage_warning=(
            "As cargas publicadas pela Revista Magnum para este calibre sao "
            "exclusivas de carabina Winchester 1892 em perfeito estado ou Puma "
            "065, que suportam pressao maior que o limite SAAMI. O manual e "
            "explicito: NAO USE ESTAS CARGAS EM REVOLVERES."
        ),
    ),
    CartridgeSpec(
        ".357 MAXIMUM", 51_500, None, 50.55, SMALL_PISTOL_MAGNUM, (0.357,),
        usage_warning=(
            "As cargas publicadas sao para Thompson/Contender ou arma longa "
            "adaptada, nao para os revolveres existentes neste calibre."
        ),
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

    wanted_small = spec.primer.startswith("Small")
    if wanted_small and mentions_large:
        return f"{spec.name} usa espoleta {spec.primer}, nao Large."
    if not wanted_small and mentions_small:
        return f"{spec.name} usa espoleta {spec.primer}, nao Small."

    #  Espoleta de pistola e de rifle nao sao intercambiaveis: a de rifle tem
    #  copo mais espesso e mistura mais energetica.
    mentions_rifle = "rifle" in text
    mentions_pistol = "pistol" in text
    wanted_rifle = "Rifle" in spec.primer
    if wanted_rifle and mentions_pistol:
        return f"{spec.name} usa espoleta {spec.primer}, nao de pistola."
    if not wanted_rifle and mentions_rifle:
        return f"{spec.name} usa espoleta {spec.primer}, nao de rifle."
    return None


def get_usage_warning(caliber: str | None) -> str | None:
    """Restricao de uso que o manual destaca para o cartucho."""
    spec = get_spec(caliber)
    return spec.usage_warning if spec else None
