"""Tests for services.trajectory_service — ballistic trajectory calculations."""

import math

import pytest

from services.trajectory_service import (
    AtmosphericConditions,
    ProjectileData,
    TrajectoryPoint,
    TrajectoryResult,
    drag_coefficient_g1,
    drag_coefficient_g7,
    speed_of_sound_ms,
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


class TestDragCurves:
    def test_g1_matches_the_standard_table_at_key_machs(self):
        assert drag_coefficient_g1(0.50) == pytest.approx(0.2032, abs=1e-4)
        assert drag_coefficient_g1(1.00) == pytest.approx(0.4805, abs=1e-4)
        assert drag_coefficient_g1(1.40) == pytest.approx(0.6625, abs=1e-4)
        assert drag_coefficient_g1(3.00) == pytest.approx(0.4957, abs=1e-4)

    def test_g7_matches_the_standard_table_at_key_machs(self):
        assert drag_coefficient_g7(0.50) == pytest.approx(0.1194, abs=1e-4)
        assert drag_coefficient_g7(1.05) == pytest.approx(0.4043, abs=1e-4)
        assert drag_coefficient_g7(2.00) == pytest.approx(0.2917, abs=1e-4)

    def test_curves_interpolate_between_table_points(self):
        mid = drag_coefficient_g1(0.5250)
        assert 0.2020 < mid < 0.2032

    def test_curves_clamp_outside_the_table(self):
        assert drag_coefficient_g1(-1.0) == drag_coefficient_g1(0.0)
        assert drag_coefficient_g1(99.0) == drag_coefficient_g1(4.0)

    def test_drag_peaks_around_the_transonic_barrier(self):
        """Both curves rise steeply through Mach 1 — the reason subsonic
        transition upsets a bullet."""
        assert drag_coefficient_g1(1.4) > drag_coefficient_g1(0.5) * 3
        assert drag_coefficient_g7(1.05) > drag_coefficient_g7(0.5) * 3

    def test_speed_of_sound_tracks_temperature(self):
        assert speed_of_sound_ms(15) == pytest.approx(340.3, rel=0.005)
        assert speed_of_sound_ms(0) == pytest.approx(331.3, rel=0.005)
        assert speed_of_sound_ms(35) > speed_of_sound_ms(-5)

    def test_g7_bc_selects_the_g7_curve(self):
        assert ProjectileData(weight_grains=168, bc_g1=0.462).drag_model == "G1"
        assert ProjectileData(weight_grains=168, bc_g7=0.224).drag_model == "G7"


class TestAgainstPublishedData:
    """Remaining velocity against published tables.

    The drag term used to divide by BC *and* apply the projectile's own area
    and mass. BC already carries sectional density, so counting it twice
    penalised light bullets by 1/SD: the .308 came out right while the .223
    lost 44% of its velocity by 300m. With area and mass gone the two SD
    terms cancel and only BC remains.
    """

    def _velocities(self, bc, mv_fps, distances):
        proj = ProjectileData(
            weight_grains=100, bc_g1=bc, diameter_mm=7.0, muzzle_velocity_fps=mv_fps
        )
        result = calculate_trajectory(
            proj, zero_range_m=100, max_range_m=max(distances), step_m=min(distances)
        )
        return {p.range_m: p.velocity_fps for p in result.points}

    def test_308_168gr(self):
        v = self._velocities(0.462, 2650, [100, 200, 300])
        assert v[100] == pytest.approx(2440, rel=0.03)
        assert v[200] == pytest.approx(2240, rel=0.03)
        assert v[300] == pytest.approx(2040, rel=0.03)

    def test_3006_180gr(self):
        v = self._velocities(0.480, 2700, [100, 200, 300])
        assert v[300] == pytest.approx(2120, rel=0.03)

    def test_223_55gr_light_low_bc(self):
        """The case the old model got worst. Held to 15% because a G1 BC
        understates a spitzer's real supersonic performance — the residual is
        the drag model's shape mismatch, not the arithmetic."""
        v = self._velocities(0.243, 3240, [100, 200, 300])
        assert v[100] == pytest.approx(2900, rel=0.06)
        assert v[300] == pytest.approx(2300, rel=0.15)

    def test_9mm_115gr_subsonic_pistol(self):
        v = self._velocities(0.140, 1180, [50, 100])
        assert v[50] == pytest.approx(1110, rel=0.10)
        assert v[100] == pytest.approx(1050, rel=0.10)

    def test_no_caliber_is_off_by_more_than_the_old_worst_case(self):
        """The old model peaked at 44% error. Nothing may regress past 15%."""
        cases = [
            (0.462, 2650, {100: 2440, 200: 2240, 300: 2040}),
            (0.243, 3240, {100: 2900, 200: 2590, 300: 2300}),
            (0.480, 2700, {100: 2500, 200: 2310, 300: 2120}),
            (0.400, 2960, {100: 2740, 200: 2530, 300: 2330}),
            (0.243, 3680, {100: 3310, 200: 2960, 300: 2640}),
        ]
        for bc, mv, expected in cases:
            got = self._velocities(bc, mv, list(expected))
            for dist, want in expected.items():
                error = abs(got[dist] - want) / want
                assert error < 0.15, f"BC {bc} @ {dist}m: {error:.1%}"

    def test_g1_and_g7_agree_when_given_equivalent_bcs(self):
        """A G7 BC of 0.224 is the published equivalent of G1 0.462 for a
        .308 168gr. Two independent curves must reach the same answer."""
        g1 = ProjectileData(weight_grains=168, bc_g1=0.462, diameter_mm=7.82, muzzle_velocity_fps=2650)
        g7 = ProjectileData(weight_grains=168, bc_g7=0.224, diameter_mm=7.82, muzzle_velocity_fps=2650)
        r1 = calculate_trajectory(g1, max_range_m=300, step_m=100)
        r7 = calculate_trajectory(g7, max_range_m=300, step_m=100)
        assert r7.points[-1].velocity_fps == pytest.approx(r1.points[-1].velocity_fps, rel=0.02)
        assert r7.points[-1].drop_cm == pytest.approx(r1.points[-1].drop_cm, rel=0.03)

    def test_drop_matches_published_figures(self):
        proj = ProjectileData(weight_grains=168, bc_g1=0.462, diameter_mm=7.82, muzzle_velocity_fps=2650)
        r = calculate_trajectory(proj, zero_range_m=100, max_range_m=400, step_m=100)
        drops = {p.range_m: p.drop_cm for p in r.points}
        assert drops[200] == pytest.approx(-13.5, abs=2.0)
        assert drops[300] == pytest.approx(-49.0, abs=4.0)
        assert drops[400] == pytest.approx(-109.0, abs=8.0)


class TestWindDrift:
    """Drift used to accumulate `wind * dt * (1 - v/v0) * 0.5`. The 0.5 was a
    fudge with nothing behind it, and it left drift about 43% short of
    published tables — the dangerous direction, since a shooter who trusts the
    figure holds too little wind and misses.

    Drag now acts on velocity relative to the moving air mass, which produces
    the lag that causes drift without any correction factor.
    """

    MPH_10 = 4.4704

    def _proj(self):
        return ProjectileData(
            weight_grains=168, bc_g1=0.462, diameter_mm=7.82, muzzle_velocity_fps=2650
        )

    def _drift_at(self, distance, wind_ms, angle_deg=90.0):
        r = calculate_trajectory(
            self._proj(), zero_range_m=100, max_range_m=distance, step_m=100,
            wind_speed_ms=wind_ms, wind_angle_deg=angle_deg,
        )
        return next(p for p in r.points if p.range_m == distance).wind_drift_cm

    def test_matches_published_tables_within_a_fifth(self):
        """Published .308 168gr figures for a 10 mph full-value crosswind.
        The point-mass response runs about 15% high — a known trait of the
        model, and far better than the 43% shortfall it replaces."""
        for distance, published in ((100, 2.0), (200, 8.6), (300, 20.3), (400, 38.6)):
            got = self._drift_at(distance, self.MPH_10)
            assert got == pytest.approx(published, rel=0.20), f"{distance}m"

    def test_drift_is_never_short_of_published(self):
        """Erring high costs a hit; erring low is the one that surprises."""
        for distance, published in ((200, 8.6), (300, 20.3), (400, 38.6)):
            assert self._drift_at(distance, self.MPH_10) >= published

    def test_head_and_tail_wind_cause_no_lateral_drift(self):
        assert self._drift_at(300, self.MPH_10, angle_deg=0.0) == pytest.approx(0.0, abs=0.05)
        assert self._drift_at(300, self.MPH_10, angle_deg=180.0) == pytest.approx(0.0, abs=0.05)

    def test_oblique_wind_follows_the_cosine(self):
        """A 45 degree wind is a 0.707 value wind, not a half value one."""
        full = self._drift_at(300, self.MPH_10, angle_deg=90.0)
        oblique = self._drift_at(300, self.MPH_10, angle_deg=45.0)
        assert oblique / full == pytest.approx(0.707, rel=0.02)

    def test_drift_scales_with_wind_speed(self):
        single = self._drift_at(300, self.MPH_10)
        double = self._drift_at(300, self.MPH_10 * 2)
        assert double == pytest.approx(single * 2, rel=0.05)

    def test_drift_grows_faster_than_distance(self):
        """Drift comes from lag time, which compounds as the bullet slows."""
        d200 = self._drift_at(200, self.MPH_10)
        d400 = self._drift_at(400, self.MPH_10)
        assert d400 > d200 * 4

    def test_headwind_costs_velocity_and_tailwind_saves_it(self):
        """The old model ignored the along-track component entirely."""
        def velocity(angle):
            r = calculate_trajectory(
                self._proj(), zero_range_m=100, max_range_m=300, step_m=100,
                wind_speed_ms=8.94, wind_angle_deg=angle,
            )
            return next(p for p in r.points if p.range_m == 300).velocity_fps

        assert velocity(180) < velocity(90) < velocity(0)

    def test_still_air_leaves_the_trajectory_untouched(self):
        r = calculate_trajectory(
            self._proj(), zero_range_m=100, max_range_m=300, step_m=100, wind_speed_ms=0.0
        )
        point = next(p for p in r.points if p.range_m == 300)
        assert all(p.wind_drift_cm == 0.0 for p in r.points)
        assert point.velocity_fps == pytest.approx(2040, rel=0.03)
        assert point.drop_cm == pytest.approx(-49.0, abs=4.0)


class TestRangeBounds:
    def test_points_stop_at_the_requested_range(self):
        """Asking for 300m used to return a 400m row as well."""
        proj = ProjectileData(weight_grains=168, bc_g1=0.462, muzzle_velocity_fps=2650)
        for max_range, step in ((300, 100), (400, 100), (500, 25)):
            r = calculate_trajectory(proj, max_range_m=max_range, step_m=step)
            assert r.points[-1].range_m == max_range
            assert r.points[0].range_m == step
