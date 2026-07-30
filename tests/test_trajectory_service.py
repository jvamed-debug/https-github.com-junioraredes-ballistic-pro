"""Tests for services.trajectory_service — ballistic trajectory calculations."""

import math

import pytest

from services.trajectory_service import (
    AtmosphericConditions,
    ProjectileData,
    TrajectoryPoint,
    TrajectoryResult,
    calculate_trajectory,
)


class TestAtmosphericConditions:
    def test_default_air_density(self):
        atm = AtmosphericConditions()
        rho = atm.air_density
        assert 1.1 < rho < 1.3  # ~1.225 kg/m³ at sea level

    def test_altitude_reduces_density(self):
        sea_level = AtmosphericConditions(altitude_m=0).air_density
        high_alt = AtmosphericConditions(altitude_m=2000).air_density
        assert high_alt < sea_level

    def test_higher_temperature_reduces_density(self):
        cold = AtmosphericConditions(temperature_c=0).air_density
        hot = AtmosphericConditions(temperature_c=40).air_density
        assert hot < cold

    def test_higher_pressure_increases_density(self):
        low_p = AtmosphericConditions(pressure_hpa=980).air_density
        high_p = AtmosphericConditions(pressure_hpa=1040).air_density
        assert high_p > low_p


class TestProjectileData:
    def test_weight_conversion(self):
        proj = ProjectileData(weight_grains=150)
        assert abs(proj.weight_kg - 150 * 0.0000647989) < 1e-9

    def test_velocity_conversion(self):
        proj = ProjectileData(weight_grains=150, muzzle_velocity_fps=2800)
        assert abs(proj.muzzle_velocity_ms - 2800 * 0.3048) < 0.01

    def test_bc_effective_prefers_g7(self):
        proj = ProjectileData(weight_grains=150, bc_g1=0.450, bc_g7=0.230)
        assert proj.bc_effective == 0.230

    def test_bc_effective_falls_back_to_g1(self):
        proj = ProjectileData(weight_grains=150, bc_g1=0.450)
        assert proj.bc_effective == 0.450


class TestCalculateTrajectory:
    def _make_projectile(self, **kwargs):
        defaults = dict(
            weight_grains=168,
            bc_g1=0.462,
            diameter_mm=7.62,
            muzzle_velocity_fps=2700,
        )
        defaults.update(kwargs)
        return ProjectileData(**defaults)

    def test_returns_trajectory_result(self):
        result = calculate_trajectory(self._make_projectile())
        assert isinstance(result, TrajectoryResult)
        assert len(result.points) > 0

    def test_points_cover_requested_range(self):
        result = calculate_trajectory(self._make_projectile(), max_range_m=300, step_m=50)
        ranges = [p.range_m for p in result.points]
        assert 50 in ranges
        assert 100 in ranges
        assert 300 in ranges

    def test_velocity_decreases_with_distance(self):
        result = calculate_trajectory(self._make_projectile(), max_range_m=300, step_m=100)
        velocities = [p.velocity_ms for p in result.points]
        for i in range(1, len(velocities)):
            assert velocities[i] < velocities[i - 1]

    def test_energy_decreases_with_distance(self):
        result = calculate_trajectory(self._make_projectile(), max_range_m=300, step_m=100)
        energies = [p.energy_j for p in result.points]
        for i in range(1, len(energies)):
            assert energies[i] < energies[i - 1]

    def test_zero_range_has_minimal_drop(self):
        result = calculate_trajectory(self._make_projectile(), zero_range_m=100, step_m=25)
        zero_point = next((p for p in result.points if p.range_m == 100), None)
        assert zero_point is not None
        assert abs(zero_point.drop_cm) < 2.0  # should be near zero at zero range

    def test_drop_increases_beyond_zero(self):
        result = calculate_trajectory(
            self._make_projectile(), zero_range_m=100, max_range_m=400, step_m=100
        )
        pts_beyond = [p for p in result.points if p.range_m > 100]
        assert len(pts_beyond) >= 2
        assert pts_beyond[-1].drop_cm < pts_beyond[0].drop_cm  # increasingly negative

    def test_wind_drift_present_with_crosswind(self):
        result = calculate_trajectory(
            self._make_projectile(), max_range_m=300, step_m=100,
            wind_speed_ms=5.0, wind_angle_deg=90.0,
        )
        last = result.points[-1]
        assert abs(last.wind_drift_cm) > 0

    def test_no_wind_drift_without_wind(self):
        result = calculate_trajectory(
            self._make_projectile(), max_range_m=300, step_m=100,
            wind_speed_ms=0.0,
        )
        for p in result.points:
            assert p.wind_drift_cm == 0.0

    def test_time_of_flight_increases(self):
        result = calculate_trajectory(self._make_projectile(), max_range_m=300, step_m=100)
        times = [p.time_of_flight_s for p in result.points]
        for i in range(1, len(times)):
            assert times[i] > times[i - 1]

    def test_zero_bc_uses_default(self):
        proj = ProjectileData(weight_grains=150, bc_g1=0.0, muzzle_velocity_fps=2500)
        result = calculate_trajectory(proj, max_range_m=200, step_m=100)
        assert len(result.points) > 0

    def test_summary_keys(self):
        result = calculate_trajectory(self._make_projectile(), max_range_m=300, step_m=100)
        assert "muzzle_velocity_fps" in result.summary
        assert "muzzle_energy_ftlbs" in result.summary

    def test_mpbr_calculated(self):
        result = calculate_trajectory(self._make_projectile(), max_range_m=500, step_m=25)
        assert result.max_point_blank_range_m >= 0

    def test_custom_atmosphere(self):
        hot_high = AtmosphericConditions(temperature_c=35, altitude_m=1500)
        result = calculate_trajectory(
            self._make_projectile(), max_range_m=200, step_m=100, atmosphere=hot_high
        )
        assert len(result.points) > 0


class TestHumidity:
    """Humid air is less dense than dry air, so it slows the bullet less.
    The field was on screen but ignored by the density calculation."""

    def test_humidity_lowers_air_density(self):
        dry = AtmosphericConditions(temperature_c=30, humidity_pct=0).air_density
        wet = AtmosphericConditions(temperature_c=30, humidity_pct=100).air_density
        assert wet < dry

    def test_humidity_effect_is_about_one_percent_when_hot_and_saturated(self):
        dry = AtmosphericConditions(temperature_c=30, humidity_pct=0).air_density
        wet = AtmosphericConditions(temperature_c=30, humidity_pct=100).air_density
        assert 0.010 < (dry - wet) / dry < 0.025

    def test_humidity_barely_matters_when_cold(self):
        """Cold air holds little vapour, so the correction nearly vanishes."""
        dry = AtmosphericConditions(temperature_c=-10, humidity_pct=0).air_density
        wet = AtmosphericConditions(temperature_c=-10, humidity_pct=100).air_density
        assert (dry - wet) / dry < 0.002

    def test_dry_sea_level_matches_the_standard_atmosphere(self):
        rho = AtmosphericConditions(
            temperature_c=15, pressure_hpa=1013.25, humidity_pct=0, altitude_m=0
        ).air_density
        assert rho == pytest.approx(1.2250, rel=0.001)

    def test_saturation_pressure_matches_published_values(self):
        """Tetens: 12.3 hPa at 10C, 42.4 hPa at 30C."""
        assert AtmosphericConditions(temperature_c=10).saturation_vapour_pressure_hpa == pytest.approx(12.28, rel=0.01)
        assert AtmosphericConditions(temperature_c=30).saturation_vapour_pressure_hpa == pytest.approx(42.43, rel=0.01)

    def test_vapour_pressure_never_exceeds_station_pressure(self):
        """Guards the dry term against going negative in absurd input."""
        rho = AtmosphericConditions(
            temperature_c=60, pressure_hpa=800, humidity_pct=100, altitude_m=5000
        ).air_density
        assert rho > 0


class TestAltitudeIsSeaLevelReferenced:
    def test_altitude_thins_the_air(self):
        low = AtmosphericConditions(altitude_m=0).air_density
        high = AtmosphericConditions(altitude_m=2000).air_density
        assert high < low

    def test_matches_standard_atmosphere_at_altitude(self):
        """ISA at 2000m is 2C and 1.0066 kg/m3. Pressure is given as the
        sea-level (QNH) figure a weather app reports, which is what the
        altitude term then corrects down."""
        rho = AtmosphericConditions(
            temperature_c=2, pressure_hpa=1013.25, humidity_pct=0, altitude_m=2000
        ).air_density
        assert rho == pytest.approx(1.0066, rel=0.01)

    def test_thinner_air_flattens_the_trajectory(self):
        proj = ProjectileData(weight_grains=168, bc_g1=0.462, diameter_mm=7.82, muzzle_velocity_fps=2650)
        sea = calculate_trajectory(proj, max_range_m=300, step_m=100,
                                   atmosphere=AtmosphericConditions(altitude_m=0))
        mountain = calculate_trajectory(proj, max_range_m=300, step_m=100,
                                        atmosphere=AtmosphericConditions(altitude_m=2500))
        assert mountain.points[-1].drop_cm > sea.points[-1].drop_cm
        assert mountain.points[-1].velocity_fps > sea.points[-1].velocity_fps
