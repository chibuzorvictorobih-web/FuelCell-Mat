"""One-at-a-time parameter studies holding other model inputs fixed."""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd

from fuelcell_mat.model import Kinetics, Membrane, OperatingConditions, stack_metrics

SENSITIVITY_PARAMETERS: dict[str, tuple[float, float, str]] = {
    "Membrane thickness": (5.0, 250.0, "µm"),
    "Reference conductivity": (0.005, 0.3, "S/cm"),
    "Relative humidity (both feeds)": (30.0, 100.0, "%"),
    "Cell temperature": (50.0, 90.0, "°C"),
}


def sensitivity_study(
    parameter: str,
    values: np.ndarray | list[float],
    current_density_a_cm2: float,
    membrane: Membrane,
    conditions: OperatingConditions,
    kinetics: Kinetics,
) -> pd.DataFrame:
    if parameter not in SENSITIVITY_PARAMETERS:
        raise ValueError(f"Unknown sensitivity parameter: {parameter}")
    lo, hi, unit = SENSITIVITY_PARAMETERS[parameter]
    values = np.asarray(values, dtype=float)
    if values.ndim != 1 or len(values) == 0 or not np.all(np.isfinite(values)):
        raise ValueError("Sensitivity values must be a nonempty finite 1D array.")
    if np.any(values < lo) or np.any(values > hi):
        raise ValueError(f"Sensitivity values for {parameter} must be within {lo}–{hi}.")
    records: list[dict] = []
    for value in values:
        test_membrane, test_conditions = membrane, conditions
        if parameter == "Membrane thickness":
            test_membrane = replace(membrane, thickness_um=float(value))
        elif parameter == "Reference conductivity":
            test_membrane = replace(membrane, conductivity_ref_s_cm=float(value))
        elif parameter == "Relative humidity (both feeds)":
            test_conditions = replace(conditions, anode_rh_pct=float(value), cathode_rh_pct=float(value))
        elif parameter == "Cell temperature":
            test_conditions = replace(conditions, temperature_c=float(value))
        metrics = stack_metrics(current_density_a_cm2, test_membrane, test_conditions, kinetics)
        records.append({
            "parameter": parameter,
            "parameter_unit": unit,
            "parameter_value": float(value),
            "cell_voltage_V": metrics["cell_voltage_V"],
            "power_density_W_cm2": metrics["power_density_W_cm2"],
            "stack_power_W": metrics["stack_power_W"],
            "membrane_asr_ohm_cm2": metrics["membrane_asr_ohm_cm2"],
            "operational": metrics["operational"],
        })
    return pd.DataFrame.from_records(records)
