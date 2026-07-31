"""Registro das polvoras CBC conforme o Manual de Recarga da fabricante.

A CBC divide seu catalogo em duas series que nao se misturam:

    Serie 100 — "destinam-se, exclusivamente, a recarga de municoes
    destinadas as armas longas raiadas"

    Serie 200 — "destinam-se as municoes de fogo central, tais como
    revolveres e pistolas"

E o manual e categorico sobre trocar uma pela outra:

    "Nunca utilize polvoras indicadas na recarga de municoes para Revolveres
    ou Pistolas na recarga de municoes para Rifles. Esta troca pode resultar
    em incidentes gravissimos."

Este modulo carrega essa tabela para o codigo poder verificar a combinacao
antes de o atirador registrar uma recarga.
"""

from __future__ import annotations

from dataclasses import dataclass

RIFLE = "rifle"
HANDGUN = "curta"

SERIES_100 = 100
SERIES_200 = 200


@dataclass(frozen=True)
class Powder:
    name: str
    series: int
    #  Posicao na escala de vivacidade do manual: 1 e a mais viva (queima mais
    #  rapido) dentro da sua serie. Trocar por uma polvora mais viva mantendo a
    #  mesma carga eleva a pressao de camara.
    burn_rank: int
    grain_format: str
    #  Densidade gravimetrica nominal em g/L, para converter medida de volume
    #  em peso. Faixa do manual; guardamos o ponto medio.
    bulk_density_g_per_l: float

    @property
    def intended_use(self) -> str:
        return RIFLE if self.series == SERIES_100 else HANDGUN


#  Serie 100 — armas longas raiadas. Ordem de vivacidade do manual:
#  129 (mais viva) > 102 > 126 > 128 > 124 (mais lenta).
_SERIES_100 = [
    Powder("CBC 129", SERIES_100, 1, "Tubular Monoperfurado", 890),
    Powder("CBC 102", SERIES_100, 2, "Tubular Monoperfurado", 890),
    Powder("CBC 126", SERIES_100, 3, "Tubular Monoperfurado", 890),
    Powder("CBC 128", SERIES_100, 4, "Tubular Monoperfurado", 900),
    Powder("CBC 124", SERIES_100, 5, "Tubular Monoperfurado", 930),
]

#  Serie 200 — revolveres, pistolas e cartuchos de caca. Ordem de vivacidade
#  do manual: 216 (mais viva) ... 244 (mais lenta).
_SERIES_200 = [
    Powder("CBC 216", SERIES_200, 1, "Disco Poroso", 480),
    Powder("CBC 250", SERIES_200, 2, "Disco Compacto", 400),
    Powder("CBC 212", SERIES_200, 3, "Disco Poroso", 500),
    Powder("CBC 217", SERIES_200, 4, "Disco Poroso", 500),
    Powder("CBC 219", SERIES_200, 5, "Disco Poroso", 500),
    Powder("CBC 218", SERIES_200, 6, "Disco Poroso", 500),
    Powder("CBC 266", SERIES_200, 7, "Disco Poroso", 500),
    Powder("CBC 222", SERIES_200, 8, "Disco Poroso", 500),
    Powder("CBC 246", SERIES_200, 9, "Disco Poroso", 500),
    Powder("CBC 231", SERIES_200, 10, "Disco Compacto", 620),
    Powder("CBC 207", SERIES_200, 11, "Disco Compacto", 620),
    Powder("CBC 236", SERIES_200, 12, "Disco Poroso", 500),
    Powder("CBC 210", SERIES_200, 13, "Disco Compacto", 620),
    Powder("CBC 220", SERIES_200, 14, "Disco Compacto", 620),
    Powder("CBC 244", SERIES_200, 15, "Disco Compacto", 620),
]

POWDERS: dict[str, Powder] = {p.name: p for p in _SERIES_100 + _SERIES_200}


#  Classificacao dos calibres que o catalogo da aplicacao conhece. Serve para
#  decidir qual serie de polvora se aplica; um calibre fora desta lista nao e
#  verificado, porque adivinhar seria pior do que nao opinar.
CARTRIDGE_TYPE: dict[str, str] = {
    ".22-250 REMINGTON": RIFLE,
    ".223 REMINGTON": RIFLE,
    ".243 WINCHESTER": RIFLE,
    ".270 WINCHESTER": RIFLE,
    ".30-06 SPRING.": RIFLE,
    ".30-30 WINCHESTER": RIFLE,
    ".300 WINCHESTER": RIFLE,
    ".308 WINCHESTER": RIFLE,
    ".45-70 GOVERNEMENT": RIFLE,
    ".25 AUTO": HANDGUN,
    ".32 AUTO": HANDGUN,
    ".32 S&W": HANDGUN,
    ".32 S&W CURTO": HANDGUN,
    ".32 S&W L": HANDGUN,
    ".357 MAGNUM": HANDGUN,
    ".38 S&W": HANDGUN,
    ".38 SPL": HANDGUN,
    ".38 SPL CURTO": HANDGUN,
    ".380 AUTO": HANDGUN,
    ".40 S&W": HANDGUN,
    ".44 - 40 WINCHESTER": HANDGUN,
    ".44 REM. MAGNUM": HANDGUN,
    ".44 S&W SPECIAL": HANDGUN,
    ".45 AUTO": HANDGUN,
    ".45 COLT": HANDGUN,
    "9mm Luger": HANDGUN,
}


#  Polvoras que cada fonte indica para cada cartucho.
#
#  CBC = Manual de Recarga da propria fabricante, que descreve para quais
#  calibres cada polvora se destina.
#  MAGNUM = Revista Magnum, Edicao Especial no 44, cujas tabelas trazem cargas
#  efetivamente testadas com pressao medida.
#
#  Uma combinacao ausente das duas nao esta necessariamente errada — nenhuma
#  fonte se declara exaustiva — mas nao tem respaldo publicado, e num catalogo
#  de recarga a procedencia do numero importa tanto quanto o numero.
CBC_MANUAL_INDICATIONS: dict[str, set[str]] = {
    ".25 AUTO": {"CBC 222", "CBC 246"},
    ".32 AUTO": {"CBC 212", "CBC 246"},
    ".32 S&W": {"CBC 212", "CBC 216", "CBC 250"},
    ".32 S&W CURTO": {"CBC 250"},
    ".32 S&W L": {"CBC 216", "CBC 250"},
    ".357 MAGNUM": {"CBC 207", "CBC 220"},
    ".38 S&W": {"CBC 212", "CBC 216"},
    ".38 SPL": {"CBC 207", "CBC 216", "CBC 217", "CBC 219", "CBC 231", "CBC 250"},
    ".38 SPL CURTO": {"CBC 212", "CBC 216", "CBC 250"},
    ".380 AUTO": {"CBC 212", "CBC 217", "CBC 218", "CBC 219", "CBC 266"},
    ".40 S&W": {"CBC 207", "CBC 231", "CBC 246", "CBC 266"},
    ".44 - 40 WINCHESTER": {"CBC 212", "CBC 217", "CBC 219", "CBC 250", "CBC 266"},
    ".44 REM. MAGNUM": {"CBC 244"},
    ".44 S&W SPECIAL": {"CBC 212", "CBC 216", "CBC 250"},
    ".45 AUTO": {"CBC 212", "CBC 217", "CBC 219", "CBC 266"},
    ".45 COLT": {"CBC 212", "CBC 216", "CBC 250"},
    "9mm Luger": {"CBC 207", "CBC 217", "CBC 231", "CBC 246", "CBC 266"},
    ".223 REMINGTON": {"CBC 102"},
    ".22-250 REMINGTON": {"CBC 126"},
    ".243 WINCHESTER": {"CBC 126"},
    ".30-06 SPRING.": {"CBC 126"},
    ".30-30 WINCHESTER": {"CBC 126"},
    ".308 WINCHESTER": {"CBC 102"},
    ".45-70 GOVERNEMENT": {"CBC 129"},
}

MAGNUM_TESTED: dict[str, set[str]] = {
    ".25 AUTO": {"CBC 209", "CBC 216"},
    ".32 AUTO": {"CBC 209", "CBC 216", "CBC 219"},
    ".32 S&W": {"CBC 216"},
    ".32 S&W L": {"CBC 209", "CBC 216", "CBC 219"},
    ".357 MAGNUM": {"CBC 207", "CBC 220"},
    ".38 S&W": {"CBC 216"},
    ".38 SPL": {"CBC 207", "CBC 209", "CBC 216", "CBC 217", "CBC 219"},
    ".380 AUTO": {"CBC 209", "CBC 216", "CBC 219"},
    ".40 S&W": {"CBC 207", "CBC 210", "CBC 217"},
    ".44 REM. MAGNUM": {"CBC 207", "CBC 220"},
    ".44 - 40 WINCHESTER": {"CBC 216", "CBC 217", "CBC 219"},
    ".45 AUTO": {"CBC 209", "CBC 216", "CBC 217", "CBC 219"},
    "9mm Luger": {"CBC 207", "CBC 210", "CBC 216", "CBC 217", "CBC 219"},
    #  Armas longas raiadas. A 126 aparece testada no .223 e no .30-06, o que
    #  o texto da CBC nao deixava claro — ele descreve a 126 com "calibres
    #  como o", enumeracao que nao pretende ser fechada.
    ".22-250 REMINGTON": {"CBC 102"},
    ".223 REMINGTON": {"CBC 102", "CBC 126"},
    ".308 WINCHESTER": {"CBC 102"},
    ".30-06 SPRING.": {"CBC 102", "CBC 126"},
    ".30-30 WINCHESTER": {"CBC 102", "CBC 126"},
}


def referenced_powders(caliber: str | None) -> set[str]:
    """Uniao das polvoras que as fontes publicadas indicam para o cartucho."""
    if not caliber:
        return set()
    key = " ".join(str(caliber).split()).upper()
    found: set[str] = set()
    for table in (CBC_MANUAL_INDICATIONS, MAGNUM_TESTED):
        for known, powders in table.items():
            if known.upper() == key:
                found |= powders
    return found


def check_powder_is_referenced(caliber: str | None, powder: str | None) -> str | None:
    """Avisa quando nenhuma fonte publicada indica a polvora para o cartucho.

    Distinto de check_powder_for_caliber: aquele pega a troca entre series,
    que o fabricante proibe expressamente. Este pega a combinacao que apenas
    nao consta em lugar nenhum — pode ser omissao das fontes, pode ser erro,
    e quem recarrega merece saber a diferenca.

    Devolve None quando o cartucho nao esta mapeado ou a polvora esta fora do
    catalogo CBC, porque ai nao ha o que comparar.
    """
    p = get_powder(powder)
    if p is None:
        return None
    known = referenced_powders(caliber)
    if not known or p.name in known:
        return None

    #  Nem toda ausencia pesa igual. Trocar por uma polvora mais LENTA que as
    #  indicadas erra para o lado seguro, e a propria CBC descreve algumas
    #  polvoras com "calibres como o", redacao que nao pretende ser exaustiva.
    #  Ja uma polvora mais VIVA que qualquer uma das indicadas queima antes de
    #  o projetil sair da frente, e e assim que se estoura uma camara.
    referenced = [POWDERS[n] for n in known if n in POWDERS]
    same_series = [q for q in referenced if q.series == p.series]
    if not same_series:
        return None

    fastest_listed = min(q.burn_rank for q in same_series)
    listed = ", ".join(sorted(known))

    if p.burn_rank < fastest_listed:
        faster_than = min(same_series, key=lambda q: q.burn_rank)
        return (
            f"{p.name} nao consta em nenhuma fonte publicada para {caliber}, e "
            f"queima mais rapido que {faster_than.name}, a mais viva que as "
            f"fontes indicam. Polvora mais viva na mesma carga eleva o pico de "
            f"pressao. Fontes listam: {listed}. Nao use sem confirmar numa "
            "tabela do fabricante."
        )

    return (
        f"{p.name} nao consta nas fontes publicadas para {caliber}, que listam "
        f"{listed}. Queima mais lenta que as indicadas, o que erra para o lado "
        "seguro, mas confirme numa tabela do fabricante."
    )


def get_powder(name: str | None) -> Powder | None:
    """Localiza uma polvora do catalogo CBC, tolerando espacos e caixa."""
    if not name:
        return None
    key = " ".join(str(name).split()).upper()
    for candidate_name, powder in POWDERS.items():
        if candidate_name.upper() == key:
            return powder
    return None


def get_cartridge_type(caliber: str | None) -> str | None:
    if not caliber:
        return None
    key = " ".join(str(caliber).split()).upper()
    for known, kind in CARTRIDGE_TYPE.items():
        if known.upper() == key:
            return kind
    return None


def check_powder_for_caliber(caliber: str | None, powder: str | None) -> str | None:
    """Retorna um aviso se a polvora nao pertencer a serie do cartucho.

    Devolve None quando a combinacao esta correta ou quando nao ha base para
    julgar — polvora fora do catalogo CBC, ou calibre que nao consta na
    classificacao. Silencio aqui significa "sem informacao", nao "aprovado".
    """
    p = get_powder(powder)
    kind = get_cartridge_type(caliber)
    if p is None or kind is None:
        return None
    if p.intended_use == kind:
        return None

    if kind == RIFLE:
        return (
            f"{p.name} e da Serie 200, destinada a revolveres e pistolas, e "
            f"{caliber} e cartucho de arma longa raiada. O Manual de Recarga "
            "da CBC e explicito: nunca use polvora de arma curta em municao "
            "para rifle — a troca pode resultar em incidentes gravissimos."
        )
    return (
        f"{p.name} e da Serie 100, destinada exclusivamente a armas longas "
        f"raiadas, e {caliber} e cartucho de arma curta. Use uma polvora da "
        "Serie 200 para este calibre."
    )


def compare_burn_rate(from_powder: str | None, to_powder: str | None) -> str | None:
    """Avisa quando a substituicao vai para uma polvora mais viva.

    Manter a carga em grains ao trocar por uma polvora de queima mais rapida
    eleva o pico de pressao. Sem base para comparar entre series diferentes,
    caso em que a verificacao de serie e que se aplica.
    """
    a = get_powder(from_powder)
    b = get_powder(to_powder)
    if a is None or b is None or a.series != b.series or a.name == b.name:
        return None
    if b.burn_rank < a.burn_rank:
        return (
            f"{b.name} queima mais rapido que {a.name} na escala de vivacidade "
            "da CBC. Repetir a mesma carga eleva a pressao de camara; refaca o "
            "desenvolvimento a partir da carga minima."
        )
    return None
