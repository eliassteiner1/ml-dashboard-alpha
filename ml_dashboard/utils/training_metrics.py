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






