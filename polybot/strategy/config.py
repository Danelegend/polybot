from dataclasses import dataclass
from typing import TYPE_CHECKING, Type

if TYPE_CHECKING:
	from polybot.strategy.strategy import StrategyBase

@dataclass
class StrategyConfig:
	name: str # The name of this strategy instance

	instrument_ids: list[str] # The instrument ids that this instance should be run for

	cls: Type["StrategyBase"] # The class of the strategy implementation

	enabled: bool = True # Whether this strategy instance should be run
