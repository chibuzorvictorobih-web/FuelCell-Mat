"""Steady-state, illustrative proton-exchange membrane fuel-cell model.

All pressures are absolute. Gas activities are partial pressures divided by
1 bar, assuming ideal gases and unit liquid-water activity. The model is not
calibrated to a commercial cell or intended for safety-critical design.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

FARADAY_C_MOL = 96485.33212
GAS_CONSTANT_J_MOL_K = 8.314462618
MOLAR_MASS_H2_G_MOL = 2.01588
REFERENCE_TEMPERATURE_K = 298.15
HHV_VOLTAGE_V = 1.481  # Approximate 25°C HHV-equivalent per two electrons.
LHV_VOLTAGE_V = 1.253  # Approximate 25°C LHV-equivalent per two electrons.
MODEL_VERSION = "1.0.0"


@dataclass(frozen=True)
class Membrane:
    name: str = "Reference membrane"
    thickness_um: float = 50.0
    conductivity_ref_s_cm: float = 0.10
    activation_energy_kj_mol: float = 12.0
    hydration_exponent: float = 1.5
    reference_temp_c: float = 80.0

    def validate(self) -> None:
        if not self.name.strip():
            raise ValueError("Membrane name cannot be empty.")
        if not 5 <= self.thickness_um <= 250:
            raise ValueError("Membrane thickness must be between 5 and 250 µm.")
        if not 0.005 <= self.conductivity_ref_s_cm <= 0.30:
            raise ValueError("Reference conductivity must be 0.005–0.30 S/cm.")
        if not 0 <= self.activation_energy_kj_mol <= 40:
            raise ValueError("Activation energy must be 0–40 kJ/mol.")
        if not 0 <= self.hydration_exponent <= 4:
            raise ValueError("Hydration exponent must be 0–4.")
        if not 50 <= self.reference_temp_c <= 90:
            raise ValueError("Reference temperature must be 50–90 °C.")


@dataclass(frozen=True)
class OperatingConditions:
    temperature_c: float = 80.0
    anode_pressure_bar: float = 1.5
    cathode_pressure_bar: float = 1.5
    anode_rh_pct: float = 90.0
    cathode_rh_pct: float = 90.0
    oxygen_fraction_dry: float = 0.21
    active_area_cm2: float = 100.0
    cell_count: int = 40
    hydrogen_feed_stoich: float = 1.5
    air_feed_stoich: float = 2.0

    def validate(self) -> None:
        if not 50 <= self.temperature_c <= 90:
            raise ValueError("Cell temperature must be 50–90 °C.")
        if not 1 <= self.anode_pressure_bar <= 4:
            raise ValueError("Anode pressure must be 1–4 bar absolute.")
        if not 1 <= self.cathode_pressure_bar <= 4:
            raise ValueError("Cathode pressure must be 1–4 bar absolute.")
        if not 30 <= self.anode_rh_pct <= 100:
            raise ValueError("Anode relative humidity must be 30–100%.")
        if not 30 <= self.cathode_rh_pct <= 100:
            raise ValueError("Cathode relative humidity must be 30–100%.")
        if not 0.18 <= self.oxygen_fraction_dry <= 1:
            raise ValueError("Dry oxidant oxygen mole fraction must be 0.18–1.")
        if not 1 <= self.active_area_cm2 <= 2500:
            raise ValueError("Active area must be 1–2500 cm² per cell.")
        if isinstance(self.cell_count, bool) or not isinstance(self.cell_count, (int, np.integer)):
            raise ValueError("Cell count must be a whole number.")
        if not 1 <= self.cell_count <= 500:
            raise ValueError("Cell count must be 1–500.")
        if not 1 <= self.hydrogen_feed_stoich <= 5:
            raise ValueError("Hydrogen feed stoichiometry must be 1–5.")
        if not 1 <= self.air_feed_stoich <= 5:
            raise ValueError("Oxidant feed stoichiometry must be 1–5.")
        psat = saturation_vapor_pressure_bar(self.temperature_c)
        if psat * self.anode_rh_pct / 100 >= self.anode_pressure_bar:
            raise ValueError("Anode water-vapor partial pressure exceeds total pressure.")
        if psat * self.cathode_rh_pct / 100 >= self.cathode_pressure_bar:
            raise ValueError("Cathode water-vapor partial pressure exceeds total pressure.")


@dataclass(frozen=True)
class Kinetics:
    effective_exchange_current_a_cm2: float = 0.008
    charge_transfer_coefficient: float = 0.5
    effective_electrons: float = 1.0
    limiting_current_a_cm2: float = 1.8
    transport_multiplier: float = 3.5
    other_asr_ohm_cm2: float = 0.04

    def validate(self) -> None:
        if not 0.0001 <= self.effective_exchange_current_a_cm2 <= 0.1:
            raise ValueError("Effective exchange current density must be 0.0001–0.1 A/cm².")
        if not 0.2 <= self.charge_transfer_coefficient <= 1:
            raise ValueError("Charge-transfer coefficient must be 0.2–1.")
        if not 1 <= self.effective_electrons <= 4:
            raise ValueError("Effective electron number must be 1–4.")
        if not 0.4 <= self.limiting_current_a_cm2 <= 4:
            raise ValueError("Limiting current density must be 0.4–4 A/cm².")
        if not 1 <= self.transport_multiplier <= 10:
            raise ValueError("Transport multiplier must be 1–10.")
        if not 0 <= self.other_asr_ohm_cm2 <= 0.5:
            raise ValueError("Other area-specific resistance must be 0–0.5 Ω·cm².")


def saturation_vapor_pressure_bar(temperature_c: float) -> float:
    """NIST Stull (1947) Antoine fit for water, 255.9–373 K, bar."""
    kelvin = float(temperature_c) + 273.15
    if not 255.9 <= kelvin <= 373.0:
        raise ValueError("Water vapor-pressure fit applies from 255.9 to 373 K.")
    return 10 ** (4.6543 - 1435.264 / (kelvin - 64.848))


def reactant_partial_pressures_bar(conditions: OperatingConditions) -> tuple[float, float]:
    """Use pure hydrogen as the dry anode gas and specified dry cathode O2 fraction."""
    conditions.validate()
    psat = saturation_vapor_pressure_bar(conditions.temperature_c)
    p_h2 = conditions.anode_pressure_bar - psat * conditions.anode_rh_pct / 100
    p_o2 = (
        conditions.cathode_pressure_bar - psat * conditions.cathode_rh_pct / 100
    ) * conditions.oxygen_fraction_dry
    return p_h2, p_o2


def reversible_voltage_v(conditions: OperatingConditions) -> float:
    """Liquid-water Nernst equilibrium voltage using ideal-gas activities."""
    p_h2, p_o2 = reactant_partial_pressures_bar(conditions)
    kelvin = conditions.temperature_c + 273.15
    standard_v = 1.229 - 0.00085 * (kelvin - REFERENCE_TEMPERATURE_K)
    return float(
        standard_v
        + GAS_CONSTANT_J_MOL_K * kelvin / (2 * FARADAY_C_MOL)
        * np.log(p_h2 * np.sqrt(p_o2))
    )


def membrane_conductivity_s_cm(membrane: Membrane, conditions: OperatingConditions) -> float:
    """Illustrative Arrhenius × RH-exponent approximation, not a membrane datasheet."""
    membrane.validate()
    conditions.validate()
    kelvin = conditions.temperature_c + 273.15
    t_ref = membrane.reference_temp_c + 273.15
    rh_avg_fraction = (conditions.anode_rh_pct + conditions.cathode_rh_pct) / 200
    temperature_factor = np.exp(
        membrane.activation_energy_kj_mol * 1000 / GAS_CONSTANT_J_MOL_K
        * (1 / t_ref - 1 / kelvin)
    )
    return float(membrane.conductivity_ref_s_cm * temperature_factor * rh_avg_fraction ** membrane.hydration_exponent)


def membrane_asr_ohm_cm2(membrane: Membrane, conditions: OperatingConditions) -> float:
    """ASR = dry thickness (cm) / effective conductivity (S/cm)."""
    return float(membrane.thickness_um * 1e-4 / membrane_conductivity_s_cm(membrane, conditions))


def polarization_curve(
    current_densities_a_cm2: np.ndarray | list[float],
    membrane: Membrane,
    conditions: OperatingConditions,
    kinetics: Kinetics,
) -> pd.DataFrame:
    """Calculate modeled voltage losses over current-density points.

    At or below zero predicted voltage, results are masked rather than
    reported as a functioning cell. Currents must satisfy 0 <= j < j_lim.
    """
    membrane.validate()
    conditions.validate()
    kinetics.validate()
    j = np.asarray(current_densities_a_cm2, dtype=float)
    if j.ndim != 1 or len(j) == 0 or not np.all(np.isfinite(j)):
        raise ValueError("Current densities must be a nonempty finite 1D array.")
    if np.any(j < 0) or np.any(j >= kinetics.limiting_current_a_cm2):
        raise ValueError("Each current density must satisfy 0 ≤ j < limiting current density.")

    kelvin = conditions.temperature_c + 273.15
    e_rev = reversible_voltage_v(conditions)
    sigma = membrane_conductivity_s_cm(membrane, conditions)
    asr_membrane = membrane.thickness_um * 1e-4 / sigma
    asr_total = asr_membrane + kinetics.other_asr_ohm_cm2

    # Symmetric Butler–Volmer-type surrogate; parameters are effective fit values.
    activation_v = (
        GAS_CONSTANT_J_MOL_K * kelvin
        / (kinetics.charge_transfer_coefficient * kinetics.effective_electrons * FARADAY_C_MOL)
        * np.arcsinh(j / (2 * kinetics.effective_exchange_current_a_cm2))
    )
    ohmic_v = j * asr_total
    # Limiting-current logarithm with an explicit, empirical transport factor.
    transport_v = -(
        kinetics.transport_multiplier * GAS_CONSTANT_J_MOL_K * kelvin
        / (2 * FARADAY_C_MOL)
        * np.log1p(-j / kinetics.limiting_current_a_cm2)
    )
    raw_voltage = e_rev - activation_v - ohmic_v - transport_v
    feasible = raw_voltage > 0
    voltage = np.where(feasible, raw_voltage, np.nan)
    power_density = j * voltage
    # Efficiency is undefined at zero power; values exclude auxiliaries and gas utilization.
    hhv_efficiency = np.where((j > 0) & feasible, voltage / HHV_VOLTAGE_V * 100, np.nan)
    lhv_efficiency = np.where((j > 0) & feasible, voltage / LHV_VOLTAGE_V * 100, np.nan)

    return pd.DataFrame({
        "current_density_A_cm2": j,
        "reversible_voltage_V": np.full_like(j, e_rev),
        "activation_loss_V": activation_v,
        "ohmic_loss_V": ohmic_v,
        "transport_loss_V": transport_v,
        "predicted_voltage_V": voltage,
        "power_density_W_cm2": power_density,
        "hhv_voltage_efficiency_pct": hhv_efficiency,
        "lhv_voltage_efficiency_pct": lhv_efficiency,
        "membrane_conductivity_S_cm": np.full_like(j, sigma),
        "membrane_asr_ohm_cm2": np.full_like(j, asr_membrane),
        "total_asr_ohm_cm2": np.full_like(j, asr_total),
        "operational": feasible,
    })


def stack_metrics(
    current_density_a_cm2: float,
    membrane: Membrane,
    conditions: OperatingConditions,
    kinetics: Kinetics,
) -> dict:
    """Return cell, stack, and reactant-flow metrics at one operating point."""
    curve = polarization_curve([current_density_a_cm2], membrane, conditions, kinetics)
    row = curve.iloc[0]
    is_operational = bool(row["operational"]) and current_density_a_cm2 > 0
    cell_current_a = current_density_a_cm2 * conditions.active_area_cm2
    consumed_mol_s = cell_current_a * conditions.cell_count / (2 * FARADAY_C_MOL)
    oxidant_consumed_mol_s = consumed_mol_s / 2
    h2_consumed_g_h = consumed_mol_s * MOLAR_MASS_H2_G_MOL * 3600
    voltage = float(row["predicted_voltage_V"]) if is_operational else None
    return {
        "current_density_A_cm2": current_density_a_cm2,
        "operational": is_operational,
        "reversible_voltage_V": float(row["reversible_voltage_V"]),
        "cell_voltage_V": voltage,
        "cell_current_A": cell_current_a,
        "stack_voltage_V": voltage * conditions.cell_count if is_operational else None,
        "stack_power_W": voltage * cell_current_a * conditions.cell_count if is_operational else None,
        "power_density_W_cm2": float(row["power_density_W_cm2"]) if is_operational else None,
        "hhv_voltage_efficiency_pct": float(row["hhv_voltage_efficiency_pct"]) if is_operational else None,
        "lhv_voltage_efficiency_pct": float(row["lhv_voltage_efficiency_pct"]) if is_operational else None,
        "membrane_conductivity_S_cm": float(row["membrane_conductivity_S_cm"]),
        "membrane_asr_ohm_cm2": float(row["membrane_asr_ohm_cm2"]),
        "total_asr_ohm_cm2": float(row["total_asr_ohm_cm2"]),
        "activation_loss_V": float(row["activation_loss_V"]),
        "ohmic_loss_V": float(row["ohmic_loss_V"]),
        "transport_loss_V": float(row["transport_loss_V"]),
        "hydrogen_consumption_g_h": h2_consumed_g_h if is_operational else None,
        "hydrogen_feed_g_h": h2_consumed_g_h * conditions.hydrogen_feed_stoich if is_operational else None,
        "oxygen_consumption_mol_h": oxidant_consumed_mol_s * 3600 if is_operational else None,
        "dry_oxidant_feed_mol_h": (
            oxidant_consumed_mol_s * 3600 / conditions.oxygen_fraction_dry * conditions.air_feed_stoich
            if is_operational else None
        ),
    }


def maximum_power_point(membrane: Membrane, conditions: OperatingConditions, kinetics: Kinetics) -> dict:
    """Numerically locate maximum modeled power on 0–98% of limiting current."""
    j_grid = np.linspace(0, kinetics.limiting_current_a_cm2 * 0.98, 3001)
    data = polarization_curve(j_grid, membrane, conditions, kinetics)
    power = data["power_density_W_cm2"].to_numpy()
    if np.all(np.isnan(power)):
        return {"current_density_A_cm2": None, "power_density_W_cm2": None, "cell_voltage_V": None}
    i = int(np.nanargmax(power))
    return {
        "current_density_A_cm2": float(j_grid[i]),
        "power_density_W_cm2": float(power[i]),
        "cell_voltage_V": float(data.iloc[i]["predicted_voltage_V"]),
    }


def input_snapshot(membrane: Membrane, conditions: OperatingConditions, kinetics: Kinetics) -> dict:
    return {
        "model_version": MODEL_VERSION,
        "disclaimer": "Illustrative steady-state calculation; not experimentally validated or a design certification.",
        "membrane": asdict(membrane),
        "operating_conditions": asdict(conditions),
        "kinetics": asdict(kinetics),
    }
