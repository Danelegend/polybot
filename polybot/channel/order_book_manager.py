from typing import Protocol

from polybot.common.types import INSTRUMENT_ID
from polybot.common.orderbook import OrderBook

class IOrderBookWriter(Protocol):
	def create_orderbook(self, instrument_id: INSTRUMENT_ID):
		...


class IOrderBookReader(Protocol):
	def get_orderbook(self, instrument_id: INSTRUMENT_ID) -> OrderBook:
		...


class OrderBookManager(IOrderBookWriter, IOrderBookReader):
	def __init__(self):
		self.orderbooks: dict[INSTRUMENT_ID, OrderBook] = {}

	def create_orderbook(self, instrument_id: INSTRUMENT_ID):
		self.orderbooks[instrument_id] = OrderBook()

	def get_orderbook(self, instrument_id: INSTRUMENT_ID) -> OrderBook:
		return self.orderbooks[instrument_id]

	def __getitem__(self, instrument_id: INSTRUMENT_ID) -> OrderBook:
		return self.get_orderbook(instrument_id)