from dash_plotter import DashPlotter
import time

PLOTTER = DashPlotter()
PLOTTER.run_script()

print("doing more work!")
print("and more")
time.sleep(1)

PLOTTER.run_script_spin()