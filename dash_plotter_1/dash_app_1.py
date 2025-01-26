### IMPORTS ###
########################################################################################################################
from dash import Dash, dcc, html, Output, Input, State, ctx, no_update
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time, os, sys
import numpy as np

import threading

"""
note on axis resetting with double click: the implementation is actually buggy and doesn't work reliable. In short, the fix is to either use autorangeoptions_minallowed / autorangeoptions_maxallowed where applicable. The second fix, is to return not the figure in the callback function for updating the plot, but also the parent container, e.g. actually piece together the dbc.Graph object and return this. This actually then works as intended!
"""

def make_figure_1(data_store):
    samples_total  = data_store["total_samples"]
    padding_factor = 0.03
    y_range        = [0, None]
    x_range        = [- padding_factor * samples_total, (1 + padding_factor) * samples_total]
    text_color     = "rgba(200, 200, 200, 1.0)"
    grid_color     = "rgba(100, 100, 100, 1.0)"
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        name       = "train loss",
        mode       = "lines",
        x          = data_store["train_loss_X"], 
        y          = data_store["train_loss_Y"], 
        line       = dict(color = "firebrick", width = 2.0, shape = "spline", smoothing = 0.6),
        ))
    
    fig.add_trace(go.Scatter(
        name       = "valid loss",
        mode       = "lines", 
        x          = data_store["valid_loss_X"], 
        y          = data_store["valid_loss_Y"],
        line       = dict(color = "Seagreen", width = 2.0, shape = "spline", smoothing = 0.6),
        ))
    
    fig.add_trace(go.Scatter(
        name       = "best valid loss",
        mode       = "lines+markers",
        x          = [0, (1 + padding_factor) * samples_total], 
        y          = np.array([1, 1]) * data_store["valid_loss_best_Y"],
        line       = dict(color = "seagreen", width = 2, dash = "dot", shape = "linear"),
        marker     = dict(size = [0, 20], opacity = [0, 1], symbol = ["circle", "diamond-wide"], line_width = [0, 0]),
        showlegend = False,
    ))
    
    fig.update_layout(
        uirevision = "const",
        margin = dict(l=0, r=220, t=0, b=0),
        margin_pad = 5,
        plot_bgcolor  = "rgba(0, 0, 0, 0.0)",
        paper_bgcolor = "rgba(0, 0, 0, 0.0)",
        legend = dict(
            font = dict(color=text_color, family="JetBrains Mono", size=12), # setting weight will glitch!
            xref="container", yref="container",
            xanchor = "right", yanchor = "top",
            x = 1.0, y = 1.0,
        ),
        annotations = [
            dict(
                x = x_range[1], y = data_store["valid_loss_best_Y"],
                xref="x", yref="y",
                xanchor = "left", yanchor="middle",
                text = f" <b>val.best <br> {data_store["valid_loss_best_Y"]:08.4f}</b>",
                font=dict(family="JetBrains Mono", size=14, color="seagreen"),
                showarrow = False,
                align = "left",
                # bgcolor = "rgba(0, 0, 0, 0.5)",
                # bordercolor = "seagreen", borderwidth = 2,
            ),
        ],
        modebar = {
            "orientation": "v",  
        },
    )

    fig.update_xaxes(
        title = "xaxis name: which is usually nr of samples processed",
        title_standoff = 10,
        title_font = dict(
            color = text_color,
            family = "JetBrains Mono",
            size = 14,
            weight = 500,
            ),
        tickfont=dict(
            family="JetBrains Mono", 
            size=10, 
            color=text_color,
            weight = 500,
            ),
        zeroline = True, zerolinewidth=1.5, zerolinecolor=text_color,
        showgrid = True, gridwidth=0.3, gridcolor=grid_color, griddash="dash",
        autorangeoptions_minallowed = x_range[0],
        autorangeoptions_maxallowed = x_range[1],
    )
    
    fig.update_yaxes(
        title = "yaxis name",
        title_standoff = 15,
        title_font = dict(
            color = text_color,
            family = "JetBrains Mono",
            size = 14,
            weight = 500,
            ),
        tickfont=dict(
            family="JetBrains Mono", 
            size=10, 
            color=text_color,
            weight = 500,
            ), 
        tickangle=-90, 
        zeroline = True, zerolinewidth=1.5, zerolinecolor=text_color,
        showgrid=True, gridwidth = 0.3, gridcolor=grid_color,
        autorangeoptions_minallowed = y_range[0],
    )
    
    return fig

def make_figure_2(data_store):
    samples_total  = data_store["total_samples"]
    padding_factor = 0.03
    y_range        = [0, None]
    x_range        = [- padding_factor * samples_total, (1 + padding_factor) * samples_total]
    text_color     = "rgba(200, 200, 200, 1.0)"
    grid_color     = "rgba(100, 100, 100, 1.0)"
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig.add_shape(
        type = "line",
        x0 = samples_total, y0 = 0,
        x1 = samples_total, y1 = 1,
        xref = "x", yref="paper",
        line = dict(color = text_color, width = 1.5, dash = "solid"),
    )
    
    fig.add_trace(go.Scatter(
        name       = "ud rate",
        mode       = "lines",
        x          = data_store["udrate_X"], 
        y          = data_store["udrate_Y"],
        line       = dict(color = "gold", width = 2.0, shape = "spline", smoothing = 0.6),
    ), 
    secondary_y = False)
    
    fig.add_trace(go.Scatter(
        name       = "eff LR",
        mode       = "lines",
        x          = data_store["momentum_X"], 
        y          = data_store["momentum_Y"],
        line       = dict(color = "orange", width = 2.0, shape = "spline", smoothing = 0.6),
    ), 
    secondary_y = False)
    
    fig.add_trace(go.Scatter(
        name       = "batch size",
        mode       = "lines",
        x          = data_store["batch_size_X"], 
        y          = data_store["batch_size_Y"],
        line       = dict(color = "darkolivegreen", width = 2.0, shape = "spline", smoothing = 0.6),
    ), 
    secondary_y = True)
    
    fig.update_layout(
        uirevision = "const",
        margin = dict(l=0, r=220, t=0, b=0),
        margin_pad = 5,
        plot_bgcolor  = "rgba(0, 0, 0, 0.0)",
        paper_bgcolor = "rgba(0, 0, 0, 0.0)",
        legend = dict(
            font = dict(color=text_color, family="JetBrains Mono", size=12), # setting weight will glitch!
            xref="container", yref="container",
            xanchor = "right", yanchor = "top",
            x = 1.0, y = 1.0,
        ),
        modebar = {
            "orientation": "v",  
        },
    )
    
    fig.update_xaxes(
        tickfont=dict(
            family="JetBrains Mono", 
            size=10, 
            color=text_color,
            weight = 500,
            ),
        domain = [0, 1.0],
        zeroline = True, zerolinewidth=1.5, zerolinecolor=text_color,
        showgrid = True, gridwidth=0.3, gridcolor=grid_color, griddash="dash",
        autorangeoptions_minallowed = x_range[0],
        autorangeoptions_maxallowed = x_range[1],
    )
     
    fig.update_yaxes(
        title = "effective udrate",
        title_standoff = 15,
        title_font = dict(
            color = text_color,
            family = "JetBrains Mono",
            size = 14,
            weight = 500,
            ),
        tickfont=dict(
            family="JetBrains Mono", 
            size=10, 
            color=text_color,
            weight = 500,
            ), 
        tickangle=-90, 
        zeroline = True, zerolinewidth=1.5, zerolinecolor=text_color,
        showgrid = True, gridwidth = 0.3, gridcolor=grid_color,
        autorangeoptions_minallowed = y_range[0],
        secondary_y= False,
    )
    
    fig.update_yaxes(
        title = "batch size",
        title_standoff = 15,
        title_font = dict(
            color = text_color,
            family = "JetBrains Mono",
            size = 14,
            weight = 500,
            ),
        tickfont=dict(
            family="JetBrains Mono", 
            size=10, 
            color=text_color,
            weight = 500,
            ), 
        tickangle=-90, 
        zeroline = False, zerolinewidth=1.5, zerolinecolor=text_color,
        showgrid = False, gridwidth = 0.3, gridcolor=grid_color,
        autorangeoptions_minallowed = y_range[0],
        secondary_y= True,
    )
    
    return fig

def make_figure_3(data_store):
    samples_total  = data_store["total_samples"]
    padding_factor = 0.03
    y_range        = [0, None] # max(1.20 * max(data_store["weight_norm_Y"]), 1.20 * max(data_store["grad_norm_Y"]))
    x_range        = [- padding_factor * samples_total, (1 + padding_factor) * samples_total]
    text_color     = "rgba(200, 200, 200, 1.0)"
    grid_color     = "rgba(100, 100, 100, 1.0)"
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig.add_shape(
        type = "line",
        x0 = samples_total, y0 = 0,
        x1 = samples_total, y1 = 1,
        xref = "x", yref="paper",
        line = dict(color = text_color, width = 1.5, dash = "solid"),
    )
    
    fig.add_trace(go.Scatter(
        name       = "weight norm",
        mode       = "lines",
        x          = data_store["weight_norm_X"], 
        y          = data_store["weight_norm_Y"],
        line       = dict(color = "steelblue", width = 2.0, shape = "spline", smoothing = 0.6),
    ), 
    secondary_y = False)
    
    fig.add_trace(go.Scatter(
        name       = "grad norm",
        mode       = "lines",
        x          = data_store["grad_norm_X"], 
        y          = data_store["grad_norm_Y"],
        line       = dict(color = "saddlebrown", width = 2.0, shape = "spline", smoothing = 0.6),
    ), 
    secondary_y = True)
    
    fig.update_layout(
        uirevision = "const",
        margin = dict(l=0, r=220, t=0, b=0),
        margin_pad = 5,
        plot_bgcolor  = "rgba(0, 0, 0, 0.0)",
        paper_bgcolor = "rgba(0, 0, 0, 0.0)",
        legend = dict(
            font = dict(color=text_color, family="JetBrains Mono", size=12), # setting weight will glitch!
            xref="container", yref="container",
            xanchor = "right", yanchor = "top",
            x = 1.0, y = 1.0,
        ),
        modebar = {
            "orientation": "v",  
        },
    )
    
    fig.update_xaxes(
        # title = "xaxis name: samples processed",
        # title_standoff = 10,
        # title_font = dict(
        #     color = text_color,
        #     family = "JetBrains Mono",
        #     size = 14,
        #     weight = 500,
        #     ),
        tickfont=dict(
            family="JetBrains Mono", 
            size=10, 
            color=text_color,
            weight = 500,
            ),
        domain = [0, 1.0],
        zeroline = True, zerolinewidth=1.5, zerolinecolor=text_color,
        showgrid = True, gridwidth=0.3, gridcolor=grid_color, griddash="dash",
        autorangeoptions_minallowed = x_range[0],
        autorangeoptions_maxallowed = x_range[1],
    )
     
    fig.update_yaxes(
        title = "weight norm",
        title_standoff = 15,
        title_font = dict(
            color = text_color,
            family = "JetBrains Mono",
            size = 14,
            weight = 500,
            ),
        tickfont=dict(
            family="JetBrains Mono", 
            size=10, 
            color=text_color,
            weight = 500,
            ), 
        tickangle=-90, 
        zeroline = True, zerolinewidth=1.5, zerolinecolor=text_color,
        showgrid = True, gridwidth = 0.3, gridcolor=grid_color,
        autorangeoptions_minallowed = y_range[0],
        secondary_y= False,
    )
    
    fig.update_yaxes(
        title = "grad norm",
        title_standoff = 15,
        title_font = dict(
            color = text_color,
            family = "JetBrains Mono",
            size = 14,
            weight = 500,
            ),
        tickfont=dict(
            family="JetBrains Mono", 
            size=10, 
            color=text_color,
            weight = 500,
            ), 
        tickangle=-90, 
        zeroline = False, zerolinewidth=1.5, zerolinecolor=text_color,
        showgrid = False, gridwidth = 0.3, gridcolor=grid_color,
        autorangeoptions_minallowed = y_range[0],
        secondary_y= True,
    )
    
    return fig

def make_figure_6(data_store):
    def create_heatmap(x, y, Z, i, zmin = None, zmax = None):
        trace = go.Heatmap(
            x             = x,
            y             = y,
            z             = np.log(Z[i, :, :] + 1e-6),
            zmin          = zmin,
            zmax          = zmax,
            xgap          = 4,
            ygap          = 4,
            showscale     = False,
            customdata    = Z[i, :, :],
            hovertemplate = "loss: %{customdata:.3f}<extra></extra>",
            visible       = False,
            colorscale    = "Balance",
        )
        return trace
    
    def create_bar(x, y, i):
        trace = go.Bar(
            x             = x[i, :] + 0.05,
            y             = y,
            orientation   = "h",
            marker        = dict(color = "firebrick", line = dict(width = 0)),
            customdata    = x[i, :],
            hovertemplate = "EV: %{customdata:.4f}<extra></extra>",
            base          = 2.0 - 0.05,
            showlegend    = False,
            visible       = False,
        )
        return trace
    
    # heatmap stuff
    x        = data_store["ll_x"]
    y        = data_store["ll_y"]
    Z        = data_store["ll_Z"]
    Z[:, 0, 0] = np.linspace(1, 20, 10) # only for debugging
    zmin     = np.log(Z + 1e-6).min()
    zmax     = np.log(Z + 1e-6).max()
    n_epochs = data_store["n_epochs"]
    init     = data_store["currentepoch"]
    
    fac_1     = 1
    fac_2     = 1.1
    x_range_1 = [fac_1 * x.min(), fac_1 * x.max()]
    y_range_1 = [fac_1 * y.min(), fac_1 * y.max()]
    x_range_2 = [fac_2 * x.min(), fac_2 * x.max()]
    y_range_2 = [fac_2 * y.min(), fac_2 * y.max()]
    
    text_color     = "rgba(200, 200, 200, 1.0)"
    grid_color     = "rgba(100, 100, 100, 1.0)"
    
    # pca singular values stuff    
    fig = go.Figure()
    
    G = 0.02
    for i in range(n_epochs):
        fig.add_trace( # bottom left Q
            create_heatmap(x[0: 8]-G, y[0: 8]-G, Z[:, 0: 8, 0: 8], i, zmin = zmin, zmax = zmax)
        )
        fig.add_trace( # bottom right Q
            create_heatmap(x[8:16]+G, y[0: 8]-G, Z[:, 8:16, 0: 8], i, zmin = zmin, zmax = zmax)
        )
        fig.add_trace( # top left Q
            create_heatmap(x[0: 8]-G, y[8:16]+G, Z[:, 0: 8, 8:16], i, zmin = zmin, zmax = zmax)
        )
        fig.add_trace( # top right Q
            create_heatmap(x[8:16]+G, y[8:16]+G, Z[:, 8:16, 8:16], i, zmin = zmin, zmax = zmax)
        )
        
        fig.add_trace( # add barplot
            create_bar(data_store["Pvalues_x"], data_store["Pvalues_y"], i)
        )
        
    for j in range(5):
        fig.data[5*init+j].visible = True

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
    )
    
    fig.update_xaxes(
        scaleanchor    = "y",
        showgrid       = False,
        zeroline       = False,
        showticklabels = False,
        autorangeoptions_minallowed = -1.1 - 0.3,
        autorangeoptions_maxallowed =  3.1,
        fixedrange     = True,
    )

    fig.update_yaxes(
        scaleanchor    = "x",
        showgrid       = False,
        zeroline       = False,
        showticklabels = False,
        autorangeoptions_minallowed = y_range_2[0] - 0.2,
        autorangeoptions_maxallowed = y_range_2[1],
        fixedrange     = True,
    )
    
    return fig


def create_app(data_store):
    app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP]) # 

    card1 = dbc.Card(
        [
            dbc.CardHeader(
                "Main Plot: Training and Validation Error",
                className="px-1 py-0 pt-0 pb-1"
            ),
            dbc.CardBody(
                dcc.Graph(
                    id="plot1",
                    # figure = make_figure_1(data_store),
                    responsive=True,
                    style={"height": "100%", "width": "100%"},
                    config={
                        # "displayModeBar": False, 
                        "showTips": False, 
                        "displaylogo": False,
                        "toImageButtonOptions": {
                            "format": "svg", # one of png, svg, jpeg, webp
                            'scale': 1, # Multiply title/legend/axis/canvas sizes by this factor
                        }
                        }
                ),
                className="px-0 py-0 pt-2 pb-0"
            ), 
        ],
        className="h-100 p-2"
    )   
    
    card2 = dbc.Card(
        [
            dbc.CardHeader(
                "Parameter-Space PCA",
                className="px-1 py-0 pt-0 pb-1"
            ),
            dbc.CardBody(
                [
                    dcc.Graph(
                        id="plot4",
                        figure = make_figure_6(data_store),
                        responsive=True,
                        style={
                            "height"   : "100%", 
                            "width"    : "100%", 
                            }, 
                        config={
                            # "displayModeBar": False, 
                            "showTips": False, 
                            "displaylogo": False,
                            "toImageButtonOptions": {
                                "format": "svg", # one of png, svg, jpeg, webp
                                'scale': 1, # Multiply title/legend/axis/canvas sizes by this factor
                            }
                        }
                    ), 
                ],
                className="px-0 py-0 pt-2 pb-2",
            ),        
            dbc.CardFooter(
                dcc.Slider(
                    min        = 0, 
                    max        = (data_store["n_epochs"] - 1), 
                    step       = None,
                    value      = data_store["currentepoch"],
                    id         = "epochslider",
                    tooltip    = {"placement": "top", "always_visible": False},
                    updatemode = "drag",
                    marks = {
                        0: {}, 1: {}, 2: {}, 3: {}, 4: {}, 5: {}, 6: {}, 7: {}, 8: {}, 9: {},
                    },
                    className = "pt-0 pb-0 px-0 py-0",
                ), 
                className="px-0 py-0 pt-1 pb-0",                
            ),
        ], 
        className="h-100 p-2"
    )  
    
    card3 = dbc.Card(
        [
            dbc.CardHeader(
                "Auxiliary Plot 1: Learning Rate and Batch Size",
                className="px-1 py-0 pt-0 pb-1"
            ),
            dbc.CardBody(
                dcc.Graph(
                    id="plot2",
                    # figure = make_figure_2(data_store),
                    responsive=True,
                    style={"height": "100%", "width": "100%"},
                    config={
                        # "displayModeBar": False, 
                        "showTips": False, 
                        "displaylogo": False,
                        "toImageButtonOptions": {
                            "format": "svg", # one of png, svg, jpeg, webp
                            'scale': 1, # Multiply title/legend/axis/canvas sizes by this factor
                        }
                        }
                ),
                className="px-0 py-0 pt-2 pb-0"
            ), 
        ],
        className="h-100 p-2",
    )   
    
    card4 = dbc.Card(
        [
            dbc.CardHeader(
                "Additional Information: ",
                className="px-1 py-0 pt-0 pb-1"
            ),
            dbc.CardBody(
                "just some text",
                className="px-0 py-0 pt-2 pb-0"
            ), 
        ],
        className = "h-100 p-2",
    )
    
    card5 = dbc.Card(
        [
            dbc.CardHeader(
                "Auxiliary Plot 2: ",
                className="px-1 py-0 pt-0 pb-1"
            ),
            dbc.CardBody(
                dcc.Graph(
                    id="plot3",
                    # figure = make_figure_2(data_store),
                    responsive=True,
                    style={"height": "100%", "width": "100%"},
                    config={
                        # "displayModeBar": False, 
                        "showTips": False, 
                        "displaylogo": False,
                        "toImageButtonOptions": {
                            "format": "svg", # one of png, svg, jpeg, webp
                            'scale': 1, # Multiply title/legend/axis/canvas sizes by this factor
                        }
                        }
                ),
                className="px-0 py-0 pt-2 pb-0"
            ), 
        ],
        className="h-100 p-2"
    )
    
    app.layout = html.Div(
        style={
            'display'              : 'grid',  # Enable grid layout
            'grid-template-rows'   : '5fr 3fr 3fr',  # Three rows of equal height
            'grid-template-columns': '2fr 1fr',  # Two columns of equal width
            'gap'                  : '10px',  # Space between grid items
            'height'               : '100vh',  # Full viewport height for the grid
            "padding"              : "10px",
        },
        children=[
            # Row 1, Column 1
            card1,
            # Row 1, Column 2
            card2,
            # Row 2, Column 1
            card3,
            # Row 2+3, Column 2 (Spans two rows)
            html.Div(
                card4,
                style={
                    'background': 'transparent',
                    'grid-row': '2 / span 2',  # Start at row 2, span 2 rows
                    'grid-column': '2',  # Stay in column 2
                }
            ),
            # Row 3, Column 1
            card5,
            dcc.Interval(
                id="update-interval",  # This triggers updates at a set interval
                interval=2000,          # Update every 500ms
                n_intervals=0          # Counts the number of updates
                ),
            dcc.Store(id = "visible_heatmap", data = data_store["currentepoch"]),
        ]
    )
    
    @app.callback(
        [Output("plot1", "figure"), Output("plot2", "figure"), Output("plot3", "figure")],
        Input("update-interval", "n_intervals"),
    )
    def update_plot(n):     
        return make_figure_1(data_store), make_figure_2(data_store), make_figure_3(data_store)
    
    @app.callback(
        [Output("plot4", "figure"), Output("visible_heatmap", "data")],
        [Input("epochslider", "value")],
        [State("plot4", "figure"), State("visible_heatmap", "data")],
    )
    def update_heatmap(selected_epoch, current_figure, current_visible):
        updated_fig = go.Figure(current_figure)
        
        for j in range(5):
            updated_fig.data[5*current_visible+j].visible = False
            updated_fig.data[5*selected_epoch+j].visible = True
        
        return updated_fig, selected_epoch
        
    return app

def run_app(app, port=8050):
    def _run():
        app.run(host="127.0.0.1", jupyter_mode="tab", port=port, debug=True, use_reloader=False)
    threading.Thread(target=_run).start()
    
if __name__ == "__main__":
    
    # generate some dummy data when this is run from this script
    data_store = {
        "total_samples": 120,
        
        "train_loss_X": np.linspace(0, 100, 100), "train_loss_Y": np.random.rand(100) + 0.3,
        "valid_loss_X": np.linspace(0, 100, 100), "valid_loss_Y": np.random.rand(100) + 0.6,
        "valid_loss_best_Y": 1.41,
        
        "weight_norm_X": np.linspace(0, 100, 100), "weight_norm_Y": np.random.rand(100),
        "grad_norm_X": np.linspace(0, 100, 100), "grad_norm_Y": np.random.rand(100) + 2,
        
        "batch_size_X": np.linspace(0, 100, 20), "batch_size_Y": np.random.rand(20) + 100,
        "momentum_X": np.linspace(0, 100, 100), "momentum_Y": np.random.rand(100) + 0.5,
        
        "udrate_X": np.linspace(0, 100, 100), "udrate_Y": np.random.rand(100) + 2,
        
        "n_epochs": 10, "currentepoch": 0,
        "ll_x": np.linspace(-1, 1, 16), "ll_y": np.linspace(-1, 1, 16), "ll_Z": np.random.rand(10, 16, 16) + 1,
        
        "nPvalues": 20,
        "Pvalues_x": np.random.rand(10, 20), "Pvalues_y": np.linspace(1, -1, 20),
        }
        
    app = create_app(data_store)
    app.run(debug=True)
