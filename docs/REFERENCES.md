# Technical references

These sources provide background for PEM fuel-cell operating principles, polarization-loss decomposition, thermodynamic activities, water vapor pressure and membrane hydration. **They do not validate the particular numerical parameters selected for the illustrative scenarios**.

1. U.S. Department of Energy, [Fuel Cell Basics](https://www.energy.gov/cmei/fuels/fuel-cell-basics). Hydrogen/air PEM fuel-cell principles and electrochemistry.
2. U.S. Department of Energy, National Energy Technology Laboratory, [Fuel Cell Handbook, Seventh Edition](https://netl.doe.gov/sites/default/files/netl-file/FCHandbook7.pdf). Activation, ohmic and concentration polarization, Nernst potential, and fuel-cell system fundamentals.
3. National Institute of Standards and Technology, [Chemistry WebBook: Water — Antoine Equation Parameters](https://webbook.nist.gov/cgi/cbook.cgi?ID=C7732185&Type=ANTOINE). Includes the Stull (1947) correlation used in this model, in bar and kelvin.
4. [Modelling the Proton-Conductive Membrane in Practical Polymer Electrolyte Membrane Fuel Cell (PEMFC) Simulation: A Review](https://pmc.ncbi.nlm.nih.gov/articles/PMC7692588/), 2020. Background on membrane proton conductivity, water uptake and the limitations of reduced hydration models.
5. [Analytical modeling of PEM fuel cell i–V curve](https://www.sciencedirect.com/science/article/pii/S0960148110003319), 2011. Analytical current–voltage modeling and voltage-loss components.
6. U.S. Department of Energy, [Comparison of Fuel Cell Technologies](https://www.energy.gov/cmei/fuels/comparison-fuel-cell-technologies). Contextual fuel-cell performance benchmarks, **not calibration of the model**.

The code uses independent, documented model assumptions and illustrative reference-case coefficients. Do not interpret outputs as laboratory test results or reproduce fitted performance claims without appropriate experimental data.
