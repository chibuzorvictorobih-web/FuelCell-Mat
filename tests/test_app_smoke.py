"""Exercise the calculator workflow and results with deterministic UI controls."""

from __future__ import annotations

import runpy
import sys
import types
from pathlib import Path

import pytest


class RenderStopped(Exception):
    """Represent Streamlit's normal script stop when no calculation exists."""


class DisplayStub(types.ModuleType):
    def __init__(self, submit=True):
        super().__init__("streamlit")
        self.session_state = {}
        self.submit = submit
        self.figures = 0
        self.downloads = 0
        self.messages = []
        self.button_labels = []
        self.section_labels = []
        self.metrics = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def set_page_config(self, **kwargs):
        assert kwargs["page_title"]

    def _control(self, key, fallback):
        if key:
            self.session_state.setdefault(key, fallback)
            return self.session_state[key]
        return fallback

    def selectbox(self, label, options, index=0, **kwargs):
        return self._control(kwargs.get("key"), options[index])

    def multiselect(self, label, options, default=None, **kwargs):
        return self._control(kwargs.get("key"), default or [])

    def radio(self, label, options, **kwargs):
        return self._control(kwargs.get("key"), options[0])

    def slider(self, label, *args, **kwargs):
        default = kwargs.get("value", args[2] if len(args) > 2 else None)
        return self._control(kwargs.get("key"), default)

    def number_input(self, label, *args, **kwargs):
        default = kwargs.get("value", args[2] if len(args) > 2 else None)
        return self._control(kwargs.get("key"), default)

    def form_submit_button(self, label, **kwargs):
        self.button_labels.append(label)
        return self.submit

    def form(self, *args, **kwargs):
        return self

    def expander(self, *args, **kwargs):
        return self

    def columns(self, count):
        return [self] * (len(count) if isinstance(count, (list, tuple)) else count)

    def tabs(self, titles):
        return [self for _ in titles]

    def plotly_chart(self, figure, **kwargs):
        assert figure.data
        self.figures += 1

    def download_button(self, label, data, **kwargs):
        assert data
        self.downloads += 1

    def header(self, label, **kwargs):
        self.section_labels.append(label)

    def metric(self, label, value, **kwargs):
        self.metrics.append((label, value))

    def error(self, message, **kwargs):
        self.messages.append(message)

    def stop(self):
        raise RenderStopped

    def __getattr__(self, name):
        if name in {
            "markdown", "title", "caption", "subheader", "divider", "write",
            "dataframe", "warning", "info", "latex",
        }:
            return lambda *args, **kwargs: None
        raise AttributeError(name)


APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


def run_app(monkeypatch, display):
    monkeypatch.setitem(sys.modules, "streamlit", display)
    runpy.run_path(str(APP_PATH), run_name="__main__")


def test_opening_screen_has_calculator_and_waits_for_submission(monkeypatch):
    display = DisplayStub(submit=False)
    with pytest.raises(RenderStopped):
        run_app(monkeypatch, display)
    assert "Calculator" in display.section_labels
    assert "Calculate fuel-cell performance" in display.button_labels
    assert display.figures == 0
    assert display.downloads == 0
    assert "fcm_calculated_inputs" not in display.session_state


def test_submit_calculator_displays_results_charts_and_exports(monkeypatch):
    display = DisplayStub(submit=True)
    run_app(monkeypatch, display)
    assert "Calculator" in display.section_labels
    assert "Calculate fuel-cell performance" in display.button_labels
    assert display.figures == 5
    assert display.downloads == 4
    assert len(display.metrics) == 4
    assert display.metrics[0][0] == "Cell voltage"
    assert not display.messages


def test_invalid_target_above_limiting_current_is_rejected(monkeypatch):
    display = DisplayStub(submit=True)
    display.session_state["fcm_target_j"] = 2.0
    with pytest.raises(RenderStopped):
        run_app(monkeypatch, display)
    assert any("Cannot calculate" in m for m in display.messages)
    assert "fcm_calculated_inputs" not in display.session_state


def test_results_are_frozen_until_calculate_pressed_again(monkeypatch):
    display = DisplayStub(submit=True)
    run_app(monkeypatch, display)
    old_membrane = display.session_state["fcm_calculated_inputs"][0]
    assert old_membrane.thickness_um == 50

    # Changing input does not modify the last submitted calculation.
    display.submit = False
    display.session_state["fcm_thickness"] = 70.0
    run_app(monkeypatch, display)
    assert display.session_state["fcm_calculated_inputs"][0].thickness_um == 50

    display.submit = True
    run_app(monkeypatch, display)
    assert display.session_state["fcm_calculated_inputs"][0].thickness_um == 70


def test_recalculation_updates_physical_output(monkeypatch):
    display = DisplayStub(submit=True)
    run_app(monkeypatch, display)
    baseline_voltage = float(display.metrics[0][1].split()[0])

    display.session_state["fcm_thickness"] = 125.0
    display.metrics.clear()
    run_app(monkeypatch, display)
    thicker_voltage = float(display.metrics[0][1].split()[0])
    assert thicker_voltage < baseline_voltage


def test_invalid_new_submission_removes_previous_results(monkeypatch):
    display = DisplayStub(submit=True)
    run_app(monkeypatch, display)
    assert "fcm_calculated_inputs" in display.session_state
    display.session_state["fcm_target_j"] = 2.0
    with pytest.raises(RenderStopped):
        run_app(monkeypatch, display)
    assert "fcm_calculated_inputs" not in display.session_state
    assert any("Cannot calculate" in m for m in display.messages)
