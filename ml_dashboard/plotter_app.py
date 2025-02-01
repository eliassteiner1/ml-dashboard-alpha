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
from ml_dashboard.components import make_plotter_app, make_flexgraph, make_pcagraph



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

        self._app    = make_plotter_app(
            self._setup_options, self._store, self._n2t, 
            graph1 = self._graph1, graph2 = self._graph2, graph3 = self._graph3, graph4 = self._graph4
        )
    
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

