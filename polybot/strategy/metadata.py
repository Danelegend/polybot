from dataclasses import dataclass

from polybot.common.types import INSTRUMENT_ID

@dataclass
class StrategyMetaData:
	name: str

	instruments: list[INSTRUMENT_ID] # Instruments that this strategy cares about

	enabled: bool