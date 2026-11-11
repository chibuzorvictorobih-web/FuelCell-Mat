"""Physics-direction, dimensional, boundary, and reproducibility checks."""

from dataclasses import replace

import numpy as np
import pytest

from fuelcell_mat.model import (
    FARADAY_C_MOL,
    Kinetics,
    Membrane,
    OperatingConditions,
    input_snapshot,
    maximum_power_point,
    membrane_asr_ohm_cm2,
    membrane_conductivity_s_cm,
    polarization_curve,
    reactant_partial_pressures_bar,
    reversible_voltage_v,
    saturation_vapor_pressure_bar,
    stack_metrics,
)


def test_water_saturation_pressure_at_80c():
    # Approx. 0.474 bar around 80 °C (reference physical property).
    assert saturation_vapor_pressure_bar(80) == pytest.approx(0.474, abs=0.007)


def test_vapor_pressure_range_rejected():
    with pytest.raises(ValueError):
        saturation_vapor_pressure_bar(130)


def test_oxygen_pressure_accounts_for_humidity_and_dry_fraction():
    c = OperatingConditions()
    h2, o2 = reactant_partial_pressures_bar(c)
    vapor = saturation_vapor_pressure_bar(c.temperature_c) * c.anode_rh_pct / 100
    assert h2 == pytest.approx(c.anode_pressure_bar - vapor)
    assert o2 == pytest.approx((c.cathode_pressure_bar - vapor) * 0.21)


def test_nernst_increases_with_oxygen_fraction():
    c = OperatingConditions()
    richer = replace(c, oxygen_fraction_dry=0.40)
    assert reversible_voltage_v(richer) > reversible_voltage_v(c)


def test_conductivity_increases_with_temperature_and_humidity():
    m = Membrane()
    base = OperatingConditions()
    warmer = replace(base, temperature_c=90)
    wetter = replace(base, anode_rh_pct=100, cathode_rh_pct=100)
    assert membrane_conductivity_s_cm(m, warmer) > membrane_conductivity_s_cm(m, base)
    assert membrane_conductivity_s_cm(m, wetter) > membrane_conductivity_s_cm(m, base)


def test_asr_doubles_when_thickness_doubles():
    m = Membrane()
    c = OperatingConditions()
    assert membrane_asr_ohm_cm2(replace(m, thickness_um=100), c) == pytest.approx(
        2 * membrane_asr_ohm_cm2(m, c)
    )


def test_open_circuit_voltage_and_power():
    data = polarization_curve([0.0], Membrane(), OperatingConditions(), Kinetics())
    assert data.iloc[0]["predicted_voltage_V"] == pytest.approx(reversible_voltage_v(OperatingConditions()))
    assert data.iloc[0]["power_density_W_cm2"] == pytest.approx(0)
    assert np.isnan(data.iloc[0]["hhv_voltage_efficiency_pct"])


def test_polarization_decreases_and_power_nonnegative():
    df = polarization_curve(np.linspace(0, 1.5, 60), Membrane(), OperatingConditions(), Kinetics())
    voltage = df["predicted_voltage_V"].dropna().to_numpy()
    assert np.all(np.diff(voltage) < 0)
    assert (df["power_density_W_cm2"].dropna() >= 0).all()
    assert df["activation_loss_V"].iloc[0] == 0
    assert df["ohmic_loss_V"].iloc[0] == 0
    assert df["transport_loss_V"].iloc[0] == 0


def test_ohmic_voltage_drop_and_thickness_direction():
    m = Membrane()
    c = OperatingConditions()
    k = Kinetics()
    thin = stack_metrics(1.0, m, c, k)
    thick = stack_metrics(1.0, replace(m, thickness_um=150), c, k)
    assert thin["cell_voltage_V"] > thick["cell_voltage_V"]
    expected_drop = 1.0 * (membrane_asr_ohm_cm2(replace(m, thickness_um=150), c) - membrane_asr_ohm_cm2(m, c))
    assert thin["cell_voltage_V"] - thick["cell_voltage_V"] == pytest.approx(expected_drop)


def test_hydrogen_flow_follows_faradays_law_and_stack_cell_count():
    c = OperatingConditions(active_area_cm2=100, cell_count=40)
    metrics = stack_metrics(1.0, Membrane(), c, Kinetics())
    expected_h2_mol_per_second = 1.0 * 100 * 40 / (2 * FARADAY_C_MOL)
    expected_h2_g_h = expected_h2_mol_per_second * 2.01588 * 3600
    assert metrics["hydrogen_consumption_g_h"] == pytest.approx(expected_h2_g_h)
    assert metrics["hydrogen_feed_g_h"] == pytest.approx(expected_h2_g_h * 1.5)
    assert metrics["stack_power_W"] == pytest.approx(metrics["cell_voltage_V"] * 100 * 40)


def test_default_point_plausible_but_not_validation():
    point = stack_metrics(1.0, Membrane(), OperatingConditions(), Kinetics())
    assert point["operational"]
    assert 0.50 < point["cell_voltage_V"] < 1.0
    assert 30 < point["hhv_voltage_efficiency_pct"] < 70


def test_nonpositive_voltage_is_masked():
    m = Membrane(thickness_um=250, conductivity_ref_s_cm=0.005)
    c = OperatingConditions(anode_rh_pct=30, cathode_rh_pct=30)
    point = stack_metrics(1.0, m, c, Kinetics())
    assert not point["operational"]
    assert point["cell_voltage_V"] is None
    assert point["stack_power_W"] is None
    assert np.isnan(polarization_curve([1.0], m, c, Kinetics())["predicted_voltage_V"].iloc[0])


def test_current_limits_rejected():
    with pytest.raises(ValueError, match="limiting"):
        polarization_curve([1.8], Membrane(), OperatingConditions(), Kinetics())
    with pytest.raises(ValueError, match="current"):
        polarization_curve([-0.1], Membrane(), OperatingConditions(), Kinetics())
    with pytest.raises(ValueError):
        polarization_curve([np.nan], Membrane(), OperatingConditions(), Kinetics())


def test_invalid_inputs_rejected():
    with pytest.raises(ValueError):
        Membrane(thickness_um=0).validate()
    with pytest.raises(ValueError):
        OperatingConditions(temperature_c=95).validate()
    with pytest.raises(ValueError):
        OperatingConditions(cell_count=1.5).validate()
    with pytest.raises(ValueError):
        Kinetics(limiting_current_a_cm2=0).validate()


def test_power_peak_is_in_range():
    k = Kinetics()
    peak = maximum_power_point(Membrane(), OperatingConditions(), k)
    assert peak["power_density_W_cm2"] > 0
    assert 0 < peak["current_density_A_cm2"] <= 0.98 * k.limiting_current_a_cm2


def test_snapshot_structure_reproducible():
    snap = input_snapshot(Membrane(), OperatingConditions(), Kinetics())
    assert snap["model_version"] == "1.0.0"
    assert snap["membrane"]["thickness_um"] == 50.0
