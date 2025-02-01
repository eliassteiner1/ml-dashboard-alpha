from   dash import Dash, Input, Output, State, dcc, html
import dash_bootstrap_components as dbc
import plotly.graph_objects as go


def make_graphcard(title: str, graphid: str, graphfig: go.Figure):
    """
    template function to create a card with a simple graph that can display multiple different dataseries.
    
    title:    text displayed in the header of the card
    graphid:  the html id given to the graph element of this card (for callbacks)
    graphfig: the initial figure that is displayed when the app is started
    """
    
    header = dbc.CardHeader(
        children  = [
            html.Div(
                children  = [title], 
                style     = {
                    "flex":         1, 
                    "padding-left": "0.25rem",
                    "margin-right": "10px",
                },
            ),
            html.Div(
                children  = ["refresh:"], 
                style     = {
                    "margin-right": "5px",
                },
                className = "refresh-text",
            ),
            html.Div(  
                children  = [
                    dcc.Dropdown(
                        className        = "custom-dropdown",
                        id               = f"{graphid}-refreshrate", 
                        options          = [
                            {"label": "200ms", "value":   200},
                            {"label": "500ms", "value":   500},
                            {"label": "  1s ", "value":  1000},
                            {"label": "  5s ", "value":  5000},
                            {"label": " 10s ", "value": 10000},
                        ],
                        value            = 1000, # default interval: 1 second
                        style            = {"font-size": 10, "color": "black"},
                        clearable        = False,
                        optionHeight     = 18,
                        persistence      = "const", # remembers the last value
                        persistence_type = "local", # session, local, or memory 
                    ),
                ],
            ), 
        ],
        style     = {
            "display":        "flex",
            "flex-direction": "row",
            "align-items":    "center",
        },
        className = "px-0 py-0 pt-0 pb-1",
    )
    
    body   = dbc.CardBody(
        children  = [
            dcc.Graph(
                id         = graphid,  # html id for referencing in callbacks
                figure     = graphfig, # initial figure displayed (until changed by callback)
                responsive = True,     # makes the graph automatically resize to parent container
                style      = {"height": "100%", "width": "100%"},
                config     = {
                    "showTips"            : False, # disable the plotly hints
                    "displaylogo"         : False,
                    "toImageButtonOptions": {
                        "format": "svg", # one of png, svg, jpeg, webp
                        "scale" : 1,     # multiplies title/legend/axis/canvas sizes by this factor
                    }
                },
            ), 
        ],
        className = "px-0 py-0 pt-2 pb-0",
    )
    
    card   = dbc.Card(
        children  = [
            header,
            body,
        ],
        className = "h-100 p-2", # h-100 makes the card take up the full available height
    )
    
    return card

def make_pcacard(title: str, graphid: str, graphfig: go.Figure, n_steps: int):
    
    header = dbc.CardHeader(
        children  = [
            html.Div(
                children = [title], 
                style    = {
                    "flex":         1, 
                    "padding-left": "0.25rem",
                },
            ),
        ],
        className = "px-0 py-0 pt-0 pb-1",
        style     = {
            "display":        "flex",
            "flex-direction": "row",
            "align-items":    "center",
        },
    )
    
    body   = dbc.CardBody(
        children = [
            dcc.Graph(
                id         = graphid,  # html id for referencing in callbacks
                figure     = graphfig, # initial figure displayed (until changed by callback)
                responsive = True,     # makes the graph automatically resize to parent container
                style      = {"height": "100%", "width": "100%"},
                config     = {
                    "showTips"            : False, # disable the plotly hints
                    "displaylogo"         : False,
                    "toImageButtonOptions": {
                        "format": "svg", # one of png, svg, jpeg, webp
                        "scale" : 1,     # multiplies title/legend/axis/canvas sizes by this factor
                    }
                },
            ), 
        ],
        className = "px-0 py-0 pt-2 pb-0",  
    )
    
    footer = dbc.CardFooter(
        children = [
            dcc.Slider(
                min        = 0, 
                max        = (n_steps - 1), 
                step       = None,
                value      = 0,
                id         = f"{graphid}-slider",
                tooltip    = {"placement": "top", "always_visible": False},
                updatemode = "drag",
                marks      = {0: {}, },
                className = "pt-0 pb-0 px-0 py-0",
            ), 
        ],
        className="px-0 py-0 pt-1 pb-0",
        
    )

    card   = dbc.Card(
        children  = [
            header,
            body,
            footer,
        ],
        className = "h-100 p-2", # h-100 makes the card take up the full available height
    )
    
    return card

def make_infocard(title: str):
    
    header = dbc.CardHeader(
        children  = [
            html.Div(
                title, 
                style = {"padding-left": "0.25rem"}
            ),
        ],
        className = "px-0 py-0 pt-0 pb-1",
        
    )
    
    body   = dbc.CardBody(
        children = [
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
            html.Div(
                " Lorem ipsum dolor sit amet, consectetur adipiscing elit. Curabitur lobortis feugiat diam, nec auctor mi feugiat at. Aliquam placerat quis purus a aliquam. Vivamus condimentum, ligula a pellentesque consequat, dolor sem pulvinar elit, eget facilisis mi ante a nulla. Donec laoreet orci neque, ac euismod nulla consectetur sed. Curabitur ullamcorper porttitor dapibus. Nam quis placerat risus, ac tempor nunc. Sed pharetra, dolor non varius viverra, ex elit varius dolor, vel dapibus orci erat quis lacus. Aenean ut arcu non nunc laoreet lacinia. Suspendisse egestas sapien est. Sed scelerisque sit amet dolor vitae convallis. Nulla facilisi. Etiam convallis sollicitudin volutpat. Aliquam erat volutpat. Morbi tristique pellentesque euismod. Integer lobortis libero mi, vitae accumsan tellus feugiat convallis. Integer laoreet erat ut suscipit lacinia. Morbi elementum arcu mi, vitae lobortis leo hendrerit vestibulum. Nullam viverra quam massa. Nulla blandit a dui a fermentum. Mauris enim ipsum, rutrum in iaculis eu, elementum vitae sapien. Nunc sollicitudin, orci eget accumsan mattis, ante arcu facilisis metus, ultrices scelerisque nisl arcu in risus. Vestibulum id libero ut ante pulvinar eleifend. Mauris vel accumsan velit. Donec sapien justo, molestie quis accumsan non, porttitor imperdiet risus. In nec consequat metus, a dapibus mauris. Suspendisse posuere suscipit nibh non fringilla. Suspendisse potenti. Maecenas malesuada, dui sed dapibus luctus, lorem elit luctus ipsum, vel rutrum orci nisl sit amet lectus. Interdum et malesuada fames ac ante ipsum primis in faucibus. Fusce orci libero, consequat in est ullamcorper, vestibulum placerat diam. Fusce nec lacus vel ipsum porttitor congue eget vel lectus. Class aptent taciti sociosqu ad litora torquent per conubia nostra, per inceptos himenaeos. Suspendisse semper magna libero, ut scelerisque velit sodales non. Aliquam nunc augue, lacinia ac mattis in, mattis vel sapien. Vestibulum id consequat lacus. Integer luctus massa et turpis ultrices maximus. Nunc elementum augue ipsum, eget pellentesque elit aliquet a. Proin vel neque enim. Mauris sit amet ex dolor. Quisque quis dui porta, luctus nulla vitae, vulputate metus. Morbi consequat eros nec fermentum fringilla. Duis laoreet, purus ac efficitur venenatis, massa massa vulputate urna, in euismod risus diam sed ipsum. Aenean sit amet sapien enim. Nullam malesuada, purus pharetra dignissim vulputate, metus nibh ultrices ante, venenatis semper libero mi vitae justo. Proin ut tempor sem. Aenean semper et nulla id porta. Sed eu pretium eros, eu vestibulum nulla. Aliquam ornare dignissim dolor, eget volutpat sem ornare congue. Suspendisse pharetra aliquam mi. Nunc dictum felis ex, in posuere tellus tincidunt eget. Cras a tincidunt orci, ut pellentesque tellus. Quisque volutpat fringilla nunc in eleifend. Maecenas arcu lorem, volutpat et accumsan vulputate, porttitor non est. Morbi diam libero, semper sed orci et, feugiat sagittis quam. Proin vehicula lorem non semper vehicula. Aenean lobortis elementum ex, vel cursus turpis porta vitae. Sed vel lacus at massa imperdiet vulputate vitae in erat. Vivamus a ultrices augue, sit amet venenatis augue. Aliquam malesuada tempus risus, at pretium nunc sodales eu. Aliquam maximus sem tortor, sed iaculis nibh tincidunt sit amet. Nam porttitor bibendum lectus, sit amet semper enim convallis id. Donec lobortis ornare justo."
            ),
        ],
        className = "px-1 py-0 pt-2 pb-0",
        style     = {
            "whiteSpace":    "normal", 
            "display":       "flex", 
            "flexDirection": "column",
            "overflowY":     "scroll",
        },
    )
    
    footer = dbc.CardFooter(
        children  = [
            html.Div(
                "just an infocard footer",
                style = {"padding-left": "0.25rem"}
            )
        ],
        className ="px-0 py-0 pt-1 pb-0",
    )
    
    card   = dbc.Card(
        children  = [
            header,
            body,
            # footer,
        ],
        className = "h-100 p-2", # h-100 makes the card take up the full available height
        id        = "infocard" # for css to format only this one
    )
    
    return card

