r"""Multilayer perceptron (MLP) example."""

import laco.language as L
from torch import nn

__all__ = ["MLP", "HP"]


@L.params
class HP:
    dim_in: int = 128
    dim_out: int = 128
    dim_hidden: int = 256
    num_layers: int = 3
    activation: type[nn.Module] = nn.ReLU


MLP = L.call(nn.Sequential)(
    L.call(nn.Linear)(
        in_features=HP.dim_in,
        out_features=HP.dim_hidden,
    ),
    L.call(HP.activation)(),
    L.repeat(
        HP.num_layers,
        L.call(nn.Sequential)(
            L.call(nn.Linear)(
                in_features=HP.dim_hidden,
                out_features=HP.dim_hidden,
            ),
            L.call(HP.activation)(),
        ),
    ),
    L.call(nn.Linear)(
        in_features=HP.dim_hidden,
        out_features=HP.dim_out,
    ),
)
