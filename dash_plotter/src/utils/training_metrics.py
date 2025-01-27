import torch
import torch.nn as nn


def calc_network_info(net: nn.Module, opt: torch.optim.Optimizer):
    """
    calculate the effective update rate by getting the effective LR for each param and then multiplying this LR with the gradient for each parameter.
    
    outputs all at once for ADAM optimizer: gradient norm, eff. LR norm and eff. updaterate norm
    """
    
    n_params    = 0
    grads       = []
    eff_LRs     = []
    grad_norm   = 0
    eff_LR_norm = 0
    eff_udrate  = 0
    
    # grab all gradient tensors
    for p in net.parameters():
        grads.append(p.grad)
        n_params += torch.numel(p)
    
    # grab all effective LR tensors
    beta1, beta2 = opt.state_dict()["param_groups"][0]["betas"]
    LR           = opt.state_dict()["param_groups"][0]["lr"]
    epsilon      = opt.state_dict()["param_groups"][0].get("eps", 10**-8)
    for key, value in opt.state_dict()["state"].items():
        step    = value["step"]
        m1      = value["exp_avg"]
        m2      = value["exp_avg_sq"]
        m1_corr = m1 / (1 - beta1**step)
        m2_corr = m2 / (1 - beta2**step)
        eff_LR  = (LR * m1_corr) / (torch.sqrt(m2_corr) + epsilon)
        eff_LRs.append(eff_LR)
    
    # calculate effective update rate, grad norm and effective LR
    for grad, eff_LR in zip(grads, eff_LRs): # TODO: check if grads and eff_LRs match up!
        grad_norm   += torch.sum(grad**2)
        eff_LR_norm += torch.sum(eff_LR**2)
        eff_udrate  += torch.sum((grad * eff_LR)**2)

    return grad_norm**0.5, eff_LR_norm**0.5, eff_udrate**0.5


def calc_net_gradnorm(net: nn.Module):
    """just calculates the gradient norm of a network. Call before gradients have been zeroed!"""
    grad_norm = 0
    for p in net.parameters():
        grad_norm += torch.sum(p.grad**2)
    
    return grad_norm**0.5

def calc_net_weightnorm(net: nn.Module):
    """just calculates the parameter weight norm of a network"""
    weight_norm = 0
    for p in net.parameters():
        weight_norm += torch.sum(p**2)
        
    return weight_norm**0.5
