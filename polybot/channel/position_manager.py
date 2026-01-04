from dataclasses import dataclass
from collections import defaultdict
from typing import Protocol

from polybot.common.types import INSTRUMENT_ID

@dataclass
class Position:
	iid: INSTRUMENT_ID
	volume: float
	price: float

	def get_nominal_value(self) -> float:
		return self.volume * self.price



class IPositionWriter(Protocol):
	def add_position(self, iid: INSTRUMENT_ID, volume: float, price: float): # Negative volume means sell
		...


class IPositionReader(Protocol):
	def get_total_volume(self, iid: INSTRUMENT_ID) -> float:
		...

	def get_total_nominal_value(self, iid: INSTRUMENT_ID) -> float:
		...


class PositionManager(IPositionWriter, IPositionReader):
	def __init__(self):
		self.positions: dict[INSTRUMENT_ID, dict[float, Position]] = defaultdict(dict)
	
	def get_total_volume(self, iid: INSTRUMENT_ID) -> float:
		return sum(position.volume for position in self.positions[iid].values())

	def add_position(self, iid: INSTRUMENT_ID, volume: float, price: float):
		if price in self.positions[iid]:
			self.positions[iid][price].volume += volume
		else:
			self.positions[iid][price] = Position(iid, volume, price)

	def get_total_nominal_value(self, iid: INSTRUMENT_ID) -> float:
		return sum(position.get_nominal_value() for position in self.positions[iid].values())

