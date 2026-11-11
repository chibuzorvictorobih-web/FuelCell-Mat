"""Illustrative membrane scenarios; not commercial material specifications."""

from fuelcell_mat.model import Membrane

MEMBRANES: dict[str, Membrane] = {
    "Reference membrane": Membrane(
        name="Reference membrane", thickness_um=50, conductivity_ref_s_cm=0.10,
        activation_energy_kj_mol=12, hydration_exponent=1.5,
    ),
    "Thin / conductive": Membrane(
        name="Thin / conductive", thickness_um=25, conductivity_ref_s_cm=0.14,
        activation_energy_kj_mol=11, hydration_exponent=1.3,
    ),
    "Thick / resistive": Membrane(
        name="Thick / resistive", thickness_um=125, conductivity_ref_s_cm=0.065,
        activation_energy_kj_mol=15, hydration_exponent=1.8,
    ),
}
