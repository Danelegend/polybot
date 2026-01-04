from typing import Type

from .config import StrategyConfig
from .strategy import StrategyBase

def create_strategy(config: StrategyConfig) -> StrategyBase:
    return _build(config.cls, config)


def _build(cls: Type[StrategyBase], config: StrategyConfig) -> StrategyBase:
    obj = cls()
    obj.config = config
    return obj

