import numpy as np
import plotly.graph_objects as go
from   plotly.subplots import make_subplots
from   ml_dashboard.utils import adjust_alpha


def make_flexgraph(store: dict, n2t: dict, opt: dict, graph: int):
    """
    _nt2 is the reference to self._n2t that is used to store the mapping of trace number to a useful name
    opt dict is the options dict of graphX (with options, trace1, trace2, ...), not the full one. 
    graph int is just the graph number
    """
    
    # customization parameters (#TODO make more globally controllable later)
    padding_factor = 0.03 # the additional space that is added + and - along the x axis
    smoothing      = 0.6  # smooting factor of all the spline traces
    gray_light     = "rgba(200, 200, 200, 1.0)"
    gray_dark      = "rgba(100, 100, 100, 1.0)"
    
    # some handles for often used variables
    total          = opt["options"]["total"] # total number of Samples to be processed. defines x range
    xrange         = [- padding_factor * total, (1 + padding_factor) * total]
    yrange         = [0, None]

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
            n2t[f"g{graph}"][f"t{i}_main"] = len(n2t[f"g{graph}"])
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
                    size       = [0, 20], 
                    opacity    = [0, 1], 
                    symbol     = ["circle", "triangle-left"], 
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
            n2t[f"g{graph}"][f"t{trace_w_best}_best"] = len(n2t[f"g{graph}"])
        
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
                        fillcolor = adjust_alpha(opt[key]["C"], 0.25),
                        showlegend = False,
                        legendgroup = f"group{i}",
                        hoverinfo   = "none",
                    ),
                ]
                
                if opt["options"]["subplots"] is True:
                    fig.add_traces(traces, secondary_ys = ([False]*2 if opt[key]["T"] == "primary" else [True]*2))
                else:
                    fig.add_traces(traces)
                    
                n2t[f"g{graph}"][f"t{i}_lo"] = len(n2t[f"g{graph}"])
                n2t[f"g{graph}"][f"t{i}_hi"] = len(n2t[f"g{graph}"])  
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
                        color    = [adjust_alpha(opt[key]["C"], 0), opt[key]["C"]], 
                        size     = [10, 4],
                        gradient = dict(
                            color = [adjust_alpha(opt[key]["C"], 0.9), opt[key]["C"]], 
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
                n2t[f"g{graph}"][f"t{i}_end"] = len(n2t[f"g{graph}"])
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

def make_pcagraph(store: dict, n2t: dict, opt: dict):
    
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
    
    def _make_pcagraph_step(
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
        n2t[f"g{4}"][f"step{step}"] = {} # has to be initialized first!
        
        fig.add_trace(_create_LL( # top right (Q1)
            LL_x[res//2:res]+G, 
            LL_y[res//2:res]+G, 
            LL_z[step, res//2:res, res//2:res], 
            zmin = LL_zmin, 
            zmax = LL_zmax
        ))
        n2t[f"g{4}"][f"step{step}"]["LL_q1"] = len(n2t[f"g{4}"][f"step{step}"])
        
        fig.add_trace(_create_LL( # top left (Q2)
            LL_x[0:res//2]-G, 
            LL_y[res//2:res]+G, 
            LL_z[step, res//2:res, 0:res//2], 
            zmin = LL_zmin, 
            zmax = LL_zmax
        ))
        n2t[f"g{4}"][f"step{step}"]["LL_q2"] = len(n2t[f"g{4}"][f"step{step}"])
        
        fig.add_trace(_create_LL( # bottom left (Q3)
            LL_x[0:res//2]-G, 
            LL_y[0:res//2]-G, 
            LL_z[step, 0:res//2, 0:res//2], 
            zmin = LL_zmin, 
            zmax = LL_zmax
        ))
        n2t[f"g{4}"][f"step{step}"]["LL_q3"] = len(n2t[f"g{4}"][f"step{step}"])
        
        fig.add_trace(_create_LL( # bottom right (Q4)
            LL_x[res//2:res]+G, 
            LL_y[0:res//2]-G, 
            LL_z[step, 0:res//2, res//2:res], 
            zmin = LL_zmin, 
            zmax = LL_zmax
        ))
        n2t[f"g{4}"][f"step{step}"]["LL_q4"] = len(n2t[f"g{4}"][f"step{step}"])
        
        fig.add_trace(_create_PV( # add barplot
            PV_x[step, :], 
            PV_y
        ))
        n2t[f"g{4}"][f"step{step}"]["PV_bar"] = len(n2t[f"g{4}"][f"step{step}"])
        
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
    
    # grab values for LL plot (can't really be empty because log(Z)!)
    LL_x = store[f"g{4}_LL_x"] # the same for all steps
    LL_y = store[f"g{4}_LL_y"] # the same for all steps
    LL_z = store[f"g{4}_LL_z"] # [n_steps/epochs, resolution, resolution]
    
    # grab values for the PV plot
    PV_x = store[f"g{4}_PV_x"]
    PV_y = store[f"g{4}_PV_y"]
        
    return [_make_pcagraph_step(LL_x, LL_y, LL_z, res, PV_x, PV_y, step = i) for i in range(n_steps)]

def update_flexgraph(store: dict, n2t: dict, opt: dict, fig: go.Figure, graph: int):
    """
    store : reference to the plotter object store
    n2t   : reference to hte plotter object mapping between trace numbers and some more useful names
    opt   : is just the graphX dict (with options and traces), not the whole setup_options!
    fig   : reference to the figure that is to be modified
    graph : graph number
    """

    # TODO define more globally later
    paddx = 0.03 
    paddy = 0.05
    
    # init all with zero to avoid having min() or max() failing. zeros do not affect outcome anyways
    graphmax_pr = [0]
    graphmin_pr = [0]
    graphmax_sc = [0] 
    graphmin_sc = [0]
    
    i = 1
    for key in opt.keys(): # loop over all traceX in a graph -------------------
        if "trace" not in key:
            continue # skip the option key
        
        # update data MAIN traces ----------------------------------------------
        fig.data[n2t[f"g{graph}"][f"t{i}_main"]].x = store[f"g{graph}_t{i}_x"]
        fig.data[n2t[f"g{graph}"][f"t{i}_main"]].y = store[f"g{graph}_t{i}_y"]
        
        # update data BEST trace -----------------------------------------------
        if opt["options"]["showbest"] == key:
            total            = opt["options"]["total"]
            trace_w_best_key = opt["options"]["showbest"]
            
            # only possible if the trace data is more than: [None]. Account for initial "None" when doing min! > ([1:])
            if len(store[f"g{graph}_t{i}_y"]) > 1:
                best = min(store[f"g{graph}_t{i}_y"][1:]) #TODO replace this to use ymin!! (currently inefficient)
                
                fig.data[n2t[f"g{graph}"][f"t{i}_best"]].x = [0, (1 + paddx) * total]
                fig.data[n2t[f"g{graph}"][f"t{i}_best"]].y = [best, best]
                
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
                            bgcolor   = "rgba(20, 20, 20, 1.0)",
                        ),
                    ],
                )
        
        # update data ERROR traces ---------------------------------------------
        if opt[key]["E"] is True:
            fig.data[n2t[f"g{graph}"][f"t{i}_lo"]].x = store[f"g{graph}_t{i}_x"]
            fig.data[n2t[f"g{graph}"][f"t{i}_lo"]].y = store[f"g{graph}_t{i}_lo"] 
            fig.data[n2t[f"g{graph}"][f"t{i}_hi"]].x = store[f"g{graph}_t{i}_x"]
            fig.data[n2t[f"g{graph}"][f"t{i}_hi"]].y = store[f"g{graph}_t{i}_hi"]
        
        # update ENDPOINTS -----------------------------------------------------
        if opt[key]["P"] is True:
            fig.data[n2t[f"g{graph}"][f"t{i}_end"]].x = [store[f"g{graph}_t{i}_x"][-1]] * 2
            fig.data[n2t[f"g{graph}"][f"t{i}_end"]].y = [store[f"g{graph}_t{i}_y"][-1]] * 2
        
        # grab and store MIN / MAX for each trace ------------------------------
        if opt["options"]["subplots"] is False:
            graphmax_pr.append(store[f"g{graph}_t{i}_ymax"])
            graphmin_pr.append(store[f"g{graph}_t{i}_ymin"])
        else:
            if opt[key]["T"] == "primary":
                graphmax_pr.append(store[f"g{graph}_t{i}_ymax"])
                graphmin_pr.append(store[f"g{graph}_t{i}_ymin"])
            else:
                graphmax_sc.append(store[f"g{graph}_t{i}_ymax"])
                graphmin_sc.append(store[f"g{graph}_t{i}_ymin"])

        i += 1 # ---------------------------------------------------------------
    
    # update range constraints of whole graph ----------------------------------
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

def update_pcagraph(store: dict, n2t: dict, figlist: list[go.Figure]):
    
    LLz  = store[f"g{4}_LL_z"]
    PVx  = store[f"g{4}_PV_x"]
    res  = store[f"g{4}_LL_res"]
    zmin = np.log(LLz + 1e-6).min()
    zmax = np.log(LLz + 1e-6).max()  
    
    for stepnr, fig in enumerate(figlist): # this should actually modify the stored figs (by reference)
        # Heatmap
        tracenr                      = n2t[f"g{4}"][f"step{stepnr}"][f"LL_q1"]
        fig.data[tracenr].z          = np.log(LLz[stepnr, res//2:res, res//2:res] + 1e-6)
        fig.data[tracenr].customdata = LLz[stepnr, res//2:res, res//2:res]
        fig.data[tracenr].zmin       = zmin
        fig.data[tracenr].zmax       = zmax
        
        tracenr                      = n2t[f"g{4}"][f"step{stepnr}"][f"LL_q2"]
        fig.data[tracenr].z          = np.log(LLz[stepnr, res//2:res, 0:res//2] + 1e-6)
        fig.data[tracenr].customdata = LLz[stepnr, res//2:res, 0:res//2]
        fig.data[tracenr].zmin       = zmin
        fig.data[tracenr].zmax       = zmax
        
        tracenr                      = n2t[f"g{4}"][f"step{stepnr}"][f"LL_q3"]
        fig.data[tracenr].z          = np.log(LLz[stepnr, 0:res//2, 0:res//2] + 1e-6)
        fig.data[tracenr].customdata = LLz[stepnr, 0:res//2, 0:res//2]
        fig.data[tracenr].zmin       = zmin
        fig.data[tracenr].zmax       = zmax
        
        tracenr                      = n2t[f"g{4}"][f"step{stepnr}"][f"LL_q4"]
        fig.data[tracenr].z          = np.log(LLz[stepnr, 0:res//2, res//2:res] + 1e-6)
        fig.data[tracenr].customdata = LLz[stepnr, 0:res//2, res//2:res]
        fig.data[tracenr].zmin       = zmin
        fig.data[tracenr].zmax       = zmax

        # Pvalues Barplot
        fig.data[n2t[f"g{4}"][f"step{stepnr}"]["PV_bar"]].x          = PVx[stepnr, :] + 0.05
        fig.data[n2t[f"g{4}"][f"step{stepnr}"]["PV_bar"]].customdata = PVx[stepnr, :]



    