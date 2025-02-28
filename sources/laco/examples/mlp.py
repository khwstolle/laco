r"""Multilayer perceptron (MLP) example."""

import torch.nn as nn
import laco.language as L

__all__ = ["MLP"]


class HP(L.params):
    dim_in: int
    dim_out: int
    dim_hidden: float = L.ref("${mul:${.dim_in},${.dim_out}}")
    num_layers: int = 3
    activation: nn.Module = nn.ReLU


MLP = L.call(nn.Sequential)(
    L.call(nn.Linear)(),
    L.call(HP.activation)(),
    L.repeat(
        HP.num_layers,
        L.call(nn.Sequential)(
            L.call(nn.Linear)(),
            L.call(HP.activation),
        ),
    )
    L.call(nn.Linear)(),
)
