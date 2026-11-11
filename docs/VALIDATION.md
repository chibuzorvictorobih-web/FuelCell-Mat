# Computational checks and model limitations

## Reproducibility procedure

From the repository root, install dependencies and run:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

To check the interface:

```bash
python -m streamlit run app.py
```

Use the reference controls (80 °C, 1.5 bar at each electrode, 90% RH, reference membrane, j = 1 A/cm²) and press **Calculate fuel-cell performance**. The results are reproducible because no random inputs or external services are used.

## Automated test coverage

| Group | Check | Scientific / software rationale |
|---|---|---|
| Water properties | 80 °C saturated vapor pressure ≈ 0.474 bar | Engineering reference-point sanity check |
| Gas composition | Oxygen pressure uses dry oxygen fraction and vapor subtraction | Unit and activity consistency |
| Equilibrium | Increasing oxygen mole fraction increases E_rev at fixed conditions | Nernst response |
| Materials | Higher RH or temperature increases modeled conductivity | Directional Arrhenius/hydration check |
| Materials | Doubling thickness doubles membrane ASR | ASR dimensions |
| Polarization | Open-circuit activation, ohmic and transport losses are zero | Zero-current boundary |
| Polarization | Voltage decreases as current density increases (reference case) | Expected polarization shape |
| Polarization | Thicker membrane reduces cell voltage at fixed current | Expected ohmic change |
| Stack | Hydrogen consumption matches Faraday's law for series cells | Charge conservation |
| Stack | Power = voltage × cell current × cell count | Unit and stack consistency |
| Model range | Invalid current and inputs fail explicitly | Prevents singularity and silent extrapolation |
| Physical envelope | Nonpositive-voltage predictions are masked | Avoids presenting impossible electrical operating points |
| Comparison | Thin/conductive preset outperforms thick/resistive at fixed current | Isolated membrane influence |
| Data integrity | Committed reference CSV and JSON match recomputed outputs | Reproducible published example |
| Exports | JSON serializes valid and infeasible operating points | Portable, machine-readable results |
| Visualizations | Five Plotly chart functions generate serializable figures | Catch plotting regressions |
| Calculator workflow | Opening form, button submission, invalid current limit and last-submitted-state handling | Catch interface-code regressions without requiring a running browser |
| Sensitivity | Thickness and hydration trends | Sweep reproducibility |

## Interpretation

These are **unit, boundary, directional, consistency, export and interface-code smoke tests**, not experimental validation. Passing them does not establish quantitative predictive accuracy for a particular membrane or stack. Measured current–voltage data, with specified materials and operating conditions, would be needed for model calibration and residual-error analysis.

Potential extensions: simultaneous fitting of exchange current, ASR and mass-transfer terms to laboratory data; gas-crossover effects; explicit membrane water-content models; spatial temperature and humidity fields; uncertainty intervals; membrane tensile and durability properties.
