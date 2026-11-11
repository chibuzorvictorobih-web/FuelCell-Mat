# Model equations and assumptions

FuelCell-Mat implements a simplified, **steady-state hydrogen/air proton-exchange membrane fuel-cell (PEMFC)** polarization model. It is intended for exploratory parameter studies of membrane thickness, conductivity, hydration and operating conditions. None of the membrane-property scenarios are claimed to represent measured commercial materials.

## Inputs and units

| Quantity | Code name | Unit | Reference case |
|---|---|---|---:|
| Cell temperature | `temperature_c` | °C | 80 |
| Anode / cathode pressure | `anode_pressure_bar`, `cathode_pressure_bar` | bar absolute | 1.5 / 1.5 |
| Anode / cathode gas relative humidity | `anode_rh_pct`, `cathode_rh_pct` | % | 90 / 90 |
| Oxygen mole fraction in dry oxidant | `oxygen_fraction_dry` | 1 | 0.21 |
| Membrane thickness | `thickness_um` | µm | 50 |
| Membrane reference conductivity | `conductivity_ref_s_cm` | S/cm | 0.10 |
| Reference temperature | `reference_temp_c` | °C | 80 |
| Conductivity activation energy | `activation_energy_kj_mol` | kJ/mol | 12 |
| Hydration exponent | `hydration_exponent` | 1 | 1.5 |
| Effective exchange current | `effective_exchange_current_a_cm2` | A/cm² | 0.008 |
| Effective transfer coefficient | `charge_transfer_coefficient` | 1 | 0.5 |
| Effective kinetic electron number | `effective_electrons` | 1 | 1 |
| Limiting current density | `limiting_current_a_cm2` | A/cm² | 1.8 |
| Transport scale factor | `transport_multiplier` | 1 | 3.5 |
| Non-membrane area-specific resistance | `other_asr_ohm_cm2` | Ω·cm² | 0.04 |
| Active area per cell | `active_area_cm2` | cm² | 100 |
| Number of cells in series | `cell_count` | 1 | 40 |
| Hydrogen / oxidant inlet stoichiometry | `hydrogen_feed_stoich`, `air_feed_stoich` | 1 | 1.5 / 2.0 |

The reference conductivity is defined at **80 °C and 100% RH**, whereas the reference operating case has 90% RH in each gas feed. The effective kinetic electron number is **not** the same as the stoichiometric number of two electrons per hydrogen molecule; it is a phenomenological fitting parameter.

## Thermodynamic reversible potential

For the overall reaction H₂ + ½ O₂ → H₂O(l), with ideal-gas reactants and unit liquid-water activity:

\[
E_{rev}=1.229-0.00085(T-298.15)+\frac{RT}{2F}\ln\left[\left(\frac{p_{H_2}}{1\,\mathrm{bar}}\right)\sqrt{\frac{p_{O_2}}{1\,\mathrm{bar}}}\right]
\]

where T is in kelvin, R = 8.314462618 J/(mol·K), and F = 96485.33212 C/mol. The 0.00085 V/K standard-voltage temperature slope is a constant approximation in this temperature range.

Anode pure hydrogen and cathode oxygen/neutral gas are assumed. Water vapor occupies a fraction of each feed:

\[
p_{H_2}=P_a-(RH_a/100)p_{sat}(T),\qquad
p_{O_2}=x_{O_2,dry}\,[P_c-(RH_c/100)p_{sat}(T)].
\]

The NIST Stull (1947) Antoine equation for water is used across the model's 50–90 °C temperature range (the equation's cited range is 255.9–373 K):

\[
\log_{10}(p_{sat}/\mathrm{bar})=4.6543-\frac{1435.264}{T-64.848}.
\]

## Effective membrane conductivity and resistance

\[
\sigma(T,RH)=\sigma_{ref}\,\exp\left[\frac{E_a}{R}\left(\frac{1}{T_{ref}}-\frac{1}{T}\right)\right]\,\left(\frac{RH_a+RH_c}{200}\right)^m
\]

\[
ASR_{mem}=\frac{t_{mem,cm}}{\sigma},\qquad
ASR_{total}=ASR_{mem}+ASR_{other}.
\]

The membrane is treated as uniform, and gas feed RH is used as a proxy for membrane hydration. This Arrhenius × power-law relationship is a deliberately reduced empirical scenario model, **not** the full Springer–Zawodzinski–Gottesfeld ion/water transport model. A 50 µm membrane is 0.005 cm thick; this conversion is included explicitly.

## Activation, ohmic and transport losses

A symmetric Butler–Volmer-inspired inverse-hyperbolic-sine approximation is used:

\[
\eta_{act}=\frac{RT}{\alpha\,n_{eff}F}\;\operatorname{asinh}\left(\frac{j}{2j_{0,eff}}\right)
\]

The form is exactly consistent with a symmetric Butler–Volmer relation for α = 0.5, and is treated as an empirical approximation when α differs from 0.5. The single effective exchange-current parameter represents the combined observed kinetics, not separately identified anode and cathode catalysts. It is not a measured intrinsic ORR exchange current.

\[
\eta_{ohm}=j\,ASR_{total}
\]

\[
\eta_{tr}=-k_{tr}\frac{RT}{2F}\ln\left(1-\frac{j}{j_{lim}}\right).
\]

The transport multiplier scales the limiting-current logarithm empirically. The limiting current is held fixed across temperature, humidity and oxygen-composition sweeps. This is an approximation; real limiting current depends on gas supply and transport.

\[
V=E_{rev}-\eta_{act}-\eta_{ohm}-\eta_{tr},\qquad P_A=jV.
\]

Only current densities satisfying **0 ≤ j < j_lim** are evaluated. Curves stop at 98% of j_lim. Where the modeled raw cell voltage becomes nonpositive, loaded voltage and power are masked (shown as unavailable), not displayed as valid zero-power operating points.

## Stack power, hydrogen flow, and efficiency

For N series-connected identical cells with active area A per cell:

\[
I=jA,\quad V_{stack}=NV,\quad P_{stack}=NVI.
\]

Assuming 100% Faradaic efficiency:

\[
\dot{n}_{H_2,consumed}=\frac{NI}{2F},\quad
\dot{n}_{O_2,consumed}=\frac{NI}{4F}.
\]

Hydrogen consumption in g/h multiplies H₂ mol/s by 2.01588 g/mol and 3600 s/h. Inlet flow estimates apply the specified stoichiometric multipliers; oxidant feed is divided by dry oxygen mole fraction. No volumetric gas flow or inlet humidifier model is included.

Ideal **cell-voltage** efficiency equivalents using hydrogen at reference heating values:

\[
\eta_{HHV,V}=V/1.481,\qquad \eta_{LHV,V}=V/1.253.
\]

These are not net system efficiencies; no blower, cooling, control, compression, DC/DC, fuel utilization or transient loss is deducted. At open circuit, efficiency is undefined for electrical power output and is omitted.

## Scope boundaries

- Homogeneous temperature, pressure and current density; no channel-by-channel or multiphase transport.
- No catalyst-specific microkinetics, crossover, degradation, membrane stress, water flooding or dry-out physics.
- No lifetime, safety-certification or component-sizing capability.
- Materials scenarios are hypothetical combinations of thickness and conductivity, not rankings of measured products.
- Inlet RH changes alter both the estimated conductivity and reactant partial pressures; the effect is not exclusively materials-driven.
- Stack cells are identical; no cell-to-cell variability or interconnect losses.

See [VALIDATION.md](VALIDATION.md) for the test strategy and [REFERENCES.md](REFERENCES.md) for technical sources.
