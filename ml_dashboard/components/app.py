from   dash import Dash, Input, Output, State, dcc, html, no_update
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

from   ml_dashboard.components import make_graphcard, make_pcacard, make_infocard
from   ml_dashboard.components import update_flexgraph, update_pcagraph


"""note on axis resetting with double click: the implementation is actually buggy and doesn't work reliable. In short, the fix is to either use autorangeoptions_minallowed / autorangeoptions_maxallowed where applicable. The second fix, is to return not the figure in the callback function for updating the plot, but also the parent container, e.g. actually piece together the dcc.Graph object and return this. This actually then works as intended!"""
 
def make_plotter_app(
    setup_options: dict, store: dict, n2t: dict,
    graph1: go.Figure, graph2: go.Figure, graph3: go.Figure, graph4: list[go.Figure]
    ):
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

    app = Dash(
        __name__, 
        external_stylesheets = [dbc.themes.BOOTSTRAP],
        assets_folder        = "../assets" # specify assets folder because project structure is different from default
        )
    
    card1 = make_graphcard(setup_options["graph1"]["options"]["title"], "graph1", graph1)
    card2 = make_graphcard(setup_options["graph2"]["options"]["title"], "graph2", graph2)
    card3 = make_graphcard(setup_options["graph3"]["options"]["title"], "graph3", graph3)
    card4 = make_pcacard(
        setup_options["graph4"]["options"]["title"], 
        "graph4", 
        graph4[0], 
        setup_options["graph4"]["options"]["n_steps"]
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
        update_flexgraph(store, n2t, opt = setup_options["graph1"], fig = graph1, graph = 1)
        return graph1
    
    @app.callback(
        Output("graph2", "figure"),
        Input("ud-interval-2", "n_intervals")
    )
    def update_graph2(n):
        update_flexgraph(store, n2t, opt = setup_options["graph2"], fig = graph2, graph = 2)
        return graph2
    
    @app.callback(
        Output("graph3", "figure"),
        Input("ud-interval-3", "n_intervals")
    )
    def update_graph3(n):
        update_flexgraph(store, n2t, opt = setup_options["graph3"], fig = graph3, graph = 3)
        return graph3
    
    @app.callback(
        Output("graph4", "figure"),
        Input("graph4-slider", "value")
    )
    def update_graph4(slidervalue):
        return graph4[slidervalue]
    
    @app.callback(
        [Output("currentstep-graph4", "data"), Output("graph4-slider", "value"), Output("graph4-slider", "marks")],
        Input("ud-interval-4", "n_intervals"),
        State("currentstep-graph4", "data")
    )
    def update_graph4_data(n, currentstep):
        if store[f"g{4}_currentstep"] <= currentstep:
            return no_update
        
        update_pcagraph(store, n2t, graph4) 
        
        # the other callback will then match shown figure to slider value that is set by this function!!
        new_currentstep = store[f"g{4}_currentstep"] 
        return new_currentstep, new_currentstep, {i: {} for i in range(new_currentstep + 1)}
    
    
    @app.callback(
        Output("proc-speed-value", "children"),
        Input("ud-interval-5", "n_intervals")
    )
    def upate_proc_speed(n):
        proc_speed = store["proc_speed"]
        
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
    
    
    