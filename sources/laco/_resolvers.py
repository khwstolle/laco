import math

from omegaconf import OmegaConf

__all__ = []


OmegaConf.register_new_resolver("sum", lambda *numbers: sum(numbers))
OmegaConf.register_new_resolver("min", lambda *numbers: min(numbers))
OmegaConf.register_new_resolver("max", lambda *numbers: max(numbers))
OmegaConf.register_new_resolver("div", lambda a, b: a / b)
OmegaConf.register_new_resolver("pow", lambda a, b: a**b)
OmegaConf.register_new_resolver("mod", lambda a, b: a % b)
OmegaConf.register_new_resolver("neg", lambda a: -a)
OmegaConf.register_new_resolver("reciprocal", lambda a: 1 / a)
OmegaConf.register_new_resolver("abs", lambda a: abs(a))
OmegaConf.register_new_resolver("round", lambda a, b: round(a, b))
OmegaConf.register_new_resolver("math", lambda name, *args: getattr(math, name)(args))
