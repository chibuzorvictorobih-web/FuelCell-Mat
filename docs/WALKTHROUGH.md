# FuelCell-Mat guided walkthrough

This guide shows reproducible demonstrations for reviewing the computational model. All outcomes are from **simulated illustrative inputs**, not fuel-cell measurements.

## Experiment 1 — Establish a baseline

1. Open the **Calculator** section at the top of the app.
2. Keep the reference membrane: 50 µm thick and 0.10 S/cm reference ionic conductivity.
3. Use 80 °C, 1.5 bar absolute at both electrodes, 90% relative humidity at both electrodes, and air (21% dry oxygen).
4. Set the operating current density to 1.0 A/cm² with 100 cm² active area and 40 series-connected cells.
5. Press **Calculate fuel-cell performance**. Record the cell voltage and stack power from **Calculator results**. Open **Performance curves** to inspect activation, ohmic and transport losses.

Expected results for model version 1.0.0 (approximately):

| Output | Result |
|---|---:|
| Reversible cell voltage | 1.172 V |
| Predicted loaded cell voltage | 0.736 V |
| Activation loss | 0.294 V |
| Ohmic loss | 0.099 V |
| Transport loss | 0.043 V |
| Power density | 0.736 W/cm² |
| Stack electric power | 2.945 kW |
| Hydrogen consumption | 150.43 g/h |
| HHV-based cell-voltage efficiency | 49.7% |

The output is a model reference point, not a measured PEMFC benchmark.

## Experiment 2 — Compare membrane designs

1. After completing and submitting the baseline calculation, open **Materials comparison**.
2. Choose **Reference membrane**, **Thin / conductive** and **Thick / resistive**.
3. Keep the current density at 1.0 A/cm² and all gas/kinetic settings unchanged.
4. Switch between cell voltage and power-density graphs.

Expected modeled values at the fixed current density:

| Illustrative scenario | Thickness | Effective membrane ASR | Cell voltage |
|---|---:|---:|---:|
| Reference membrane | 50 µm | 0.0586 Ω·cm² | 0.736 V |
| Thin / conductive | 25 µm | 0.0205 Ω·cm² | 0.774 V |
| Thick / resistive | 125 µm | 0.2325 Ω·cm² | 0.562 V |

**Interpretation:** the favorable thin/conductive scenario decreases membrane ohmic losses. This does not prove it is the best real material: durability, crossover, dimensional stability, cost and other application constraints are not modeled.

## Experiment 3 — Humidity effects

1. After completing and submitting the baseline calculation, open **Sensitivity study**.
2. Select **Relative humidity (both feeds)** and keep the 1.0 A/cm² operating point.
3. Sweep 50–100% RH.
4. Inspect cell voltage and membrane area-specific resistance separately.

For the reference membrane, example model endpoints are:

| Equal anode/cathode RH | Effective membrane ASR | Cell voltage |
|---|---:|---:|
| 50% | 0.1414 Ω·cm² | 0.657 V |
| 75% | 0.0770 Ω·cm² | 0.719 V |
| 100% | 0.0500 Ω·cm² | 0.744 V |

**Interpretation:** greater assumed hydration increases conductivity and reduces ohmic loss in this simplified model. In real cells, additional phenomena (including flooding and reactant transport) may reverse a simple monotonic relationship.

## Experiment 4 — Share reproducible inputs

1. Open **Export results** and save the polarization CSV.
2. Save the JSON scenario record, including membrane and operating assumptions.
3. To reproduce a chart, apply the stored inputs in the **Calculator** and press **Calculate fuel-cell performance** before comparing with the stored CSV.

## Further research questions

- How does a conductivity-versus-thickness trade-off affect power output at constant current density?
- Which modeled loss dominates as the load approaches its transport limit?
- How does the reference operating temperature affect both reversible voltage and ion conduction?
- How could independently measured conductivity and polarization data be used to fit and validate these coefficients?

For exact definitions and scope, see [MODEL.md](MODEL.md) and [VALIDATION.md](VALIDATION.md).
