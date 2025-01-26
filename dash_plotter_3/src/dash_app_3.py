### IMPORTS ###
########################################################################################################################
from dash import Dash, dcc, html, Output, Input, State, ctx, no_update
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time, os, sys
import numpy as np
import matplotlib.colors as mcolors
import threading
import torch

"""note on axis resetting with double click: the implementation is actually buggy and doesn't work reliable. In short, the fix is to either use autorangeoptions_minallowed / autorangeoptions_maxallowed where applicable. The second fix, is to return not the figure in the callback function for updating the plot, but also the parent container, e.g. actually piece together the dcc.Graph object and return this. This actually then works as intended!"""


class DashPlotter():
    
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
        
        self._graph1 = self._make_graph_123(opt = self._setup_options["graph1"], graph = 1)
        self._graph2 = self._make_graph_123(opt = self._setup_options["graph2"], graph = 2)
        self._graph3 = self._make_graph_123(opt = self._setup_options["graph3"], graph = 3)
        self._graph4 = self._make_graph_4(opt = self._setup_options["graph4"])
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
        n_pvalues = self._setup_options["graph4"]["options"]["n_pvalues"]
        store[f"g{4}_LL_x"] = np.linspace(-1, 1, resolution)
        store[f"g{4}_LL_y"] = np.linspace(-1, 1, resolution)
        store[f"g{4}_LL_z"] = np.ones((n_steps, resolution, resolution))
        
        store[f"g{4}_LL_z"][:, 0, 0] = np.linspace(0.9, 1.1, n_steps) # debug
        
        store[f"g{4}_PV_x"] = np.ones((n_steps, n_pvalues))
        store[f"g{4}_PV_y"] = np.linspace(1, -1, n_pvalues)
        
        store[f"g{4}_PV_x"][:, 0] = np.linspace(0, 1, n_steps) # debug
        
        # add additional information    
        store["proc_speed"] = None          

        return store
    
    def _make_graph_123(self, opt: dict, graph: int):
        """this receives the options dict of graphX, not the whole"""
        
        padding_factor = 0.03
        smoothing      = 0.6
        total          = opt["options"]["total"]
        xrange         = [- padding_factor * total, (1 + padding_factor) * total]
        yrange         = [0, None]
        gray_light     = "rgba(200, 200, 200, 1.0)"
        gray_dark      = "rgba(100, 100, 100, 1.0)"
        
        def _init_fig(opt: dict):
            """initialize the figure based on whether it needs to have suplots or not"""
            
            if opt["options"]["subplots"] is True:
                return make_subplots(specs=[[{"secondary_y": True}]])
            else:
                return go.Figure()   

        def _ADD_traces(opt: dict, fig: go.Figure):
            i = 1
            for key in opt.keys():
                if "trace" not in key:
                    continue
                trace = go.Scatter(
                    name = opt[key]["N"],
                    meta = opt[key]["N"], # just to be able to include name in hovertemplate
                    mode = "lines",
                    x    = [None],
                    y    = [None],
                    line = dict(color = opt[key]["C"], width = 2.0, shape = "spline", smoothing = smoothing),
                    legendgroup = f"group{i}",
                    hovertemplate = "%{meta}: %{y:.4f}<extra></extra>",
                )

                if opt["options"]["subplots"] is True:
                    fig.add_trace(trace, secondary_y = (False if opt[key]["T"] == "primary" else True))
                else:
                    fig.add_trace(trace)

                # add an entry for the dict that matches a name to each trace number
                self._n2t[f"g{graph}"][f"t{i}_main"] = len(self._n2t[f"g{graph}"])
                i += 1
            
            return fig
        
        def _ADD_traces_best(opt: dict, fig: go.Figure):
            if opt["options"]["showbest"] is not None:
                trace_w_best_key = opt["options"]["showbest"]                 # e.g. trace1
                trace_w_best     = int(trace_w_best_key.replace("trace", "")) # e.g. 1

                trace = go.Scatter(
                    mode       = "lines+markers",
                    x          = [None],
                    y          = [None], 
                    line       = dict(
                        color = opt[trace_w_best_key]["C"], 
                        width = 2, 
                        dash  = "dot", 
                        shape = "linear"
                    ),
                    marker     = dict(
                        size       = [0, 14], 
                        opacity    = [0, 1], 
                        symbol     = ["circle", "arrow-right"], 
                        line_width = [0, 0]
                    ),
                    showlegend = False,
                    hoverinfo  = "none",
                )

                if opt["options"]["subplots"] is True:
                    fig.add_trace(trace, secondary_y = (False if opt[trace_w_best_key]["T"] == "primary" else True))
                else:
                    fig.add_trace(trace)

                # add an entry for the dict that matches a name to each trace number
                self._n2t[f"g{graph}"][f"t{trace_w_best}_best"] = len(self._n2t[f"g{graph}"])
            
            return fig

        def _ADD_traces_error(opt: dict, fig: go.Figure):
            i = 1
            for key in opt.keys():
                if "trace" not in key:
                    continue
                if opt[key]["E"] is True:
                    traces = [
                        go.Scatter(
                            name = f"{opt[key]["N"]}_lo",
                            mode = "lines",
                            x    = [None],
                            y    = [None],
                            line = dict(color = opt[key]["C"], width = 0, shape = "spline", smoothing = smoothing), 
                            showlegend = False,
                            legendgroup = f"group{i}",
                            hoverinfo   = "none",
                        ),
                        go.Scatter(
                            name = f"{opt[key]["N"]}_hi",
                            mode = "lines",
                            x    = [None],
                            y    = [None],
                            line = dict(color = opt[key]["C"], width = 0, shape = "spline", smoothing = smoothing),
                            fill = "tonexty",
                            fillcolor = self._adjust_alpha(opt[key]["C"], 0.25),
                            showlegend = False,
                            legendgroup = f"group{i}",
                            hoverinfo   = "none",
                        ),
                    ]
                    
                    if opt["options"]["subplots"] is True:
                        fig.add_traces(traces, secondary_ys = ([False]*2 if opt[key]["T"] == "primary" else [True]*2))
                    else:
                        fig.add_traces(traces)
                        
                    self._n2t[f"g{graph}"][f"t{i}_lo"] = len(self._n2t[f"g{graph}"])
                    self._n2t[f"g{graph}"][f"t{i}_hi"] = len(self._n2t[f"g{graph}"])  
                i += 1
            
            return fig

        def _ADD_traces_newest(opt: dict, fig: go.Figure):
            i = 1
            for key in opt.keys():
                if "trace" not in key:
                    continue
                if opt[key]["P"] is True:
                    trace = go.Scatter(
                        mode = "markers",
                        x    = [None],
                        y    = [None],
                        marker = dict(
                            color    = [self._adjust_alpha(opt[key]["C"], 0), opt[key]["C"]], 
                            size     = [10, 4],
                            gradient = dict(
                                color = [self._adjust_alpha(opt[key]["C"], 0.9), opt[key]["C"]], 
                                type  = ["radial", "radial"]),
                            line     = dict(width = [0, 0]),
                        ),
                        showlegend  = False,
                        legendgroup = f"group{i}",
                        hoverinfo   = "none",
                        
                    )
            
                    if opt["options"]["subplots"] is True:
                        fig.add_trace(trace, secondary_y = (False if opt[key]["T"] == "primary" else True))
                    else:
                        fig.add_trace(trace)

                    # add an entry for the dict that matches a name to each trace number
                    self._n2t[f"g{graph}"][f"t{i}_end"] = len(self._n2t[f"g{graph}"])
                i += 1

            return fig  
            
        def _UD_layout(opt: dict, fig: go.Figure):
            fig.update_layout(
                uirevision    = "const",
                margin        = dict(l=0, r=220, t=0, b=0),
                margin_pad    = 5,
                plot_bgcolor  = "rgba(0, 0, 0, 0.0)",
                paper_bgcolor = "rgba(0, 0, 0, 0.0)",
                legend        = dict(
                    font    = dict( # setting font weight here will glitch legend visually!
                        color  = gray_light, 
                        family = "JetBrains Mono", 
                        size   = 12,
                    ), 
                    xref    = "container", 
                    yref    = "container",
                    xanchor = "right", 
                    yanchor = "top",
                    x       = 1.0, 
                    y       = 1.0,
                ),
                hoverlabel    = dict(
                    bgcolor     = "black",
                    bordercolor = "white",
                    font        = dict(
                        family = "JetBrains Mono", 
                        size   = 12, 
                        color  = "white"
                    ),
                ),
                hovermode     = "closest",
                modebar = {"orientation": "v"},
                shapes=[
                    dict(
                        type = "line",
                        x0   = total,
                        y0   = 0,
                        x1   = total,
                        y1   = 1,
                        xref = "x",
                        yref = "paper",
                        line = dict(
                            color = gray_light,
                            width = 2.0, 
                            dash  = "solid"
                        ),
                    ),
                ],
            ) 
            
            return fig
        
        def _UD_X_axis_general(opt: dict, fig: go.Figure):
            fig.update_xaxes(
                tickfont      = dict(
                    family = "JetBrains Mono", 
                    size   = 10, 
                    color  = gray_light,
                    weight = 500,
                ),
                zeroline      = True, 
                zerolinewidth = 1.5, 
                zerolinecolor = gray_light,
                showgrid      = True, 
                gridwidth     = 0.3, 
                gridcolor     = gray_dark, 
                griddash      = "dash",
                
                autorangeoptions_minallowed = xrange[0],
                autorangeoptions_maxallowed = xrange[1],
            )
            return fig
        
        def _UD_X_axis_subplots(opt: dict, fig: go.Figure):
            fig.update_xaxes(
                domain = [0, 1.0]
            )
            return fig
        
        def _UD_X_labl_general(opt: dict, fig: go.Figure):
            fig.update_xaxes(
                title          = opt["options"]["xlabel"],
                title_standoff = 10,
                title_font     = dict(
                    color  = gray_light,
                    family = "JetBrains Mono",
                    size   = 14,
                    weight = 500,
                ),
            )
            return fig
        
        def _UD_Y_axis_mono(opt: dict, fig: go.Figure):
            fig.update_yaxes(
                tickfont       = dict(
                    family = "JetBrains Mono", 
                    size   = 10, 
                    color  = gray_light,
                    weight = 500,
                ), 
                tickangle      = -90, 
                zeroline       = True, 
                zerolinewidth  = 1.5, 
                zerolinecolor  = gray_light,
                showgrid       = True, 
                gridwidth      = 0.3, 
                gridcolor      = gray_dark,
                
                autorangeoptions_minallowed = yrange[0],
            )
            return fig
        
        def _UD_Y_labl_mono(opt: dict, fig: go.Figure):
            fig.update_yaxes(
                title          = opt["options"]["ylabel1"],
                title_standoff = 15,
                title_font     = dict(
                    color  = gray_light,
                    family = "JetBrains Mono",
                    size   = 14,
                    weight = 500,
                ),
            )
            return fig
        
        def _UD_Y_axis_primary(opt: dict, fig: go.Figure):
            fig.update_yaxes(
                secondary_y   = False,
                
                tickfont      = dict(
                    family = "JetBrains Mono", 
                    size   = 10, 
                    color  = gray_light,
                    weight = 500,
                    ), 
                tickangle     = -90, 
                zeroline      = True, 
                zerolinewidth = 1.5, 
                zerolinecolor = gray_light,
                showgrid      = True, 
                gridwidth     = 0.3, 
                gridcolor     = gray_dark,
                
                autorangeoptions_minallowed = yrange[0],
            )
            return fig
        
        def _UD_Y_axis_secondary(opt: dict, fig: go.Figure):
            fig.update_yaxes(
                secondary_y= True,
                
                tickfont      = dict(
                    family = "JetBrains Mono", 
                    size   = 10, 
                    color  = gray_light,
                    weight = 500,
                    ), 
                tickangle     = -90, 
                zeroline      = False, 
                zerolinewidth = 1.5, 
                zerolinecolor = gray_light,
                showgrid      = False, 
                gridwidth     = 0.3, 
                gridcolor     = gray_dark,
                
                autorangeoptions_minallowed = yrange[0],
            )
            return fig
        
        def _UD_Y_labl_primary(opt: dict, fig: go.Figure):
            fig.update_yaxes(
                title          = opt["options"]["ylabel1"],
                title_standoff = 15,
                title_font     = dict(
                    color  = gray_light,
                    family = "JetBrains Mono",
                    size   = 14,
                    weight = 500,
                    ),
                secondary_y    = False,
            )
            return fig
        
        def _UD_Y_labl_secondary(opt: dict, fig: go.Figure):
            fig.update_yaxes(
                title          = opt["options"]["ylabel2"],
                title_standoff = 15,
                title_font     = dict(
                    color  = gray_light,
                    family = "JetBrains Mono",
                    size   = 14,
                    weight = 500,
                    ),
                secondary_y    = True,
            )
            return fig
        
        # -------------------------------------------------------- create figure
        fig = _init_fig(opt)
        # ----------------------------------------------------------- add traces
        fig = _ADD_traces_error(opt, fig)
        fig = _ADD_traces(opt, fig)
        fig = _ADD_traces_best(opt, fig)
        fig = _ADD_traces_newest(opt, fig)
        # ------------------------------------------------------------ layouting
        fig = _UD_layout(opt, fig)
        # --------------------------------------------------------- xaxis layout
        fig = _UD_X_axis_general(opt, fig)
        if opt["options"]["xlabel"] is not None:
            fig = _UD_X_labl_general(opt, fig)
        if opt["options"]["subplots"] is True:
            fig = _UD_X_axis_subplots(opt, fig)
        # --------------------------------------------------------- yaxis layout
        if opt["options"]["subplots"] is True: # with subplots
            fig = _UD_Y_axis_primary(opt, fig)
            fig = _UD_Y_axis_secondary(opt, fig)
            if opt["options"]["ylabel1"] is not None:
                fig = _UD_Y_labl_primary(opt, fig)
            if opt["options"]["ylabel2"] is not None:
                fig = _UD_Y_labl_secondary(opt, fig)
        else: # without subplots
            fig = _UD_Y_axis_mono(opt, fig)
            if opt["options"]["ylabel1"] is not None:
                fig = _UD_Y_labl_mono(opt, fig)
        
        return fig
    
    def _make_graph_4(self, opt: dict):
        
        def _create_LL(x, y, Z, zmin = None, zmax = None):
            trace = go.Heatmap(
                x             = x,
                y             = y,
                z             = np.log(Z + 1e-6),
                zmin          = zmin,
                zmax          = zmax,
                xgap          = 4,
                ygap          = 4,
                showscale     = False,
                customdata    = Z,
                hovertemplate = "loss: %{customdata:.3f}<extra></extra>",
                visible       = True,
                colorscale    = "Balance",
            )
            return trace
        
        def _create_PV(x, y):
            trace = go.Bar(
                x             = x + 0.05,
                y             = y,
                orientation   = "h",
                marker        = dict(color = "firebrick", line = dict(width = 0)),
                customdata    = x,
                hovertemplate = "EV: %{customdata:.4f}<extra></extra>",
                base          = 2.0 - 0.05,
                showlegend    = False,
                visible       = True,
            )
            return trace
        
        def _make_graph_4_step(
            LL_x: np.ndarray, LL_y: np.ndarray, LL_z: np.ndarray, res: int, 
            PV_x: np.ndarray, PV_y: np.ndarray, 
            step: int
            ):
            """res has to be divisible by 2!"""
            
            LL_zmin = np.log(LL_z + 1e-6).min()
            LL_zmax = np.log(LL_z + 1e-6).max()
        
            G = 0.02
            fac = 1.1
            y_range = [fac * LL_y.min(), fac * LL_y.max()]
            text_color = "rgba(200, 200, 200, 1.0)"
            grid_color = "rgba(100, 100, 100, 1.0)"
            
            fig = go.Figure()
            self._n2t[f"g{4}"][f"step{step}"] = {} # has to be initialized first!
            
            fig.add_trace(_create_LL( # top right Q
                LL_x[res//2:res]+G, 
                LL_y[res//2:res]+G, 
                LL_z[step, res//2:res, res//2:res], 
                zmin = LL_zmin, 
                zmax = LL_zmax
            ))
            self._n2t[f"g{4}"][f"step{step}"]["LL_q1"] = len(self._n2t[f"g{4}"][f"step{step}"])
            
            fig.add_trace(_create_LL( # top left Q
                LL_x[0:res//2]-G, 
                LL_y[res//2:res]+G, 
                LL_z[step, 0:res//2, res//2:res], 
                zmin = LL_zmin, 
                zmax = LL_zmax
            ))
            self._n2t[f"g{4}"][f"step{step}"]["LL_q2"] = len(self._n2t[f"g{4}"][f"step{step}"])
            
            fig.add_trace(_create_LL( # bottom left Q
                LL_x[0:res//2]-G, 
                LL_y[0:res//2]-G, 
                LL_z[step, 0:res//2, 0:res//2], 
                zmin = LL_zmin, 
                zmax = LL_zmax
            ))
            self._n2t[f"g{4}"][f"step{step}"]["LL_q3"] = len(self._n2t[f"g{4}"][f"step{step}"])
            
            fig.add_trace(_create_LL( # bottom right Q
                LL_x[res//2:res]+G, 
                LL_y[0:res//2]-G, 
                LL_z[step, res//2:res, 0:res//2], 
                zmin = LL_zmin, 
                zmax = LL_zmax
            ))
            self._n2t[f"g{4}"][f"step{step}"]["LL_q4"] = len(self._n2t[f"g{4}"][f"step{step}"])
            
            fig.add_trace(_create_PV( # add barplot
                PV_x[step, :], 
                PV_y
            ))
            self._n2t[f"g{4}"][f"step{step}"]["PV_bar"] = len(self._n2t[f"g{4}"][f"step{step}"])
            
            fig.update_layout(
                margin        = dict(l=0, r=0, t=0, b=0),
                margin_pad    = 0,
                plot_bgcolor  = "rgba(0, 0, 0, 0.0)",
                paper_bgcolor = "rgba(0, 0, 0, 0.0)",
                hoverlabel    = dict(
                    font        = dict(
                        family = "JetBrains Mono", 
                        size   = 12, 
                        color  = "white"
                    ),
                    bgcolor     = "black",
                    bordercolor = "white",
                ),
                bargap = 0.3,
                shapes=[
                    dict(
                        type="line",
                        x0=-1.1, x1=1.1,  # Vertical line at x=0
                        y0=0, y1=0,  # Full height of the subplot (normalized paper coordinates)
                        xref="x",   # Reference to the x-axis of the second subplot
                        yref="y",   # Reference to the y-axis of the second subplot
                        line=dict(
                            color=text_color,
                            width=2,
                        ),
                    ),
                    dict(
                        type="line",
                        x0=0, x1=0,  # Vertical line at x=0
                        y0=-1.1, y1=1.1,  # Full height of the subplot (normalized paper coordinates)
                        xref="x",   # Reference to the x-axis of the second subplot
                        yref="y",   # Reference to the y-axis of the second subplot
                        line=dict(
                            color=text_color,
                            width=2,
                        ),
                    ),
                    dict(
                        type="line",
                        x0=2.0, x1=2.0,  # Vertical line at x=0
                        y0=-1.1, y1=1.1,  # Full height of the subplot (normalized paper coordinates)
                        xref="x",   # Reference to the x-axis of the second subplot
                        yref="y",   # Reference to the y-axis of the second subplot
                        line=dict(
                            color=text_color,
                            width=2,
                        ),
                    ),
                    dict(
                        type="line",
                        x0=2.5, x1=2.5,  # Vertical line at x=0
                        y0=-1.1, y1=1.1,  # Full height of the subplot (normalized paper coordinates)
                        xref="x",   # Reference to the x-axis of the second subplot
                        yref="y",   # Reference to the y-axis of the second subplot
                        line=dict(
                            color=text_color,
                            width=1,
                            dash = "dot",
                        ),
                    ),
                    dict(
                        type="line",
                        x0=3.0, x1=3.0,  # Vertical line at x=0
                        y0=-1.1, y1=1.1,  # Full height of the subplot (normalized paper coordinates)
                        xref="x",   # Reference to the x-axis of the second subplot
                        yref="y",   # Reference to the y-axis of the second subplot
                        line=dict(
                            color=text_color,
                            width=1,
                            dash = "dot",
                        ),
                    ),
                ],
                annotations = [
                    dict(
                        x = -1.1,  # To the left of the y-axis
                        y = 0,  # Center vertically
                        text = "Y-Axis Label 1",
                        showarrow = False,
                        xref = "x",
                        yref = "y",
                        xanchor = "right",
                        yanchor = "middle",
                        textangle=-90,  # Rotate for Y-axis label
                        font = dict(
                            size = 14, 
                            color = text_color,
                            family = "JetBrains Mono",
                            ),
                    ),
                    dict(
                        x = 1.9,  # To the left of the y-axis
                        y = 0,  # Center vertically
                        text = "Y-Axis Label 2",
                        showarrow = False,
                        xref = "x",
                        yref = "y",
                        xanchor = "right",
                        yanchor = "middle",
                        textangle=-90,  # Rotate for Y-axis label
                        font = dict(
                            size = 14, 
                            color = text_color,
                            family = "JetBrains Mono",
                            ),
                    ),
                    dict(
                        x = 0,  # To the left of the y-axis
                        y = -1.1,  # Center vertically
                        text = "X-Axis Label 1",
                        showarrow = False,
                        xref = "x",
                        yref = "y",
                        xanchor = "center",
                        yanchor = "top",
                        textangle = 0,  # Rotate for Y-axis label
                        font = dict(
                            size = 14, 
                            color = text_color,
                            family = "JetBrains Mono",
                            ),
                    ),
                    dict(
                        x = 2.5,  # To the left of the y-axis
                        y = -1.1,  # Center vertically
                        text = "X l 2",
                        showarrow = False,
                        xref = "x",
                        yref = "y",
                        xanchor = "center",
                        yanchor = "top",
                        textangle = 0,  # Rotate for Y-axis label
                        font = dict(
                            size = 14, 
                            color = text_color,
                            family = "JetBrains Mono",
                            ),
                    ),
                ],
                modebar = {
                    "orientation": "v",  
                },
                uirevision = "const",
            )    
            
            fig.update_xaxes(
                scaleanchor    = "y",
                showgrid       = False,
                zeroline       = False,
                showticklabels = False,
                autorangeoptions_minallowed = -1.1 - 0.3,
                autorangeoptions_maxallowed =  3.2,
                fixedrange     = True,
            )

            fig.update_yaxes(
                scaleanchor    = "x",
                showgrid       = False,
                zeroline       = False,
                showticklabels = False,
                autorangeoptions_minallowed = y_range[0] - 0.2,
                autorangeoptions_maxallowed = y_range[1],
                fixedrange     = True,
            )
            
            return fig
        
        # grab config stuff
        n_steps   = opt["options"]["n_steps"]
        res       = opt["options"]["LL_resol"]
        n_pvalues = opt["options"]["n_pvalues"]
        
        # grab dummy values for LL plot (can't really be empty because log(Z)!)
        LL_x = self._store[f"g{4}_LL_x"] # the same for all steps
        LL_y = self._store[f"g{4}_LL_y"] # the same for all steps
        LL_z = self._store[f"g{4}_LL_z"] # [n_steps/epochs, resolution, resolution]
        
        # grab dummy values for the PV plot
        PV_x = self._store[f"g{4}_PV_x"]
        PV_y = self._store[f"g{4}_PV_y"]

        return [_make_graph_4_step(LL_x, LL_y, LL_z, res, PV_x, PV_y, step = i) for i in range(n_steps)]
    
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
        
        def _make_plotcard(title: str, graphid: str, graphfig: go.Figure, footer: dbc.CardFooter = None):
            cardcontent = [
                dbc.CardHeader(
                    title, 
                    className = "px-1 py-0 pt-0 pb-1"
                    ),
                dbc.CardBody(
                    dcc.Graph(
                        id         = graphid,
                        figure     = graphfig,
                        responsive = True,
                        style      = {"height": "100%", "width": "100%"},
                        config={
                            "showTips"            : False, 
                            "displaylogo"         : False,
                            "toImageButtonOptions": {
                                "format": "svg", # one of png, svg, jpeg, webp
                                "scale" : 1,     # Multiply title/legend/axis/canvas sizes by this factor
                            }
                        },
                    ), 
                    className = "px-0 py-0 pt-2 pb-0"
                )
            ]
            
            if footer is not None:
                cardcontent += [footer]
            
            card = dbc.Card(
                cardcontent,
                className = "h-100 p-2",
            )
            
            return card

        def _update_graph_123(opt: dict, fig: go.Figure, graph: int):
            """opt is just the graphX dict (with options and traces), not the whole setup_options!"""
            
            # TODO define more globally later
            paddx = 0.03 
            paddy = 0.05
            
            # init all with zero to avoid having min() or max() failing. zeros do not affect outcome anyways
            graphmax_pr = [0]
            graphmin_pr = [0]
            graphmax_sc = [0] 
            graphmin_sc = [0]
            
            i = 1
            for key in opt.keys(): # loop over all traceX in a graph -----------
                if "trace" not in key:
                    continue
                
                # update data MAIN traces --------------------------------------
                fig.data[self._n2t[f"g{graph}"][f"t{i}_main"]].x = self._store[f"g{graph}_t{i}_x"]
                fig.data[self._n2t[f"g{graph}"][f"t{i}_main"]].y = self._store[f"g{graph}_t{i}_y"]
                
                # update data BEST trace ---------------------------------------
                if opt["options"]["showbest"] == key:
                    total            = opt["options"]["total"]
                    trace_w_best_key = opt["options"]["showbest"]
                    
                    # only possible if the trace data is more than: [None]. Account for "None" when doing min! > ([1:])
                    if len(self._store[f"g{graph}_t{i}_y"]) > 1:
                        best = min(self._store[f"g{graph}_t{i}_y"][1:]) 
                        
                        fig.data[self._n2t[f"g{graph}"][f"t{i}_best"]].x = [0, (1 + paddx) * total]
                        fig.data[self._n2t[f"g{graph}"][f"t{i}_best"]].y = [best, best]
                        
                        if opt["options"]["subplots"] is True:
                            y = "y" if opt[trace_w_best_key]["T"] == "primary" else "y2"
                        else:
                            y = "y"   
                        fig.update_layout(
                            annotations = [
                                dict(
                                    x         = (1 + paddx) * total, 
                                    y         = best,
                                    xref      = "x", 
                                    yref      = y,
                                    xanchor   = "left", 
                                    yanchor   = "middle",
                                    text      = f"<b> lowest:<br> {best:07.4f}</b>",
                                    font      = dict(
                                        family = "JetBrains Mono", 
                                        size = 14, 
                                        color = opt[key]["C"]
                                    ),
                                    showarrow = False,
                                    align     = "left",
                                ),
                            ],
                        )
                
                # update data ERROR traces -------------------------------------
                if opt[key]["E"] is True:
                    fig.data[self._n2t[f"g{graph}"][f"t{i}_lo"]].x = self._store[f"g{graph}_t{i}_x"]
                    fig.data[self._n2t[f"g{graph}"][f"t{i}_lo"]].y = self._store[f"g{graph}_t{i}_lo"] 
                    fig.data[self._n2t[f"g{graph}"][f"t{i}_hi"]].x = self._store[f"g{graph}_t{i}_x"]
                    fig.data[self._n2t[f"g{graph}"][f"t{i}_hi"]].y = self._store[f"g{graph}_t{i}_hi"]
                
                # update ENDPOINTS ---------------------------------------------
                if opt[key]["P"] is True:
                    fig.data[self._n2t[f"g{graph}"][f"t{i}_end"]].x = [self._store[f"g{graph}_t{i}_x"][-1]] * 2
                    fig.data[self._n2t[f"g{graph}"][f"t{i}_end"]].y = [self._store[f"g{graph}_t{i}_y"][-1]] * 2
                
                # grab and store MIN / MAX for each trace ----------------------
                if opt["options"]["subplots"] is False:
                    graphmax_pr.append(self._store[f"g{graph}_t{i}_ymax"])
                    graphmin_pr.append(self._store[f"g{graph}_t{i}_ymin"])
                else:
                    if opt[key]["T"] == "primary":
                        graphmax_pr.append(self._store[f"g{graph}_t{i}_ymax"])
                        graphmin_pr.append(self._store[f"g{graph}_t{i}_ymin"])
                    else:
                        graphmax_sc.append(self._store[f"g{graph}_t{i}_ymax"])
                        graphmin_sc.append(self._store[f"g{graph}_t{i}_ymin"])

                i += 1 # -------------------------------------------------------
            
            # update range constraints of whole graph --------------------------
            if opt["options"]["subplots"] is False:
                mx = max(graphmax_pr)
                mn = min(graphmin_pr)
                fig.update_yaxes(
                    autorangeoptions_maxallowed = max(((1 + paddy) * mx),      (-paddy * mn)),
                    autorangeoptions_minallowed = min(     (-paddy * mx), ((1 + paddy) * mn)),
                )
            else:
                mx = max(graphmax_pr)
                mn = min(graphmin_pr)
                fig.update_yaxes(
                    secondary_y = False,
                    autorangeoptions_maxallowed = max(((1 + paddy) * mx),      (-paddy * mn)),
                    autorangeoptions_minallowed = min(     (-paddy * mx), ((1 + paddy) * mn)),
                )
                mx = max(graphmax_sc)
                mn = min(graphmin_sc)
                fig.update_yaxes(
                    secondary_y = True,
                    autorangeoptions_maxallowed = max(((1 + paddy) * mx),      (-paddy * mn)),
                    autorangeoptions_minallowed = min(     (-paddy * mx), ((1 + paddy) * mn)),
                )


        app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        
        card1 = _make_plotcard(self._setup_options["graph1"]["options"]["title"], "graph1", self._graph1)
        card2 = _make_plotcard(self._setup_options["graph2"]["options"]["title"], "graph2", self._graph2)
        card3 = _make_plotcard(self._setup_options["graph3"]["options"]["title"], "graph3", self._graph3)
        card4 = _make_plotcard(self._setup_options["graph4"]["options"]["title"], "graph4", self._graph4[0], 
            footer = dbc.CardFooter(
                dcc.Slider(
                    min        = 0, 
                    max        = (self._setup_options["graph4"]["options"]["n_steps"] - 1), 
                    step       = None,
                    value      = 0,
                    id         = "graph4-slider",
                    tooltip    = {"placement": "top", "always_visible": False},
                    updatemode = "drag",
                    marks = {i: {} for i in range(self._setup_options["graph4"]["options"]["n_steps"])},
                    className = "pt-0 pb-0 px-0 py-0",
                ), 
                className="px-0 py-0 pt-1 pb-0",                
            )          
        )
        card5 = dbc.Card(
            [
                dbc.CardHeader(
                    "Additional Information:",
                    className="px-1 py-0 pt-0 pb-1"
                ),
                dbc.CardBody(
                    [
                        html.Div(
                            [
                                html.Span(
                                    "Processing Speed: ", 
                                    id="proc-speed-label", 
                                    style={"float": "left"}
                                    ),
                                html.Span(
                                    "---- samples/sec", 
                                    id="proc-speed-value", 
                                    style={"float": "right"},
                                    className="bold-text",
                                    ),
                            ],
                            style={"width": "100%"},
                        ),   
                        html.Div("Total nr. of Parameters:"),
                        html.Div("asdfasdfasdf"),
                    ],
                    className="px-1 py-0 pt-2 pb-0",
                    style={"whiteSpace": "normal", "display": "flex", "flexDirection": "column"}
                ), 
            ],
            className = "h-100 p-2",
            id = "card-5",
        )
        
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
                dcc.Interval( # interval for plot3 / card3
                    id          = "ud-interval-4",
                    interval    = 1000,
                    n_intervals = 0,
                ),
                dcc.Interval( # interval for plot3 / card3
                    id          = "ud-interval-5",
                    interval    = 1000,
                    n_intervals = 0,
                ),
            ]
        )
        
        # TODO add early stops if the data store has actually not changed between updates!
        @app.callback(
            Output("graph1", "figure"),
            Input("ud-interval-1", "n_intervals")
        )
        def update_graph1(n):
            _update_graph_123(opt = self._setup_options["graph1"], fig = self._graph1, graph = 1) 
            return self._graph1
        
        @app.callback(
            Output("graph2", "figure"),
            Input("ud-interval-2", "n_intervals")
        )
        def update_graph1(n):
            _update_graph_123(opt = self._setup_options["graph2"], fig = self._graph2, graph = 2) 
            return self._graph2
        
        @app.callback(
            Output("graph3", "figure"),
            Input("ud-interval-3", "n_intervals")
        )
        def update_graph1(n):
            _update_graph_123(opt = self._setup_options["graph3"], fig = self._graph3, graph = 3) 
            return self._graph3
        
        @app.callback(
            Output("graph4", "figure"),
            Input("graph4-slider", "value")
        )
        def update_graph4(slidervalue):
            return self._graph4[slidervalue]
        
        @app.callback(
            Output("proc-speed-value", "children"),
            Input("ud-interval-5", "n_intervals")
        )
        def upate_proc_speed(n):
            proc_speed = self._store["proc_speed"]
            if proc_speed is None:
                return "---------- samples/sec"
            formatted_speed = f"{proc_speed:,.2f} sampes/sec".replace(",", "'")
            return formatted_speed
        
        
        return app
      
    def _adjust_alpha(self, color: str, adjust_a: float):
        """Takes a css "color name", "rgb(r, g, b)", or "rgba(r, g, b, a)" string and outputs the color in "rgba" format
        with 0.1 times the alpha value."""
        
        if color.startswith("rgb"):
            components = color[color.index("(")+1:color.index(")")].split(",")
            r, g, b    = map(int, components[:3])  # Extract RGB components
            a          = float(components[3]) if len(components) == 4 else 1.0  # a assumed to be 1.0 if not provided
        else:
            # Assume it's a CSS color name
            r, g, b = [int(c * 255) for c in mcolors.to_rgb(color)]
            a = 1.0

        a *= adjust_a
        a = max(0, min(a, 1)) # Ensure alpha stays in range [0, 1]
        return f"rgba({r}, {g}, {b}, {a:.3f})"
    
    
         
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
    
    def reset_data(self):
        for key in self._store.keys():
            if "ymax" in key or "ymin" in key:
                self._store[key] = 0
                continue
            if "proc_speed" in key:
                self._store[key] = None
                continue
            if "g4" in key:
                if "LL_Z" in key:
                    self._store[key][:, :, :] = 1
                if "PV_x" in key:
                    self._store[key][:, :] = 1
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




if __name__ == "__main__":
    
    setup_options = { 
        "graph1": {
            "options": {
                "title"   : "the first plot",
                "xlabel"  : "losses",
                "ylabel1" : "nr of samples processed total",
                "ylabel2" : None,
                "subplots": False,
                "showbest": "trace2",
                "total"   : 100,
            },
            "trace1" : {"N": "loss_train", "C": "firebrick", "T": None, "E": True, "P": True},
            "trace2" : {"N": "loss_valid", "C": "seagreen",  "T": None, "E": False, "P": True},
        },
        "graph2": {
            "options": {
                "title"    : "the second plot",
                "xlabel"   : None,
                "ylabel1"  : "eff. rates",
                "ylabel2"  : "batch size",
                "subplots" : True,
                "showbest" : None,
                "total"    : 100,
            },
            "trace1" : {"N": "eff. UdR", "C": "gold",       "T": "primary",   "E": False, "P": True},
            "trace2" : {"N": "eff. LR",  "C": "orange",     "T": "primary",   "E": False, "P": True},
            "trace3" : {"N": "batch sz", "C": "darkorchid", "T": "secondary", "E": False, "P": True},
        },  
        "graph3": {
            "options": {
                "title"    : "the third plot",
                "xlabel"   : None,
                "ylabel1"  : "grad norm",
                "ylabel2"  : "weight norm",
                "subplots" : True,
                "showbest" : None,
                "total"    : 100,
            },
            "trace1" : {"N": "grad norm",   "C": "steelblue",   "T": "primary",   "E": False, "P": True},
            "trace2" : {"N": "weight norm", "C": "saddlebrown", "T": "secondary", "E": False, "P": True},
        },  
        "graph4": {
            "options": {
                "title"     : "PCA stuff",
                "n_steps"   : 25,
                "LL_resol"  : 16,
                "n_pvalues" : 20,
                
            },
        },
    }
    
    PLOTTER = DashPlotter(setup_options)
    PLOTTER.run_script()
    
    Nr = lambda: np.random.rand()
    
    i = 0
    while True:
        if i >= 100:
            PLOTTER.reset_data()
            i = 0
            
        PLOTTER.add_data(graph=1, trace=1, x=i, y=2*Nr() + 5, lo = Nr()+1, hi = Nr()+2)
        PLOTTER.add_data(graph=1, trace=2, x=i, y=Nr() + 5)
        
        PLOTTER.add_data(graph=2, trace=1, x=i, y=2*Nr()+20)
        PLOTTER.add_data(graph=2, trace=2, x=i, y=3*Nr()+30)
        PLOTTER.add_data(graph=2, trace=3, x=i, y=10*Nr()+100)
        
        PLOTTER.add_data(graph=3, trace=1, x=i, y=Nr())
        PLOTTER.add_data(graph=3, trace=2, x=i, y=Nr())
        
        PLOTTER._store["proc_speed"] = np.random.rand() * 100_000
                
        i += 1
        
        time.sleep(0.3)
    
    
    
    PLOTTER.run_script_spin()
