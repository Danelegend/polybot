from typing import Protocol

from .messages import (
	TradeEvent,
	OrderBookSnapshotEvent,
	OrderBookUpdateEvent,
)

from polybot.common.types import INSTRUMENT_ID

class MarketDataConsumer(Protocol):
	def on_order_book_snapshot_event(self, event: OrderBookSnapshotEvent):
		"""
		A full snapshot of the order book at a given point in time
		"""
		...

	def on_order_book_update_event(self, event: OrderBookUpdateEvent):
		"""
		An event indicating that the order book has been updated
		"""
		...

	def on_trade_event(self, event: TradeEvent):
		"""
		An event indicating that a trade has occurred
		"""
		...


class MarketDataProvider(Protocol):
	def subscribe(self, instrument_id: INSTRUMENT_ID, consumer: MarketDataConsumer):
		...

