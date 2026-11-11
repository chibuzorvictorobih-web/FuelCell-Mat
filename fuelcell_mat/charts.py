"""Plotly chart builders for interactive exploration."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

COLOR_VOLTAGE = "#0E7490"
COLOR_POWER = "#D97706"
COLOR_ACTIVATION = "#B45309"
COLOR_OHMIC = "#2563EB"
COLOR_TRANSPORT = "#7C3AED"


def _base(fig: go.Figure, x_label: str, y_label: str, height: int = 410) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=38, b=12),
        template="plotly_white",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        xaxis_title=x_label,
        yaxis_title=y_label,
        font=dict(family="Arial, sans-serif", size=12),
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(30,41,59,0.08)", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(30,41,59,0.08)", zeroline=False)
    return fig


def voltage_chart(df: pd.DataFrame, selected_j: float) -> go.Figure:
    fig = go.Figure()
    x = df["current_density_A_cm2"]
    fig.add_trace(go.Scatter(x=x, y=df["reversible_voltage_V"], name="Reversible (ideal)",
                             mode="lines", line=dict(color="#94A3B8", dash="dash", width=2)))
    fig.add_trace(go.Scatter(x=x, y=df["predicted_voltage_V"], name="Predicted cell", mode="lines",
                             line=dict(color=COLOR_VOLTAGE, width=3)))
    fig.add_vline(x=selected_j, line_color="#64748B", line_dash="dot", line_width=1)
    fig.update_yaxes(rangemode="tozero")
    return _base(fig, "Current density (A/cm²)", "Cell voltage (V)")


def power_chart(df: pd.DataFrame, selected_j: float) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["current_density_A_cm2"], y=df["power_density_W_cm2"],
                             name="Power density", mode="lines", line=dict(color=COLOR_POWER, width=3),
                             fill="tozeroy", fillcolor="rgba(217,119,6,.09)"))
    fig.add_vline(x=selected_j, line_color="#64748B", line_dash="dot", line_width=1)
    fig.update_yaxes(rangemode="tozero")
    return _base(fig, "Current density (A/cm²)", "Power density (W/cm²)")


def loss_chart(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for column, label, color in [
        ("activation_loss_V", "Activation", COLOR_ACTIVATION),
        ("ohmic_loss_V", "Ohmic", COLOR_OHMIC),
        ("transport_loss_V", "Mass transport", COLOR_TRANSPORT),
    ]:
        fig.add_trace(go.Scatter(x=df["current_density_A_cm2"], y=df[column], name=label,
                                 stackgroup="one", mode="lines", line=dict(color=color, width=1.5)))
    return _base(fig, "Current density (A/cm²)", "Voltage loss (V)")


def comparison_chart(comparison: dict[str, pd.DataFrame], outcome: str) -> go.Figure:
    fields = {
        "Cell voltage": ("predicted_voltage_V", "Cell voltage (V)"),
        "Power density": ("power_density_W_cm2", "Power density (W/cm²)"),
    }
    column, y_label = fields[outcome]
    fig = go.Figure()
    colors = ["#0E7490", "#EA580C", "#7C3AED", "#16A34A"]
    for (label, df), color in zip(comparison.items(), colors):
        fig.add_trace(go.Scatter(x=df["current_density_A_cm2"], y=df[column],
                                 name=label, mode="lines", line=dict(width=2.6, color=color)))
    fig.update_yaxes(rangemode="tozero")
    return _base(fig, "Current density (A/cm²)", y_label, 440)


def sensitivity_chart(df: pd.DataFrame, unit: str, outcome: str) -> go.Figure:
    fields = {
        "Cell voltage": ("cell_voltage_V", "Cell voltage (V)"),
        "Stack power": ("stack_power_W", "Stack power (W)"),
        "Membrane ASR": ("membrane_asr_ohm_cm2", "Membrane ASR (Ω·cm²)"),
    }
    column, y_label = fields[outcome]
    fig = go.Figure(go.Scatter(
        x=df["parameter_value"], y=df[column], mode="lines+markers",
        marker=dict(size=4), name=outcome,
        line=dict(width=3, color=COLOR_VOLTAGE),
    ))
    fig.update_yaxes(rangemode="tozero")
    return _base(fig, f"{df.iloc[0]['parameter']} ({unit})", y_label, 420)
