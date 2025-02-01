### IMPORTS ###
########################################################################################################################
# standard library imports
import os
import sys
import threading
import time
from   collections import deque
# third-party library imports
import numpy as np
import torch
from dash import Dash, Input, Output, State, dcc, html, no_update
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.subplots import make_subplots
# local library imports
from ml_dashboard.utils import adjust_alpha
from ml_dashboard.components import make_graphcard, make_pcacard, make_infocard
from ml_dashboard.components import make_flexgraph, make_pcagraph, update_flexgraph, update_pcagraph

"""note on axis resetting with double click: the implementation is actually buggy and doesn't work reliable. In short, the fix is to either use autorangeoptions_minallowed / autorangeoptions_maxallowed where applicable. The second fix, is to return not the figure in the callback function for updating the plot, but also the parent container, e.g. actually piece together the dcc.Graph object and return this. This actually then works as intended!"""


class DashPlotter:
    
    def __init__(self, setup_options: dict):
        
        #TODO read in setup options dict and SANITIZE!
        # best only on non-subplot. not more than one best
        self._setup_options = setup_options
        
        self._store  = self._make_store()
        self._n2t    = { # links a unique identifier to the respective trace number for each trace
                "g1": {},
                "g2": {},
                "g3": {},
                "g4": {},
            } 
        
        self._graph1 = make_flexgraph(self._store, self._n2t, opt = self._setup_options["graph1"], graph = 1)
        self._graph2 = make_flexgraph(self._store, self._n2t, opt = self._setup_options["graph2"], graph = 2)
        self._graph3 = make_flexgraph(self._store, self._n2t, opt = self._setup_options["graph3"], graph = 3)
        self._graph4 = make_pcagraph (self._store, self._n2t, opt = self._setup_options["graph4"])

        self._app    = self._make_app()
    
    def _make_store(self):
        
        # add graph 1-3
        store = {}
        j, k  = 1, 1
        for keyJ in self._setup_options.keys():
            if "graph4" in keyJ:
                continue # skip the graph4 since its store is different
            for keyK in self._setup_options[keyJ].keys():
                if "trace" not in keyK:
                    continue # skipt the "options" part for each graph
                # all the data needs to have a "None" so that the legends show up even when data is empty
                store[f"g{j}_t{k}_x"]    = [None]
                store[f"g{j}_t{k}_y"]    = [None]
                store[f"g{j}_t{k}_ymin"] = 0
                store[f"g{j}_t{k}_ymax"] = 0
                
                if self._setup_options[keyJ][keyK]["E"] is True:
                    store[f"g{j}_t{k}_lo"] = [None]
                    store[f"g{j}_t{k}_hi"] = [None]

                k +=1
            k  = 1
            j += 1
        
        # add graph 4
        n_steps    = self._setup_options["graph4"]["options"]["n_steps"]
        resolution = self._setup_options["graph4"]["options"]["LL_resol"]
        n_pvalues  = self._setup_options["graph4"]["options"]["n_pvalues"]
        store[f"g{4}_LL_x"] = np.linspace(-1, 1, resolution)
        store[f"g{4}_LL_y"] = np.linspace(-1, 1, resolution)
        store[f"g{4}_LL_z"] = np.ones((n_steps, resolution, resolution))
        
        store[f"g{4}_PV_x"]       = np.zeros((n_steps, n_pvalues))
        store[f"g{4}_PV_x"][1, 0] = 1 # this one will always be one!
        store[f"g{4}_PV_y"]       = np.linspace(1, -1, n_pvalues)
        
        store[f"g{4}_LL_res"]      = resolution
        store[f"g{4}_currentstep"] = 0
        
        # add additional information    
        store["proc_speed"] = deque(maxlen=10) 
        store["proc_speed_t0"] = None
        store["proc_speed_t1"] = None        

        return store
    
    def _make_app(self):
        """
        Grid Layout:
        +------------------------------------------+---------------------------+ 
        | card1 / plot1(main train and valid loss) | card4 / plot4 (pca stuff) | 
        +------------------------------------------+----------------------- ---+ 
        | card2 / plot2 (BS, and optimizer stuff)  |                           | 
        +------------------------------------------+ card5 (general info)      | 
        | card3 / plot2 (grad and weight norm)     |                           | 
        +------------------------------------------+---------------------------+  
        """

        app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        
        card1 = make_graphcard(self._setup_options["graph1"]["options"]["title"], "graph1", self._graph1)
        card2 = make_graphcard(self._setup_options["graph2"]["options"]["title"], "graph2", self._graph2)
        card3 = make_graphcard(self._setup_options["graph3"]["options"]["title"], "graph3", self._graph3)
        card4 = make_pcacard(
            self._setup_options["graph4"]["options"]["title"], 
            "graph4", 
            self._graph4[0], 
            self._setup_options["graph4"]["options"]["n_steps"]
            )
        card5 = make_infocard("additional information")
        
        app.layout = html.Div(
            style={
                "display"              : "grid",        # Enable grid layout
                "grid-template-rows"   : "5fr 3fr 3fr", # Three rows of equal height
                "grid-template-columns": "2fr 1fr",     # Two columns of equal width
                "gap"                  : "10px",        # Space between grid items
                "height"               : "100vh",       # Full viewport height for the grid
                "padding"              : "10px",        # padding around the main div window
            },
            children=[
                # visual elemens -----------------------------------------------
                card1, # Row 1, Column 1
                card4, # Row 1, Column 2
                card2, # Row 2, Column 1
                html.Div( # Row 2+3, Column 2 (Spans two rows)
                    card5,
                    style={
                        "background" : "transparent",
                        "grid-row"   : "2 / span 2",  # Start at row 2, span 2 rows
                        "grid-column": "2",           # Stay in column 2
                    },
                ),
                card3, # Row 3, Column 1
                # dash functionality elements ----------------------------------
                dcc.Interval( # interval for plot1 / card1
                    id          = "ud-interval-1",
                    interval    = 1000,
                    n_intervals = 0,
                ),
                dcc.Interval( # interval for plot2 / card2
                    id          = "ud-interval-2",
                    interval    = 1000,
                    n_intervals = 0,
                ),
                dcc.Interval( # interval for plot3 / card3
                    id          = "ud-interval-3",
                    interval    = 1000,
                    n_intervals = 0,
                ),
                dcc.Interval( # interval for plot4 / card4
                    id          = "ud-interval-4",
                    interval    = 1000,
                    n_intervals = 0,
                ),
                dcc.Interval( # interval for plot5 / card5
                    id          = "ud-interval-5",
                    interval    = 1000,
                    n_intervals = 0,
                ),
                dcc.Store( # holds the currentstep of plot4
                    id = "currentstep-graph4", data = 0
                )
            ]
        )
        
        # TODO add early stops if the data store has actually not changed between updates!
        @app.callback(
            Output("graph1", "figure"),
            Input("ud-interval-1", "n_intervals")
        )
        def update_graph1(n):
            update_flexgraph(self._store, self._n2t, opt = self._setup_options["graph1"], fig = self._graph1, graph = 1)
            return self._graph1
        
        @app.callback(
            Output("graph2", "figure"),
            Input("ud-interval-2", "n_intervals")
        )
        def update_graph2(n):
            update_flexgraph(self._store, self._n2t, opt = self._setup_options["graph2"], fig = self._graph2, graph = 2)
            return self._graph2
        
        @app.callback(
            Output("graph3", "figure"),
            Input("ud-interval-3", "n_intervals")
        )
        def update_graph3(n):
            update_flexgraph(self._store, self._n2t, opt = self._setup_options["graph3"], fig = self._graph3, graph = 3)
            return self._graph3
        
        @app.callback(
            Output("graph4", "figure"),
            Input("graph4-slider", "value")
        )
        def update_graph4(slidervalue):
            return self._graph4[slidervalue]
        
        @app.callback(
            [Output("currentstep-graph4", "data"), Output("graph4-slider", "value"), Output("graph4-slider", "marks")],
            Input("ud-interval-4", "n_intervals"),
            State("currentstep-graph4", "data")
        )
        def update_graph4_data(n, currentstep):
            if self._store[f"g{4}_currentstep"] <= currentstep:
                return no_update
            
            update_pcagraph(self._store, self._n2t, self._graph4) 
            
            # the other callback will then match shown figure to slider value that is set by this function!!
            new_currentstep = self._store[f"g{4}_currentstep"] 
            return new_currentstep, new_currentstep, {i: {} for i in range(new_currentstep + 1)}
        
        
        @app.callback(
            Output("proc-speed-value", "children"),
            Input("ud-interval-5", "n_intervals")
        )
        def upate_proc_speed(n):
            proc_speed = self._store["proc_speed"]
            
            if len(proc_speed) == 0:
                return "---------- samples/sec"
            
            avg_speed = sum(proc_speed) / len(proc_speed)
            return f"{avg_speed:,.2f} sampes/sec".replace(",", "'")
        
        
        @app.callback(
            Output("ud-interval-1", "interval"),
            Input("graph1-refreshrate", "value")
        )
        def update_refreshrate_1(selection):
            return selection
        
        @app.callback(
            Output("ud-interval-2", "interval"),
            Input("graph2-refreshrate", "value")
        )
        def update_refreshrate_2(selection):
            return selection
        
        @app.callback(
            Output("ud-interval-3", "interval"),
            Input("graph3-refreshrate", "value")
        )
        def update_refreshrate_3(selection):
            return selection
        
        
        
        return app
      
    
    
         
    def add_data(self, graph: int, trace: int, x: float, y: float, lo: float = None, hi: float = None):
        # TODO do robust sanitizing of input data! (like detach, cpu, remove Nans, etc...)
        
        if isinstance(y, torch.Tensor):
            y = y.detach().cpu().numpy()
        if isinstance(lo, torch.Tensor):
            lo = lo.detach().cpu().numpy()
        if isinstance(hi, torch.Tensor):
            hi = hi.detach().cpu().numpy()
        
        self._store[f"g{graph}_t{trace}_x"].append(x)
        self._store[f"g{graph}_t{trace}_y"].append(y)
        
        self._store[f"g{graph}_t{trace}_ymax"] = max(self._store[f"g{graph}_t{trace}_ymax"], y)
        self._store[f"g{graph}_t{trace}_ymin"] = min(self._store[f"g{graph}_t{trace}_ymin"], y)
        
        if (lo is not None) and (hi is not None):
            self._store[f"g{graph}_t{trace}_lo"].append(y-lo)
            self._store[f"g{graph}_t{trace}_hi"].append(y+hi)
    
    def batchtimer(self, action: str, batch_size: int = None):
        
        if action not in ["start", "stop", "read"]:
            raise ValueError(f"only 'start', 'stop' and 'read' allowed as action! (got {action})")
        
        if action == "start": # starts the timer
            self._store["proc_speed_t0"] = time.perf_counter()
            self._store["proc_speed_t1"] = None
        
        if action == "stop": # stops the timer and adds recorded time as proc speed to store (for card 5)
            self._store["proc_speed_t1"] = time.perf_counter()
            if self._store["proc_speed_t0"] is None:
                raise ValueError("start time for batchtimer was not set!")
            if self._store["proc_speed_t0"] >= self._store["proc_speed_t1"]:
                raise ValueError(f"got t0: {self._store["proc_speed_t0"]} and t1: {self._store["proc_speed_t1"]}!")
            if batch_size is None:
                raise ValueError(f"please specify a batch size when stopping the timer!")
            
            self._store["proc_speed"].append(batch_size / (self._store["proc_speed_t1"] - self._store["proc_speed_t0"]))
            self._store["proc_speed_t0"] = None
            self._store["proc_speed_t1"] = None
        
        if action == "read":
            if len(self._store["proc_speed"]) == 0:
                print("warning: there have been no processing speed timings yet!")
                return 0
            else:
                return sum(self._store["proc_speed"]) / len(self._store["proc_speed"])

    def reset_data(self):
        for key in self._store.keys():
            
            if "ymax" in key or "ymin" in key:
                self._store[key] = 0
                continue
            
            if "proc_speed" in key:
                if ("t0" in key) or ("t1" in key):
                    self._store[key] = None
                    continue
                
                self._store[key] = deque(maxlen=10)  
                continue
            
            if "g4" in key:
                if "LL_z" in key:
                    x = torch.linspace(-1, 1, 16)
                    y = torch.linspace(-1, 1, 16)
                    X, Y = torch.meshgrid(x, y, indexing="xy")
                    Z = X+Y + 10

                    self._store[key][0, :, :] = Z
                    self._store[key][1, :, :] = Z
                    self._store[key][2, :, :] = Z
                if "PV_x" in key:
                    self._store[key] = np.random.rand(self._store[key].shape[0], self._store[key].shape[1])
                if "currentstep" in key:
                    self._store[key] += 1
                    
                continue
            
            self._store[key] = [None]

    def run_jupyter(self, host: str = "127.0.0.1", port: int = 8050):
        """For running the plotter in a Jupyter notebook. Handles all the threading and keeping alive automatically."""
        
        self._app.run_server(
            host         = host, 
            jupyter_mode = "tab", # also has "inline" ... 
            port         = port, 
            debug        = True, 
            use_reloader = False)
    
    def run_script(self, host: str = "127.0.0.1", port: int = 8050):
        """For running the plotter in a script. Uses a daemon thread to avoid the app from blocking the script. Use run_script_spin a the end of the script to keep the app thread alive and be able to interact with data."""
        
        def _run():   
            self._app.run_server(
                host         = host,
                port         = port,     
                debug        = True,     
                use_reloader = False  
            )
        threading.Thread(target = _run, daemon = True).start()

    def run_script_spin(self):
        """For running the plotter in a script. Run this at the very end of the script. Keeps the app thread alive until the script is interrupted with ctrl+C to be able to view the data and interact with it."""
        
        print("Plotter dash app continues to run in the background. Press ctrl+C to stop.")
        try:
            while True:
                time.sleep(1) # lower cpu load!
        except KeyboardInterrupt:
            print("Terminating plotter dash app ...")

