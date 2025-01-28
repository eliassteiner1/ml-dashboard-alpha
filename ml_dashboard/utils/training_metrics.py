import torch
import torch.nn as nn


def calc_net_nparams(net: nn.Module, only_trainable: bool = False) -> int:
    """calculates the number of parameters in a network"""
    
    if not isinstance(net, nn.Module):
        raise TypeError(f"net must be an instance of nn.Module, got {type(net).__name__} instead.")
    
    if only_trainable is True:
        return sum(torch.numel(p) for p in net.parameters() if p.requires_grad is True)
    else:
        return sum(torch.numel(p) for p in net.parameters())

def calc_net_weightnorm(net: nn.Module, only_trainable: bool = False) -> float:
    """just calculates the parameter weight norm of a network"""
    
    if not isinstance(net, nn.Module):
        raise TypeError(f"net must be an instance of nn.Module, got {type(net).__name__} instead.")
    
    with torch.no_grad():
        if only_trainable is True:
            return (sum(torch.sum(p**2) for p in net.parameters() if p.requires_grad is True)**0.5).item()
        else:
            return (sum(torch.sum(p**2) for p in net.parameters())**0.5).item()
        
def calc_net_gradnorm(net: nn.Module) -> torch.Tensor:
    """just calculates the gradient norm of a network. Call before gradients have been zeroed!"""
    
    if not isinstance(net, nn.Module):
        raise TypeError(f"net must be an instance of nn.Module, got {type(net).__name__} instead.")
    
    with torch.no_grad():
        grad_norm = sum(torch.sum(p.grad**2) for p in net.parameters() if p.grad is not None)**0.5
    
    if grad_norm == 0:
        raise ValueError("No gradients found in the network. Ensure backward() is called before this function.")
    
    return grad_norm.item()

def calc_adam_rates(net: nn.Module, opt: torch.optim.Optimizer) -> tuple[float, float]:
    """calculate the effective update rate and effective learning rate for an adam optimizer"""
    
    if not isinstance(net, nn.Module):
        raise TypeError(f"net must be an instance of nn.Module, got {type(net).__name__} instead.")
    if not isinstance(opt, torch.optim.Adam):
        raise TypeError("The optimizer must be an instance of torch.optim.Adam")

    eff_lr_norm  = 0.0
    eff_udr_norm = 0.0
    
    # extract all the optimizer parameters
    BETA1, BETA2 = opt.state_dict()["param_groups"][0]["betas"]
    LR           = opt.state_dict()["param_groups"][0]["lr"]
    EPSILON      = opt.state_dict()["param_groups"][0].get("eps", 10**-8)
    state        = opt.state_dict()["state"] # contains all the information for each param
        
    key_idx = 0
    for p in net.parameters():
        if (p.requires_grad is False) or (p.grad is None):
            key_idx += 1
            continue
 
        state_v = state[key_idx]
        step    = state_v["step"]
        m1      = state_v["exp_avg"]
        m2      = state_v["exp_avg_sq"]
        m1_corr = m1 / (1 - BETA1**step) # makes momentum really big at the beginning (when step is small)
        m2_corr = m2 / (1 - BETA2**step) # makes momentum really big at the beginning (when step is small)
        
        eff_lr  = (LR * m1_corr) / (torch.sqrt(m2_corr) + EPSILON) # epsilon just for numerical stability
        eff_udr = p.grad * eff_lr
        
        eff_lr_norm  += torch.sum(eff_lr**2)
        eff_udr_norm += torch.sum(eff_udr**2)
        
        key_idx += 1
        
    if (eff_lr_norm == 0) or (eff_udr_norm == 0):
        raise ValueError("no gradients or optimizer state found!")
    
    return (eff_lr_norm**0.5).item(), (eff_udr_norm**0.5).item()





