"""Tests for the trajectory calculation service."""

from services.trajectory_service import (
    calculate_trajectory,
    ProjectileData,
    AtmosphericConditions,
    TrajectoryResult,
)


def _make_projectile(**kwargs):
    defaults = dict(
        weight_grains=147.0,
        bc_g1=0.400,
        diameter_mm=7.62,
        muzzle_velocity_fps=2800,
    )
    defaults.update(kwargs)
    return ProjectileData(**defaults)


def test_basic_trajectory():
    proj = _make_projectile()
    result = calculate_trajectory(proj, zero_range_m=100, max_range_m=300, step_m=100)

    assert isinstance(result, TrajectoryResult)
    assert len(result.points) > 0
    assert result.zero_range_m == 100


def test_trajectory_has_drop_at_distance():
    proj = _make_projectile()
    result = calculate_trajectory(proj, zero_range_m=100, max_range_m=300, step_m=100)

    for p in result.points:
        if p.range_m == 100:
            assert abs(p.drop_cm) < 5, "Drop at zero range should be near zero"
        if p.range_m == 300:
            assert p.drop_cm < 0, "Bullet should drop at 300m"


def test_velocity_decreases_with_distance():
    proj = _make_projectile()
    result = calculate_trajectory(proj, zero_range_m=100, max_range_m=500, step_m=100)

    velocities = [p.velocity_fps for p in result.points]
    for i in range(1, len(velocities)):
        assert velocities[i] <= velocities[i - 1], "Velocity should decrease with distance"


def test_energy_decreases_with_distance():
    proj = _make_projectile()
    result = calculate_trajectory(proj, zero_range_m=100, max_range_m=500, step_m=100)

    energies = [p.energy_ftlbs for p in result.points]
    for i in range(1, len(energies)):
        assert energies[i] <= energies[i - 1], "Energy should decrease with distance"


def test_time_of_flight_increases():
    proj = _make_projectile()
    result = calculate_trajectory(proj, zero_range_m=100, max_range_m=500, step_m=100)

    tofs = [p.time_of_flight_s for p in result.points]
    for i in range(1, len(tofs)):
        assert tofs[i] > tofs[i - 1], "Time of flight should increase"


def test_wind_drift_with_crosswind():
    proj = _make_projectile()
    result = calculate_trajectory(
        proj, zero_range_m=100, max_range_m=300, step_m=100,
        wind_speed_ms=5.0, wind_angle_deg=90,
    )

    last_point = result.points[-1]
    assert abs(last_point.wind_drift_cm) > 0, "Should have wind drift with crosswind"


def test_no_wind_drift_without_wind():
    proj = _make_projectile()
    result = calculate_trajectory(
        proj, zero_range_m=100, max_range_m=300, step_m=100,
        wind_speed_ms=0.0,
    )

    for p in result.points:
        assert p.wind_drift_cm == 0.0, "No wind = no drift"


def test_altitude_affects_trajectory():
    proj = _make_projectile()
    result_sea = calculate_trajectory(
        proj, zero_range_m=100, max_range_m=300, step_m=100,
        atmosphere=AtmosphericConditions(altitude_m=0),
    )
    result_high = calculate_trajectory(
        proj, zero_range_m=100, max_range_m=300, step_m=100,
        atmosphere=AtmosphericConditions(altitude_m=3000),
    )

    sea_vel = result_sea.points[-1].velocity_fps
    high_vel = result_high.points[-1].velocity_fps
    assert high_vel > sea_vel, "Higher altitude = less drag = more retained velocity"


def test_heavier_bullet_retains_more_energy():
    light = _make_projectile(weight_grains=110, muzzle_velocity_fps=3100)
    heavy = _make_projectile(weight_grains=180, muzzle_velocity_fps=2600)

    result_light = calculate_trajectory(light, zero_range_m=100, max_range_m=300, step_m=100)
    result_heavy = calculate_trajectory(heavy, zero_range_m=100, max_range_m=300, step_m=100)

    light_energy_300 = result_light.points[-1].energy_ftlbs
    heavy_energy_300 = result_heavy.points[-1].energy_ftlbs

    assert heavy_energy_300 > light_energy_300, "Heavier bullet retains more energy at distance"


def test_mpbr_calculated():
    proj = _make_projectile()
    result = calculate_trajectory(proj, zero_range_m=100, max_range_m=500, step_m=25)
    assert result.max_point_blank_range_m > 0, "MPBR should be calculated"


def test_summary_has_muzzle_data():
    proj = _make_projectile(muzzle_velocity_fps=2800)
    result = calculate_trajectory(proj, zero_range_m=100, max_range_m=200, step_m=100)
    assert "muzzle_velocity_fps" in result.summary
    assert result.summary["muzzle_velocity_fps"] > 0
