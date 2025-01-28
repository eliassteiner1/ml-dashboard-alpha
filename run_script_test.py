import time
import numpy as np
from ml_dashboard import DashPlotter, calc_net_gradnorm, calc_net_nparams, calc_net_weightnorm


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
        
        PLOTTER._store["proc_speed"].append(np.random.rand() * 100_000)
                
        i += 1
        
        time.sleep(0.3)
    
    PLOTTER.run_script_spin()