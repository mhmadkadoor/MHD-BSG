# EV connector contact-resistance anomaly simulator

This small Python simulator models an EV charging session where the vehicle-side
connector has increased contact resistance (for example, iron used instead of
copper). It demonstrates how I2R losses produce rapid heating at the connector,
how the station can derate current stepwise, and how the session is stopped if
critical temperature thresholds are exceeded.

Files added
- `sim/ev_charging_sim.py`: main simulator. Run with Python 3.8+.

Quick run

Open a PowerShell terminal in the repository root and run:

```powershell
python -m sim.ev_charging_sim --scenario iron --duration-min 20
```

Notes
- The script prints logs to stdout and writes `sim/ev_simulation.log` with the
  same lines. The model is simplified and tuned for demonstration rather than
  precise thermal/EM simulation. Tweak contact resistance and thermal params in
  `build_scenario()` to experiment.

Suggested next steps
- Add small unit tests validating derate and stop behavior.
- Add plotting of temperature vs time for post-run analysis.
