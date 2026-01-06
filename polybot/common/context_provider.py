from dataclasses import dataclass

from polybot.state import IPositionReader
from polybot.state import IOrderReader
from polybot.common.types import INSTRUMENT_ID
from polybot.common.orderbook import OrderBook
from typing import Mapping


@dataclass
class ContextProvider:
	position_reader: IPositionReader
	order_reader: IOrderReader
	orderbooks: Mapping[INSTRUMENT_ID, OrderBook]


class ContextBuilder:
	def __init__(
		self,
		position_reader: IPositionReader,
		order_reader: IOrderReader,
	):
		self.position_reader = position_reader
		self.order_reader = order_reader

	def build_context(self, orderbooks: Mapping[INSTRUMENT_ID, OrderBook]) -> ContextProvider:
		return ContextProvider(
			position_reader=self.position_reader,
			order_reader=self.order_reader,
			orderbooks=orderbooks,
		)
