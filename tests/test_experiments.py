"""Comparison/sensitivity logic checks."""

import numpy as np
import pytest

from fuelcell_mat.experiments import sensitivity_study
from fuelcell_mat.model import Kinetics, Membrane, OperatingConditions, polarization_curve
from fuelcell_mat.presets import MEMBRANES


def test_preset_comparison_thin_membrane_improves_voltage():
    c, k = OperatingConditions(), Kinetics()
    thin = polarization_curve([1.0], MEMBRANES["Thin / conductive"], c, k).iloc[0]
    thick = polarization_curve([1.0], MEMBRANES["Thick / resistive"], c, k).iloc[0]
    assert thin["predicted_voltage_V"] > thick["predicted_voltage_V"]


def test_thickness_sensitivity_correct_trend():
    df = sensitivity_study(
        "Membrane thickness", [25.0, 50.0, 100.0], 1.0,
        Membrane(), OperatingConditions(), Kinetics(),
    )
    assert len(df) == 3
    assert np.all(np.diff(df["cell_voltage_V"].to_numpy()) < 0)
    assert np.all(np.diff(df["membrane_asr_ohm_cm2"].to_numpy()) > 0)


def test_humidity_sensitivity_correct_trend():
    df = sensitivity_study(
        "Relative humidity (both feeds)", [50.0, 75.0, 100.0], 1.0,
        Membrane(), OperatingConditions(), Kinetics(),
    )
    assert np.all(np.diff(df["membrane_asr_ohm_cm2"].to_numpy()) < 0)


def test_sensitivity_bounds_and_names():
    args = (1.0, Membrane(), OperatingConditions(), Kinetics())
    with pytest.raises(ValueError, match="Unknown"):
        sensitivity_study("not a parameter", [50], *args)
    with pytest.raises(ValueError, match="within"):
        sensitivity_study("Membrane thickness", [251], *args)
    with pytest.raises(ValueError, match="finite"):
        sensitivity_study("Membrane thickness", [np.nan], *args)
