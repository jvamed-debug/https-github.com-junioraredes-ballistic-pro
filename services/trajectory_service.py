"""Trajectory Service — calculadora balistica externa avancada.

Implementa modelo de arrasto G1/G7 simplificado para calculo de:
- Queda (drop) em funcao da distancia
- Desvio por vento (wind drift)
- Tempo de voo
- Energia remanescente
- Velocidade remanescente
"""

from __future__ import annotations

import bisect
import math
from dataclasses import dataclass, field

#  Coeficiente de arrasto do projetil padrao G1 (base plana, ogiva curta) em
#  funcao do numero de Mach. Referencia classica de balistica externa.
_G1_MACH = [
    0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55,
    0.60, 0.70, 0.725, 0.75, 0.775, 0.80, 0.825, 0.85, 0.875, 0.90, 0.925,
    0.95, 0.975, 1.00, 1.025, 1.05, 1.075, 1.10, 1.125, 1.15, 1.20, 1.25,
    1.30, 1.35, 1.40, 1.50, 1.60, 1.80, 2.00, 2.20, 2.50, 3.00, 3.50, 4.00,
]
_G1_CD = [
    0.2629, 0.2558, 0.2487, 0.2413, 0.2344, 0.2278, 0.2214, 0.2155, 0.2104,
    0.2061, 0.2032, 0.2020, 0.2034, 0.2165, 0.2230, 0.2313, 0.2417, 0.2546,
    0.2706, 0.2901, 0.3136, 0.3415, 0.3734, 0.4084, 0.4448, 0.4805, 0.5136,
    0.5427, 0.5677, 0.5883, 0.6053, 0.6191, 0.6393, 0.6518, 0.6589, 0.6621,
    0.6625, 0.6573, 0.6483, 0.6245, 0.5996, 0.5759, 0.5419, 0.4957, 0.4595,
    0.4306,
]

#  Projetil padrao G7 (boat-tail, ogiva longa) — descreve muito melhor
#  projeteis modernos de precisao.
_G7_MACH = [
    0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55,
    0.60, 0.65, 0.70, 0.725, 0.75, 0.775, 0.80, 0.825, 0.85, 0.875, 0.90,
    0.925, 0.95, 0.975, 1.00, 1.025, 1.05, 1.075, 1.10, 1.125, 1.15, 1.20,
    1.25, 1.30, 1.35, 1.40, 1.50, 1.60, 1.80, 2.00, 2.20, 2.50, 3.00, 3.50,
    4.00,
]
_G7_CD = [
    0.1198, 0.1197, 0.1196, 0.1194, 0.1193, 0.1194, 0.1194, 0.1194, 0.1193,
    0.1193, 0.1194, 0.1193, 0.1194, 0.1197, 0.1202, 0.1207, 0.1215, 0.1226,
    0.1242, 0.1266, 0.1306, 0.1368, 0.1464, 0.1660, 0.2054, 0.2993, 0.3803,
    0.4015, 0.4043, 0.4034, 0.4014, 0.3987, 0.3955, 0.3884, 0.3810, 0.3732,
    0.3657, 0.3580, 0.3440, 0.3315, 0.3097, 0.2917, 0.2751, 0.2531, 0.2251,
    0.2050, 0.1892,
]

#  Fecha a conversao entre o BC (lb/in2) e as unidades SI do resto da conta.
#  Vem de (pi/4) x (lb/in2 -> kg/m2): e nele que a densidade seccional do
#  projetil se cancela contra a que ja esta embutida no BC.
_BC_TO_SI = 5.5851e-4


def _interpolate(mach: float, machs: list[float], cds: list[float]) -> float:
    if mach <= machs[0]:
        return cds[0]
    if mach >= machs[-1]:
        return cds[-1]
    i = bisect.bisect_left(machs, mach)
    m0, m1 = machs[i - 1], machs[i]
    c0, c1 = cds[i - 1], cds[i]
    return c0 + (c1 - c0) * (mach - m0) / (m1 - m0)


def drag_coefficient_g1(mach: float) -> float:
    return _interpolate(mach, _G1_MACH, _G1_CD)


def drag_coefficient_g7(mach: float) -> float:
    return _interpolate(mach, _G7_MACH, _G7_CD)


def speed_of_sound_ms(temperature_c: float) -> float:
    return 331.3 * math.sqrt(1 + temperature_c / 273.15)


@dataclass
class AtmosphericConditions:
    """Condicoes do ar no local do disparo.

    `pressure_hpa` e a pressao reduzida ao nivel do mar (QNH) — o valor que
    apps de meteorologia informam. A queda real de pressao ate a altitude do
    atirador vem de `altitude_m`; informar aqui a pressao ja medida na
    estacao contaria a altitude duas vezes.
    """

    temperature_c: float = 15.0
    pressure_hpa: float = 1013.25
    humidity_pct: float = 50.0
    altitude_m: float = 0.0

    # Constantes dos gases para ar seco e para vapor d'agua (J/(kg*K)).
    _R_DRY = 287.058
    _R_VAPOUR = 461.495

    @property
    def saturation_vapour_pressure_hpa(self) -> float:
        """Pressao de vapor de saturacao pela equacao de Tetens."""
        t = self.temperature_c
        return 6.1078 * 10 ** (7.5 * t / (t + 237.3))

    @property
    def air_density(self) -> float:
        """Densidade do ar em kg/m3.

        Vapor d'agua e mais leve que o ar seco, entao ar umido e menos denso e
        oferece menos arrasto. O termo de umidade responde por cerca de 1% em
        dia quente e saturado — pequeno, mas era simplesmente ignorado antes,
        e o campo aparece na interface como se tivesse efeito.
        """
        t_k = self.temperature_c + 273.15
        altitude_factor = math.exp(-self.altitude_m / 8500)

        # Pressao no local, a partir da QNH corrigida pela altitude.
        station_hpa = self.pressure_hpa * altitude_factor
        vapour_hpa = (self.humidity_pct / 100) * self.saturation_vapour_pressure_hpa
        vapour_hpa = min(vapour_hpa, station_hpa)
        dry_hpa = station_hpa - vapour_hpa

        return (dry_hpa * 100) / (self._R_DRY * t_k) + (vapour_hpa * 100) / (
            self._R_VAPOUR * t_k
        )


@dataclass
class ProjectileData:
    weight_grains: float
    bc_g1: float = 0.0
    bc_g7: float = 0.0
    diameter_mm: float = 0.0
    muzzle_velocity_fps: float = 0.0

    @property
    def weight_kg(self) -> float:
        return self.weight_grains * 0.0000647989

    @property
    def muzzle_velocity_ms(self) -> float:
        return self.muzzle_velocity_fps * 0.3048

    @property
    def bc_effective(self) -> float:
        return self.bc_g7 if self.bc_g7 > 0 else self.bc_g1

    @property
    def drag_model(self) -> str:
        """Um BC so vale com a curva de arrasto a que foi medido."""
        return "G7" if self.bc_g7 > 0 else "G1"


@dataclass
class TrajectoryPoint:
    range_m: float
    drop_cm: float
    drop_moa: float
    drop_mil: float
    velocity_ms: float
    velocity_fps: float
    energy_j: float
    energy_ftlbs: float
    time_of_flight_s: float
    wind_drift_cm: float = 0.0
    wind_drift_moa: float = 0.0


@dataclass
class TrajectoryResult:
    points: list[TrajectoryPoint] = field(default_factory=list)
    zero_range_m: float = 0.0
    max_point_blank_range_m: float = 0.0
    summary: dict = field(default_factory=dict)


def calculate_trajectory(
    projectile: ProjectileData,
    zero_range_m: float = 100.0,
    max_range_m: float = 500.0,
    step_m: float = 25.0,
    sight_height_cm: float = 4.0,
    wind_speed_ms: float = 0.0,
    wind_angle_deg: float = 90.0,
    atmosphere: AtmosphericConditions | None = None,
) -> TrajectoryResult:
    if atmosphere is None:
        atmosphere = AtmosphericConditions()

    bc = projectile.bc_effective
    if bc <= 0:
        bc = 0.400

    v0 = projectile.muzzle_velocity_ms
    m = projectile.weight_kg
    rho = atmosphere.air_density

    g = 9.80665
    dt = 0.0001
    sight_height_m = sight_height_cm / 100

    wind_cross = wind_speed_ms * math.sin(math.radians(wind_angle_deg))

    sound_ms = speed_of_sound_ms(atmosphere.temperature_c)
    cd_of = drag_coefficient_g7 if projectile.drag_model == "G7" else drag_coefficient_g1

    #  Desaceleracao por arrasto: a = retard * v^2.
    #
    #  O BC ja carrega a densidade seccional do projetil (BC = SD / fator de
    #  forma), entao ela nao pode entrar de novo por area e massa. A versao
    #  anterior fazia as duas coisas, o que penalizava projetil leve na
    #  proporcao de 1/SD: o .308 168gr saia certo enquanto o .223 55gr perdia
    #  44% da velocidade a 300m contra o dado publicado. Com area e massa fora
    #  da conta, os dois termos de SD se cancelam e sobra so o BC.
    def retardation(v: float) -> float:
        return _BC_TO_SI * rho * cd_of(v / sound_ms) / bc

    # First pass: find angle for zero
    def simulate(launch_angle: float, collect_range: float = max_range_m) -> list[TrajectoryPoint]:
        x, y = 0.0, -sight_height_m
        vx = v0 * math.cos(launch_angle)
        vy = v0 * math.sin(launch_angle)
        t = 0.0
        drift_x = 0.0

        points = []
        next_range = step_m

        while x <= collect_range + step_m:
            v = math.sqrt(vx ** 2 + vy ** 2)
            if v < 10:
                break

            retard = retardation(v)

            ax = -retard * vx * v
            ay = -g - retard * vy * v

            vx += ax * dt
            vy += ay * dt
            x += vx * dt
            y += vy * dt
            t += dt

            if wind_cross != 0:
                drift_x += wind_cross * dt * (1 - v / v0) * 0.5

            if x >= next_range:
                drop_cm_val = y * 100
                range_m = next_range

                if range_m > 0:
                    drop_moa = (drop_cm_val / range_m) * 34.377
                    drop_mil = (drop_cm_val / range_m) * 10.0
                else:
                    drop_moa = 0.0
                    drop_mil = 0.0

                vel_fps = v / 0.3048
                energy_j_val = 0.5 * m * v ** 2
                energy_ftlbs = energy_j_val * 0.737562

                drift_cm = drift_x * 100
                drift_moa = (drift_cm / range_m) * 34.377 if range_m > 0 else 0

                points.append(TrajectoryPoint(
                    range_m=range_m,
                    drop_cm=round(drop_cm_val, 1),
                    drop_moa=round(drop_moa, 2),
                    drop_mil=round(drop_mil, 2),
                    velocity_ms=round(v, 1),
                    velocity_fps=round(vel_fps, 0),
                    energy_j=round(energy_j_val, 0),
                    energy_ftlbs=round(energy_ftlbs, 0),
                    time_of_flight_s=round(t, 3),
                    wind_drift_cm=round(drift_cm, 1),
                    wind_drift_moa=round(drift_moa, 2),
                ))
                next_range += step_m

        return points

    # Binary search for zero angle
    low, high = -0.01, 0.05
    for _ in range(50):
        mid = (low + high) / 2
        pts = simulate(mid, zero_range_m + step_m)
        zero_pt = None
        for p in pts:
            if abs(p.range_m - zero_range_m) < step_m / 2:
                zero_pt = p
                break
        if zero_pt is None:
            break
        if zero_pt.drop_cm > 0:
            high = mid
        else:
            low = mid

    launch_angle = (low + high) / 2
    points = simulate(launch_angle)

    mpbr = 0.0
    for p in points:
        if abs(p.drop_cm) <= 8.0:
            mpbr = p.range_m

    summary = {}
    if points:
        summary["muzzle_velocity_fps"] = round(v0 / 0.3048, 0)
        summary["muzzle_energy_ftlbs"] = round(0.5 * m * v0 ** 2 * 0.737562, 0)
        for p in points:
            if p.range_m == 100:
                summary["vel_100m"] = p.velocity_fps
                summary["energy_100m"] = p.energy_ftlbs
            if p.range_m == 200:
                summary["vel_200m"] = p.velocity_fps
                summary["energy_200m"] = p.energy_ftlbs
            if p.range_m == 300:
                summary["vel_300m"] = p.velocity_fps
                summary["energy_300m"] = p.energy_ftlbs

    return TrajectoryResult(
        points=points,
        zero_range_m=zero_range_m,
        max_point_blank_range_m=mpbr,
        summary=summary,
    )
