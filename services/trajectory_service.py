"""Trajectory Service — calculadora balistica externa avancada.

Implementa modelo de arrasto G1/G7 simplificado para calculo de:
- Queda (drop) em funcao da distancia
- Desvio por vento (wind drift)
- Tempo de voo
- Energia remanescente
- Velocidade remanescente
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass
class AtmosphericConditions:
    temperature_c: float = 15.0
    pressure_hpa: float = 1013.25
    humidity_pct: float = 50.0
    altitude_m: float = 0.0

    @property
    def air_density(self) -> float:
        t_k = self.temperature_c + 273.15
        p_pa = self.pressure_hpa * 100
        r = 287.058
        rho = p_pa / (r * t_k)
        alt_factor = math.exp(-self.altitude_m / 8500)
        return rho * alt_factor


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
    d = projectile.diameter_mm / 1000 if projectile.diameter_mm > 0 else 0.00762
    area = math.pi * (d / 2) ** 2

    g = 9.80665
    dt = 0.0001
    sight_height_m = sight_height_cm / 100

    wind_cross = wind_speed_ms * math.sin(math.radians(wind_angle_deg))

    def drag_coeff(v: float) -> float:
        mach = v / 343.0
        if mach < 0.8:
            return 0.12
        elif mach < 1.0:
            return 0.12 + (mach - 0.8) * 2.0
        elif mach < 1.2:
            return 0.52 - (mach - 1.0) * 1.0
        else:
            return 0.32 / mach

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

            cd = drag_coeff(v)
            retard = (rho * area * cd) / (2 * bc * m)

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
