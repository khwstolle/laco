r"""
Configuration reader for WandB.

This module provides functionalities to read configurations from WandB runs,
allowing users to easily access and utilize their experiment parameters.
"""

from omegaconf import DictConfig


def read_config(run: str) -> DictConfig:
    import laco
    import wandb

    api = wandb.Api()
    run = api.run(run)
    return laco.utils.as_omegadict(run.config)
