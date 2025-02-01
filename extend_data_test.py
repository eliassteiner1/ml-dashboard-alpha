# from dash import Dash, dcc, html, Input, Output, no_update
# import plotly.graph_objects as go
# import numpy as np
# import time

# app = Dash(__name__)

# # Create figure using Scattergl
# fig = go.Figure()
# fig.add_trace(go.Scattergl(x=[], y=[], mode="lines", marker=dict(size=5, color="red")))

# app.layout = html.Div([
#     dcc.Graph(id="graph", figure=fig),
#     html.Button("Start", id="start-btn"),
#     dcc.Interval(id="interval", interval=10, n_intervals=0, disabled=True),  # 10 updates/sec
# ])

# @app.callback(Output("interval", "disabled"), Input("start-btn", "n_clicks"))
# def start_simulation(n_clicks):
#     return False if n_clicks else True

# @app.callback(Output("graph", "extendData"), Input("interval", "n_intervals"))
# def update_graph(n_intervals):
#     if n_intervals:
#         new_x = [time.time()]
#         new_y = [np.random.randn()]
#         return {"x": [new_x], "y": [new_y]}, [0]  # Append to trace 0
#     return no_update

# if __name__ == "__main__":
#     app.run_server(debug=True)










from dash import Dash, dcc, html, Input, Output, no_update
import plotly.graph_objects as go
import numpy as np
import time
# from dash_extensions.enrich import DashProxy, Trigger

# Create the Dash app
app = Dash(__name__)

# Initial figure with one empty trace
fig = go.Figure()
fig.add_trace(go.Scatter(x=[None], y=[None], mode="lines", name="sin"))
fig.add_trace(go.Scatter(x=[None], y=[None], mode="lines", name="cos"))

# App layout
app.layout = html.Div([
    dcc.Graph(id="graph", figure=fig),
    html.Button("Start Simulation", id="start-btn"),
    dcc.Interval(id="interval", interval=10, n_intervals=0, disabled=True),  
])

# Enable the interval when the button is clicked
@app.callback(
    Output("interval", "disabled"),
    Input("start-btn", "n_clicks"),
)
def start_simulation(n_clicks):
    if n_clicks:
        return False  # Enable interval
    return True  # Keep disabled

# Extend data on the graph
@app.callback(
    Output("graph", "extendData"),
    Input("interval", "n_intervals"),  # Triggered every interval
)
def update_graph(n_intervals):
    if n_intervals:
        # Generate new data
        
        x_new_1 = [time.time()]  # Current time as x-axis value
        y_new_1 = [np.sin(x_new_1[0])]  # Simulated data for y-axis
        
        x_new_2 = [time.time()]
        y_new_2 = [np.cos(x_new_2[0])]
        
        # "x" list of lists [[data for t1], [data for t2]]
        # "y" list of lists [[data for t1], [data for t2]]
        # second part: [list of trace indices]
        return {"x": [x_new_1, x_new_2], "y": [y_new_1, y_new_2]}, [0, 1]  # Append to trace 0
    return no_update

# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
