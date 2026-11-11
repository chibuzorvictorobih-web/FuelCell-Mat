"""FuelCell-Mat: interactive PEM fuel-cell material and performance exploration."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import streamlit as st

from fuelcell_mat.charts import (
    comparison_chart,
    loss_chart,
    power_chart,
    sensitivity_chart,
    voltage_chart,
)
from fuelcell_mat.experiments import SENSITIVITY_PARAMETERS, sensitivity_study
from fuelcell_mat.model import (
    Kinetics,
    Membrane,
    OperatingConditions,
    input_snapshot,
    maximum_power_point,
    polarization_curve,
    reactant_partial_pressures_bar,
    stack_metrics,
)
from fuelcell_mat.presets import MEMBRANES

st.set_page_config(
    page_title="FuelCell-Mat | PEM fuel-cell calculator",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
.block-container {padding-top: 5rem; padding-bottom: 3.5rem; max-width: 1450px;}
.fcm-subtitle {color: #64748b; font-size: 1.05rem; margin-top: -.65rem; margin-bottom: 1.4rem;}
.fcm-note {border-left: 3px solid #0e7490; padding: .7rem 1rem;
           background: rgba(14,116,144,.055); border-radius: 0 .4rem .4rem 0;}
[data-testid="stMetric"] {background: rgba(148,163,184,.075); padding: 12px;
                            border-radius: 10px; border: 1px solid rgba(148,163,184,.14);}
</style>
""", unsafe_allow_html=True)

st.markdown("**MATERIALS FOR ENERGY CONVERSION · PEMFC**")
st.title("FuelCell-Mat")
st.markdown('<div class="fcm-subtitle">Calculate cell voltage, stack power, hydrogen demand and membrane performance using an illustrative PEM fuel-cell model.</div>', unsafe_allow_html=True)

# Streamlit forms commit their inputs as one calculation instead of updating
# results every time a value changes.
DEFAULT_CONTROLS = {
    "fcm_preset": "Reference membrane",
    "fcm_thickness": 50.0,
    "fcm_conductivity": 0.10,
    "fcm_ea": 12.0,
    "fcm_hydration_exp": 1.5,
    "fcm_temperature": 80,
    "fcm_target_j": 1.0,
    "fcm_anode_pressure": 1.5,
    "fcm_cathode_pressure": 1.5,
    "fcm_anode_rh": 90,
    "fcm_cathode_rh": 90,
    "fcm_oxidant": "Air (21% O₂)",
    "fcm_active_area": 100.0,
    "fcm_cell_count": 40,
    "fcm_h2_stoich": 1.5,
    "fcm_oxidant_stoich": 2.0,
    "fcm_exchange_current": 0.008,
    "fcm_transfer": 0.5,
    "fcm_n_effective": 1.0,
    "fcm_limiting_current": 1.8,
    "fcm_multiplier": 3.5,
    "fcm_other_asr": 0.04,
}
for control_name, default_value in DEFAULT_CONTROLS.items():
    st.session_state.setdefault(control_name, default_value)


def load_membrane_preset() -> None:
    """Populate membrane controls when a hypothetical preset is selected."""
    name = st.session_state["fcm_preset"]
    if name in MEMBRANES:
        selected = MEMBRANES[name]
        st.session_state["fcm_thickness"] = float(selected.thickness_um)
        st.session_state["fcm_conductivity"] = float(selected.conductivity_ref_s_cm)
        st.session_state["fcm_ea"] = float(selected.activation_energy_kj_mol)
        st.session_state["fcm_hydration_exp"] = float(selected.hydration_exponent)


st.header("Calculator")
st.write("Enter your inputs below, then select **Calculate fuel-cell performance**. Results only change when you press the button.")
st.selectbox(
    "Membrane starting point",
    [*MEMBRANES.keys(), "Custom"],
    key="fcm_preset",
    on_change=load_membrane_preset,
    help="Preset values are illustrative, not independently measured materials. You can edit them below.",
)

with st.form("fcm_calculator", clear_on_submit=False):
    st.subheader("Core calculation inputs")
    left, middle, right = st.columns(3)
    with left:
        thickness = st.number_input(
            "Membrane thickness (µm)", min_value=5.0, max_value=250.0,
            step=5.0, key="fcm_thickness",
        )
        conductivity = st.number_input(
            "Reference conductivity (S/cm)", min_value=0.005, max_value=0.30,
            step=0.005, format="%.3f", key="fcm_conductivity",
            help="At 80 °C and 100% RH, before temperature and hydration corrections.",
        )
    with middle:
        temperature = st.slider("Cell temperature (°C)", 50, 90, key="fcm_temperature")
        target_j = st.number_input(
            "Operating current density (A/cm²)", min_value=0.01, max_value=3.9,
            step=0.05, format="%.2f", key="fcm_target_j",
            help="Must be lower than the limiting current density in Advanced settings.",
        )
    with right:
        cathode_pressure = st.slider(
            "Cathode pressure (bar absolute)", 1.0, 4.0, step=0.1,
            key="fcm_cathode_pressure",
        )
        cathode_rh = st.slider("Cathode relative humidity (%)", 30, 100, key="fcm_cathode_rh")

    with st.expander("Advanced settings — anode, stack, membrane and electrode parameters", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Anode and feed gases**")
            anode_pressure = st.slider(
                "Anode pressure (bar absolute)", 1.0, 4.0, step=0.1,
                key="fcm_anode_pressure",
            )
            anode_rh = st.slider("Anode relative humidity (%)", 30, 100, key="fcm_anode_rh")
            oxidant = st.selectbox(
                "Oxidant composition",
                ["Air (21% O₂)", "Oxygen-enriched (40% O₂)", "Pure oxygen (100% O₂)"],
                key="fcm_oxidant",
            )
            st.markdown("**Membrane response**")
            ea = st.number_input(
                "Conductivity activation energy (kJ/mol)", min_value=0.0,
                max_value=40.0, step=1.0, key="fcm_ea",
            )
            rh_exponent = st.number_input(
                "Humidity-response exponent", min_value=0.0, max_value=4.0,
                step=0.1, key="fcm_hydration_exp",
            )
            st.markdown("**Stack sizing and feed rates**")
            active_area = st.number_input(
                "Active area per cell (cm²)", min_value=1.0,
                max_value=2500.0, step=10.0, key="fcm_active_area",
            )
            cell_count = st.number_input(
                "Series-connected cells", min_value=1, max_value=500,
                step=1, key="fcm_cell_count",
            )
            h2_stoich = st.slider(
                "Hydrogen feed stoichiometry", 1.0, 5.0, step=0.1,
                key="fcm_h2_stoich",
            )
            air_stoich = st.slider(
                "Oxidant feed stoichiometry", 1.0, 5.0, step=0.1,
                key="fcm_oxidant_stoich",
            )
        with c2:
            st.markdown("**Electrodes and mass transport**")
            exchange_current = st.number_input(
                "Effective exchange current density (A/cm²)", min_value=0.0001,
                max_value=0.1, step=0.001, format="%.4f", key="fcm_exchange_current",
            )
            transfer = st.slider(
                "Charge-transfer coefficient", 0.2, 1.0, step=0.05,
                key="fcm_transfer",
            )
            n_effective = st.slider(
                "Effective electrons (activation model)", 1.0, 4.0,
                step=0.5, key="fcm_n_effective",
            )
            limiting_current = st.slider(
                "Limiting current density (A/cm²)", 0.4, 4.0,
                step=0.1, key="fcm_limiting_current",
            )
            multiplier = st.slider(
                "Mass-transport scaling factor", 1.0, 10.0,
                step=0.5, key="fcm_multiplier",
            )
            other_asr = st.number_input(
                "Other ASR (Ω·cm²)", min_value=0.0, max_value=0.5,
                step=0.01, format="%.3f", key="fcm_other_asr",
            )

    calculate_pressed = st.form_submit_button(
        "Calculate fuel-cell performance", type="primary", use_container_width=True,
    )

if calculate_pressed:
    try:
        oxygen_fraction = {
            "Air (21% O₂)": 0.21,
            "Oxygen-enriched (40% O₂)": 0.40,
            "Pure oxygen (100% O₂)": 1.0,
        }[oxidant]
        candidate_membrane = Membrane(
            name=st.session_state["fcm_preset"], thickness_um=thickness,
            conductivity_ref_s_cm=conductivity,
            activation_energy_kj_mol=ea, hydration_exponent=rh_exponent,
        )
        candidate_conditions = OperatingConditions(
            temperature_c=temperature, anode_pressure_bar=anode_pressure,
            cathode_pressure_bar=cathode_pressure, anode_rh_pct=anode_rh,
            cathode_rh_pct=cathode_rh, oxygen_fraction_dry=oxygen_fraction,
            active_area_cm2=active_area, cell_count=int(cell_count),
            hydrogen_feed_stoich=h2_stoich, air_feed_stoich=air_stoich,
        )
        candidate_kinetics = Kinetics(
            effective_exchange_current_a_cm2=exchange_current,
            charge_transfer_coefficient=transfer, effective_electrons=n_effective,
            limiting_current_a_cm2=limiting_current,
            transport_multiplier=multiplier, other_asr_ohm_cm2=other_asr,
        )
        # Validate all inputs, including the operating current against the
        # selected transport limit, before saving this calculation.
        stack_metrics(target_j, candidate_membrane, candidate_conditions, candidate_kinetics)
        st.session_state["fcm_calculated_inputs"] = (
            candidate_membrane, candidate_conditions, candidate_kinetics, float(target_j),
        )
    except (ValueError, KeyError) as exc:
        st.session_state.pop("fcm_calculated_inputs", None)
        st.error(f"Cannot calculate with these inputs: {exc}")

if "fcm_calculated_inputs" not in st.session_state:
    st.info("Enter the operating conditions and press **Calculate fuel-cell performance** to see results, charts and downloads.")
    st.stop()

membrane, conditions, kinetics, target_j = st.session_state["fcm_calculated_inputs"]
try:
    j_values = np.linspace(0, kinetics.limiting_current_a_cm2 * 0.98, 181)
    df = polarization_curve(j_values, membrane, conditions, kinetics)
    point = stack_metrics(target_j, membrane, conditions, kinetics)
    peak = maximum_power_point(membrane, conditions, kinetics)
except ValueError as exc:
    st.error(f"Check the calculation inputs: {exc}")
    st.stop()

st.divider()
st.subheader("Calculator results")
a, b, c, d = st.columns(4)
a.metric("Cell voltage", f"{point['cell_voltage_V']:.3f} V" if point["operational"] else "Not feasible")
b.metric("Power density", f"{point['power_density_W_cm2']:.3f} W/cm²" if point["operational"] else "—")
c.metric("Stack power", f"{point['stack_power_W'] / 1000:.3f} kW" if point["operational"] else "—")
d.metric("HHV voltage efficiency", f"{point['hhv_voltage_efficiency_pct']:.1f}%" if point["operational"] else "—")
st.caption("These results represent the last submitted calculation. Edit the form and press Calculate again to update them.")

if not point["operational"]:
    st.warning("At this current density, the assumed losses exceed the reversible voltage. No working-cell power is reported. Try a thinner or more conductive membrane, or a lower current density.")

summary_tab, comparison_tab, sensitivity_tab, methods_tab, exports_tab = st.tabs([
    "Performance curves", "Materials comparison", "Sensitivity study", "Equations & limitations", "Export results",
])

with summary_tab:
    st.subheader("Performance curves and engineering indicators")
    left, right = st.columns(2)
    with left:
        st.plotly_chart(voltage_chart(df, target_j), use_container_width=True)
    with right:
        st.plotly_chart(power_chart(df, target_j), use_container_width=True)
    st.caption("Dotted vertical guides show the selected operating current density. The dashed upper curve is the theoretical reversible voltage, not a measured open-circuit voltage.")

    col_l, col_r = st.columns([1.1, 1])
    with col_l:
        st.subheader("Voltage-loss breakdown")
        st.plotly_chart(loss_chart(df), use_container_width=True)
    with col_r:
        st.subheader("Engineering indicators")
        p_h2, p_o2 = reactant_partial_pressures_bar(conditions)
        table_rows = [
            ("Theoretical reversible cell voltage", f"{point['reversible_voltage_V']:.3f} V"),
            ("Hydrogen partial pressure", f"{p_h2:.3f} bar"),
            ("Oxygen partial pressure", f"{p_o2:.3f} bar"),
            ("Effective membrane conductivity", f"{point['membrane_conductivity_S_cm']:.4f} S/cm"),
            ("Membrane area-specific resistance", f"{point['membrane_asr_ohm_cm2']:.4f} Ω·cm²"),
            ("Activation loss at operating point", f"{point['activation_loss_V']:.3f} V"),
            ("Ohmic loss at operating point", f"{point['ohmic_loss_V']:.3f} V"),
            ("Transport loss at operating point", f"{point['transport_loss_V']:.3f} V"),
            ("Hydrogen consumed by stack", f"{point['hydrogen_consumption_g_h']:.2f} g/h" if point["operational"] else "—"),
            ("Hydrogen supplied at selected excess", f"{point['hydrogen_feed_g_h']:.2f} g/h" if point["operational"] else "—"),
            ("Oxidant supplied (dry basis)", f"{point['dry_oxidant_feed_mol_h']:.1f} mol/h" if point["operational"] else "—"),
            ("Modeled peak power density", f"{peak['power_density_W_cm2']:.3f} W/cm²" if peak["power_density_W_cm2"] is not None else "—"),
            ("Peak-power current density", f"{peak['current_density_A_cm2']:.3f} A/cm²" if peak["current_density_A_cm2"] is not None else "—"),
        ]
        st.dataframe(pd.DataFrame(table_rows, columns=["Indicator", "Value"]),
                     hide_index=True, use_container_width=True)
    st.markdown('<div class="fcm-note">Efficiency is a cell-voltage ratio on a hydrogen HHV basis. It excludes pumps, compressors, cooling, fuel losses and other balance-of-plant loads. Feed rates are stoichiometric estimates, not gas-flow or humidification system simulations.</div>', unsafe_allow_html=True)

with comparison_tab:
    st.subheader("How does membrane selection change performance?")
    st.write("Compare illustrative membrane-property scenarios under identical gas conditions and electrode assumptions. The current scenario can also be included.")
    available = ["Current scenario", *MEMBRANES.keys()]
    chosen = st.multiselect("Membranes to compare", available,
                            default=["Current scenario", "Thin / conductive", "Thick / resistive"],
                            max_selections=4)
    outcome = st.radio("Plot", ["Cell voltage", "Power density"], horizontal=True)
    if chosen:
        compare_cases = {label: membrane if label == "Current scenario" else MEMBRANES[label] for label in chosen}
        curves = {label: polarization_curve(j_values, spec, conditions, kinetics) for label, spec in compare_cases.items()}
        st.plotly_chart(comparison_chart(curves, outcome), use_container_width=True)
        rows = []
        for label, spec in compare_cases.items():
            results = stack_metrics(target_j, spec, conditions, kinetics)
            rows.append({
                "Membrane scenario": label,
                "Thickness (µm)": spec.thickness_um,
                "Reference σ (S/cm)": spec.conductivity_ref_s_cm,
                "Effective σ (S/cm)": round(results["membrane_conductivity_S_cm"], 4),
                "Membrane ASR (Ω·cm²)": round(results["membrane_asr_ohm_cm2"], 4),
                "Voltage at set current (V)": round(results["cell_voltage_V"], 3) if results["operational"] else None,
                "Power density (W/cm²)": round(results["power_density_W_cm2"], 3) if results["operational"] else None,
            })
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
        st.download_button(
            "Download comparison table (CSV)", data=pd.DataFrame(rows).to_csv(index=False).encode("utf-8"),
            file_name="fuelcell_mat_membrane_comparison.csv", mime="text/csv",
        )
    else:
        st.info("Select at least one membrane scenario to display a comparison.")
    st.caption("Preset labels describe hypothetical material properties, not independently tested products. This comparison isolates membrane conductivity and thickness only; durability, permeability and mechanical strength are not included.")

with sensitivity_tab:
    st.subheader("One-at-a-time sensitivity analysis")
    st.write("Change one parameter while holding the others constant at the values in the last submitted calculator run. The operating current density from that run remains fixed.")
    param = st.selectbox("Parameter to vary", list(SENSITIVITY_PARAMETERS))
    min_range, max_range, unit = SENSITIVITY_PARAMETERS[param]
    current_baseline = {
        "Membrane thickness": membrane.thickness_um,
        "Reference conductivity": membrane.conductivity_ref_s_cm,
        "Relative humidity (both feeds)": (conditions.anode_rh_pct + conditions.cathode_rh_pct) / 2,
        "Cell temperature": conditions.temperature_c,
    }[param]
    start_default = max(min_range, current_baseline * 0.6 if param != "Cell temperature" else current_baseline - 15)
    end_default = min(max_range, current_baseline * 1.4 if param != "Cell temperature" else current_baseline + 10)
    start, end = st.slider(
        "Parameter sweep range", min_value=float(min_range), max_value=float(max_range),
        value=(float(start_default), float(end_default)),
        step=0.001 if param == "Reference conductivity" else 1.0,
    )
    if start >= end:
        st.info("Widen the parameter range to run a sensitivity sweep.")
    else:
        sweep = sensitivity_study(param, np.linspace(start, end, 35), target_j, membrane, conditions, kinetics)
        sensitivity_outcome = st.radio("Sensitivity result", ["Cell voltage", "Stack power", "Membrane ASR"],
                                       horizontal=True)
        st.plotly_chart(sensitivity_chart(sweep, unit, sensitivity_outcome), use_container_width=True)
        st.download_button("Download sensitivity data (CSV)",
                           data=sweep.to_csv(index=False).encode("utf-8"),
                           file_name="fuelcell_mat_sensitivity.csv", mime="text/csv")
        if not sweep["operational"].all():
            st.warning("Some parameter choices have nonpositive predicted cell voltage; those operating outputs are intentionally left blank.")
    st.caption("Changing cell temperature affects the model's equilibrium potential, gas-water vapor pressures and membrane conductivity. Changing relative humidity changes membrane conductivity and gas partial pressures. These are model assumptions, not isolated experimental effects.")

with methods_tab:
    st.subheader("Model formulation")
    st.markdown("**1. Reversible voltage (ideal-gas Nernst approximation)**")
    st.latex(r"E_{rev}=1.229-0.00085(T-298.15)+\frac{RT}{2F}\ln\!\left[\left(\frac{p_{H_2}}{1\,\mathrm{bar}}\right)\left(\frac{p_{O_2}}{1\,\mathrm{bar}}\right)^{1/2}\right]")
    st.markdown("**2. Effective membrane conductivity and area-specific resistance**")
    st.latex(r"\sigma=\sigma_{ref}\exp\!\left[\frac{E_a}{R}\left(\frac{1}{T_{ref}}-\frac{1}{T}\right)\right]\left(\frac{RH_{an}+RH_{cat}}{200}\right)^m")
    st.latex(r"ASR_{mem}=\frac{t_{mem,\,cm}}{\sigma};\qquad\eta_{ohm}=j(ASR_{mem}+ASR_{other})")
    st.markdown("**3. Kinetic and mass-transport losses**")
    st.latex(r"\eta_{act}=\frac{RT}{\alpha n_{eff}F}\,\mathrm{asinh}\!\left(\frac{j}{2j_{0,eff}}\right)")
    st.latex(r"\eta_{tr}=-k_{tr}\frac{RT}{2F}\ln\left(1-\frac{j}{j_{lim}}\right)")
    st.markdown("**4. Predicted loaded voltage, power density and stack power**")
    st.latex(r"V=E_{rev}-\eta_{act}-\eta_{ohm}-\eta_{tr}")
    st.latex(r"P_A=jV;\qquad P_{stack}=N_{cells}A_{active}jV")
    st.markdown("**5. Hydrogen use and cell-level voltage efficiency**")
    st.latex(r"\dot{n}_{H_2,stack}=\frac{N_{cells}A_{active}j}{2F};\qquad\eta_{HHV,V}=\frac{V}{1.481}\times100\%")
    st.markdown("**Interpretation and validity**")
    st.markdown("""
- A simplified steady-state hydrogen/oxygen proton-exchange membrane fuel-cell model; pure hydrogen is assumed at the anode.
- The activation term is an **effective symmetric Butler–Volmer-style approximation**, not a resolved anode/cathode kinetic model. Its exchange-current value is an illustrative fit parameter.
- Membrane conductivity follows a **chosen Arrhenius × relative-humidity power law**, not the full Springer water-transport model or a manufacturer-measured material property.
- Membrane and gas feeds are assumed to have a uniform temperature. Relative humidity is specified separately at the anode and cathode; the model uses their arithmetic average to estimate membrane hydration.
- Gas partial pressures account for estimated water vapor but **not axial depletion, flooding, local oxygen transport or pressure losses**.
- Voltage results at or below zero are masked. Curves stop at 98% of the specified limiting current density; they do not resolve behavior at the transport singularity.
- Stack power assumes identical cells in series without wiring losses. Hydrogen consumption is based on Faraday's law and 100% Faradaic efficiency; any feed excess is reported separately.
- The plotted efficiency is based on cell voltage, not net system efficiency. Lifetime, cost, catalyst degradation, thermal management, creep and membrane gas crossover are outside scope.
""")
    st.info("Intended for educational parameter studies. Predictions are not calibrated against experimental polarization data and must not be used to size or certify real fuel-cell equipment.")
    st.markdown("**Technical references**")
    st.markdown("""
- [U.S. Department of Energy — Fuel Cell Basics](https://www.energy.gov/cmei/fuels/fuel-cell-basics)
- [U.S. Department of Energy / NETL — Fuel Cell Handbook, 7th edition](https://netl.doe.gov/sites/default/files/netl-file/FCHandbook7.pdf)
- [NIST Chemistry WebBook — Water Antoine equation parameters](https://webbook.nist.gov/cgi/cbook.cgi?ID=C7732185&Type=ANTOINE)
- [Review of proton-conductive membrane modelling (2020)](https://pmc.ncbi.nlm.nih.gov/articles/PMC7692588/)
""")

with exports_tab:
    st.subheader("Download reproducible results")
    st.write("The raw modeled curve, operating point and input assumptions are available for further calculation or plotting.")
    st.download_button("Download polarization curve (CSV)",
                       data=df.to_csv(index=False, float_format="%.8g").encode("utf-8"),
                       file_name="fuelcell_mat_polarization.csv", mime="text/csv",
                       use_container_width=True)
    payload = input_snapshot(membrane, conditions, kinetics)
    payload["selected_current_density_A_cm2"] = target_j
    payload["operating_point"] = point
    payload["maximum_modelled_power_point"] = peak
    st.download_button("Download input and results (JSON)",
                       data=json.dumps(payload, indent=2, allow_nan=False).encode("utf-8"),
                       file_name="fuelcell_mat_scenario.json", mime="application/json",
                       use_container_width=True)
    st.write("**Preview: polarization data**")
    st.dataframe(df.round(4), hide_index=True, use_container_width=True, height=300)
    st.caption("CSV/JSON exports are generated entirely from the last submitted calculator inputs. No simulated values are presented as laboratory measurements.")

st.divider()
st.caption("FuelCell-Mat · Calculator UI v1.1.0 · Model v1.0.0 · Educational membrane-performance exploration · Inputs and results are illustrative, not experimentally validated.")
