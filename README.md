# DORA - Development-Oriented Real-Time Analysis

DORA is a browser-based system for monitoring and basic visualization of GFDL-based CM4-class simulations.  The code is written in primarily in Python 3.x, making use of Flask and Jinja templating.

> Features:

- Project-based organization of experiments
- Plots and statistical comparisons of scalar diagnostics
- Parameter differences between experiments
- Model-model comparison plots
- Standard suite of ocean diagnostics

> External Dependencies

- [gfdlvitals](https://gfdlvitals.readthedocs.io/en/latest/) - Scalar diagnostic toolkit
- [OM4Labs](https://github.com/raphaeldussin/om4labs) - Plots for MOM6 model output
- [xoverturning](https://github.com/raphaeldussin/xoverturning) - Generic overturning routines
- [MOM6 Parameter Scanner](https://github.com/adcroft/MOM6_parameter_scanner) - Tool for parsing MOM6 and SIS2 parameter files

---
Dashboard is based on the open-source [Jinja Template](https://github.com/app-generator/jinja-template) [AdminLTE](https://appseed.us/adminlte) provided by AppSeed [Web App Generator](https://appseed.us/app-generator).
