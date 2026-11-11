# FuelCell-Mat

**Interactive proton-exchange membrane fuel-cell performance simulator**

FuelCell-Mat is a reproducible computational engineering portfolio project exploring how **membrane thickness, ionic conductivity, temperature and reactant humidity** influence the modeled electrical performance of a hydrogen/oxygen polymer-electrolyte membrane (PEM) fuel cell.

Built with **Python, Streamlit, NumPy, Pandas and Plotly**. No database, credentials or external API are required.

## Features

- **Dedicated, button-driven calculator:** enter membrane thickness, conductivity, temperature, current density, gas pressure and humidity in the main page; press **Calculate fuel-cell performance** for reversible potential, voltage losses, loaded voltage and power density.
- **Membrane-property experiments:** compare reference, thin/conductive and thick/resistive illustrative material scenarios.
- **Sensitivity analysis:** sweep membrane thickness, conductivity, gas humidification or operating temperature at a fixed current density.
- **Stack estimates:** series-stack voltage and power, hydrogen consumption, feed requirements and cell-level voltage efficiency.
- **Explorable visualizations:** polarization curves, power-density curves and voltage-loss decomposition.
- **Reproducible exports:** CSV outputs and JSON records of inputs plus selected operating-point results.
- **Computational tests:** unit, boundary, physics-direction, reproducibility, export, chart-generation and interface smoke checks.

## Quick start

Use Python 3.11 or newer (Python 3.12 is recommended for cloud deployment).

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open the local URL reported by Streamlit (usually `http://localhost:8501`). The **Calculator** section appears at the top of the page. Select a membrane starting point, review the six core inputs, optionally expand **Advanced settings**, and press **Calculate fuel-cell performance**. Results and five analysis tabs appear beneath the form. Editing a value does not recalculate until you press the button again. For a hosted version, see [deployment instructions](docs/DEPLOYMENT.md).

## Reference operating scenario

| Input | Value |
|---|---:|
| Cell temperature | 80 °C |
| Pressure, anode / cathode | 1.5 / 1.5 bar absolute |
| Relative humidity, anode / cathode | 90 / 90% |
| Dry oxidant | Air (21% oxygen) |
| Reference membrane thickness | 50 µm |
| Reference conductivity (80 °C, 100% RH) | 0.10 S/cm |
| Current density | 1.0 A/cm² |
| Effective exchange current density | 0.008 A/cm² |
| Limiting current density | 1.8 A/cm² |
| Cell area × cells in series | 100 cm² × 40 |

The numerical parameters are **illustrative modeling choices** and **not measured material properties**. The example output in `examples/` is generated from the same default model.

## Project structure

```text
FuelCell-Mat/
├── app.py                      # Streamlit interface
├── fuelcell_mat/
│   ├── __init__.py
│   ├── model.py                # Core physics and stack calculations
│   ├── presets.py              # Illustrative membrane scenarios
│   ├── experiments.py          # Sensitivity sweeps
│   └── charts.py               # Interactive Plotly graphics
├── tests/
│   ├── test_model.py
│   ├── test_experiments.py
│   ├── test_reproducibility.py
│   └── test_app_smoke.py
├── examples/
│   ├── reference_polarization.csv
│   └── reference_scenario.json
├── docs/
│   ├── MODEL.md
│   ├── VALIDATION.md
│   ├── WALKTHROUGH.md
│   ├── REFERENCES.md
│   └── DEPLOYMENT.md
├── .streamlit/config.toml
├── requirements.txt
├── requirements-dev.txt
├── .gitignore
└── LICENSE
```

## Model approach and responsibility

The cell potential is calculated from an idealized Nernst voltage minus three modeled losses:

\[
V=E_{rev}-\eta_{activation}-\eta_{ohmic}-\eta_{transport}.
\]

The membrane conductivity is an empirical Arrhenius × relative-humidity approximation. The activation and transport relations are reduced, effective representations rather than full electrode-scale physics. The code masks nonpositive predicted voltage and restricts current density to below the chosen transport limit.

**Educational scope:** results are simulated, not laboratory measurements. The model has not been calibrated or validated against a specific commercial fuel cell. It is unsuitable for equipment specification, procurement decisions, safety engineering or warranty predictions. The displayed efficiency is a **cell-level voltage ratio**, not net system efficiency.

Read the [complete equations and assumptions](docs/MODEL.md), [guided walkthrough](docs/WALKTHROUGH.md), [test strategy](docs/VALIDATION.md), and [technical references](docs/REFERENCES.md).

## Run checks

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

## Deployment

For GitHub upload and Streamlit Community Cloud instructions, use [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md). The app entry point is **`app.py`**.

## License

MIT — see [LICENSE](LICENSE).
