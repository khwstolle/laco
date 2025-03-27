r"""Multilayer perceptron (MLP) example."""

import laco.language as L
from torch import nn

__all__ = ["model", "hps"]


@L.params
class hps:
    dim_in: int = 128
    dim_out: int = 128
    dim_hidden: int = 256
    num_layers: int = 3
    activation: type[nn.Module] = nn.ReLU


model = L.bind(nn.Sequential)(
    L.OrderedDict(
        (
            "input",
            L.call(nn.Sequential)(
                L.call(nn.Linear)(
                    in_features=hps.dim_in,
                    out_features=hps.dim_hidden,
                ),
                L.call(hps.activation)(),
            ),
        ),
        (
            "hidden",
            L.call(nn.Sequential, expand_args=True)(
                L.repeat(
                    hps.num_layers,
                    L.call(nn.Sequential)(
                        L.call(nn.Linear)(
                            in_features=hps.dim_hidden,
                            out_features=hps.dim_hidden,
                        ),
                        L.call(hps.activation)(),
                    ),
                ),
            ),
        ),
        (
            "output",
            L.call(nn.Sequential)(
                L.call(nn.Linear)(
                    in_features=hps.dim_hidden,
                    out_features=hps.dim_out,
                )
            ),
        ),
    )
)
