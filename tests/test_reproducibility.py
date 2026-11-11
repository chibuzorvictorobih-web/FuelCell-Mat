"""Reference-data, export and visualization regression checks."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from fuelcell_mat.charts import (
    comparison_chart, loss_chart, power_chart, sensitivity_chart, voltage_chart,
)
from fuelcell_mat.experiments import sensitivity_study
from fuelcell_mat.model import (
    Kinetics, Membrane, OperatingConditions, input_snapshot, maximum_power_point,
    polarization_curve, stack_metrics,
)

ROOT = Path(__file__).resolve().parents[1]


def test_reference_curve_matches_committed_csv():
    stored = pd.read_csv(ROOT / 'examples' / 'reference_polarization.csv')
    calculated = polarization_curve(
        stored['current_density_A_cm2'].to_numpy(), Membrane(),
        OperatingConditions(), Kinetics(),
    )
    assert list(stored.columns) == list(calculated.columns)
    for col in stored.select_dtypes(include='number').columns:
        np.testing.assert_allclose(
            stored[col].to_numpy(float), calculated[col].to_numpy(float),
            rtol=1e-6, atol=6e-8, equal_nan=True,
        )
    assert (stored['operational'].to_numpy() == calculated['operational'].to_numpy()).all()


def test_reference_json_matches_model():
    stored = json.loads((ROOT / 'examples' / 'reference_scenario.json').read_text())
    inputs = input_snapshot(Membrane(), OperatingConditions(), Kinetics())
    for key in ('model_version', 'membrane', 'operating_conditions', 'kinetics'):
        assert stored[key] == inputs[key]
    point = stack_metrics(1.0, Membrane(), OperatingConditions(), Kinetics())
    peak = maximum_power_point(Membrane(), OperatingConditions(), Kinetics())
    for key, value in point.items():
        if isinstance(value, float):
            assert stored['operating_point'][key] == pytest.approx(value)
        else:
            assert stored['operating_point'][key] == value
    for key, value in peak.items():
        assert stored['maximum_modelled_power_point'][key] == pytest.approx(value)


def test_operating_point_export_serializes_at_infeasible_parameters():
    membrane = Membrane(thickness_um=250, conductivity_ref_s_cm=0.005)
    conditions = OperatingConditions(anode_rh_pct=30, cathode_rh_pct=30)
    kinetics = Kinetics()
    payload = input_snapshot(membrane, conditions, kinetics)
    payload['operating_point'] = stack_metrics(1.0, membrane, conditions, kinetics)
    payload['maximum_modelled_power_point'] = maximum_power_point(membrane, conditions, kinetics)
    encoded = json.dumps(payload, allow_nan=False)
    assert json.loads(encoded)['operating_point']['cell_voltage_V'] is None


def test_chart_builders_return_serializable_figures():
    conditions, membrane, kinetics = OperatingConditions(), Membrane(), Kinetics()
    curve = polarization_curve(np.linspace(0, 1.7, 25), membrane, conditions, kinetics)
    sweep = sensitivity_study('Membrane thickness', [25, 50, 100], 1.0, membrane, conditions, kinetics)
    figures = [
        voltage_chart(curve, 1.0), power_chart(curve, 1.0), loss_chart(curve),
        comparison_chart({'Reference': curve}, 'Cell voltage'),
        sensitivity_chart(sweep, 'µm', 'Stack power'),
    ]
    for figure in figures:
        assert figure.data
        assert json.loads(figure.to_json())['data']
