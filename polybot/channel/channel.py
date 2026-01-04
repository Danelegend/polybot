from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional

from polybot.common.strategy_context import StrategyContext
from polybot.ids.interface import IInstrumentDefintionStore
from polybot.common.types import INSTRUMENT_ID, Order
from polybot.common.exceptions import ChannelStateError
from polybot.strategy import StrategyInterface, TradeData
from polybot.iml.interface import MarketDataConsumer, MarketDataProvider
from polybot.iml.messages import (
	OrderBookUpdateEvent,
	TradeEvent,
	OrderBookSnapshotEvent,
)

from .channel_interface import ChannelInterface
from .position_manager import PositionManager
from .strategy_router import StrategyRouter
from .order_book_manager import OrderBookManager

# Type alias for order handler callback
OrderHandler = Callable[[Order], None]

class ChannelStatus(Enum):
	INITIALIZED = 0
	RUNNING = 1
	ERROR = 2
	STOPPED = 3

@dataclass
class InstrumentWrapper:
	instrument_id: INSTRUMENT_ID
	is_tradable: bool


class Channel(ChannelInterface, MarketDataConsumer):
	def __init__(
		self,
		ids: IInstrumentDefintionStore,
		iml: MarketDataProvider,
		order_handler: Optional[OrderHandler] = None,
	):
		# From parameters
		self.ids = ids
		self.iml = iml
		self._order_handler = order_handler

		# Construct new DS
		self.instruments: dict[INSTRUMENT_ID, InstrumentWrapper] = {}

		self.orderbook_manager = OrderBookManager()
		self.strategy_router = StrategyRouter()
		self.position_manager: PositionManager = PositionManager()

		# State
		self.status = ChannelStatus.INITIALIZED


	def run(self):
		self.status = ChannelStatus.RUNNING


	def stop(self):
		self.status = ChannelStatus.STOPPED

	def add_strategy(self, strategy: StrategyInterface):
		if self.status != ChannelStatus.INITIALIZED:
			msg = f"Strategy can only be added during initialisation phase. Current status={self.status}"
			self._throw_channel_error(msg)

		instruments = strategy.get_metadata().instruments

		# Ensure all instruments are added
		for iid in instruments:
			if iid not in self.instruments: self._add_new_instrument(iid)

		# Add the strategy to the router
		view = self.strategy_router.add_strategy(strategy)

		# Add all the orderbooks to the view
		for iid in instruments:
			view.add_orderbook(iid, self.orderbook_manager.get_orderbook(iid))


	# Market Data Consumption Methods
	def on_order_book_update_event(self, event: OrderBookUpdateEvent):
		# Update the orderbook
		iid = event.instrument_id
		orderbook = self.orderbook_manager.get_orderbook(iid)
		for delta in event.deltas:
			orderbook.adjust_volume(
				delta.price,
				delta.size_delta,
				delta.side,
			)

		for strategy in self.strategy_router.get_strategies_to_run(iid):
			orders = strategy.on_order_book_change(iid, orderbook, StrategyContext(
				position_reader=self.position_manager,
				orderbooks={},
			))

			self._send_orders(orders)
		


	def on_trade_event(self, event: TradeEvent):
		iid = event.instrument_id
		orderbook = self.orderbook_manager.get_orderbook(iid)
		trade_data = TradeData(
			instrument_id=iid,
			price=event.price,
			size=event.size,
			side=event.side,
		)

		for strategy in self.strategy_router.get_strategies_to_run(iid):
			orders = strategy.on_trade(iid, trade_data, orderbook, StrategyContext(
				position_reader=self.position_manager,
				orderbooks={},
			))

			self._send_orders(orders)

	def on_order_book_snapshot_event(self, event: OrderBookSnapshotEvent):
		# Populate the orderbook
		iid = event.instrument_id

		self.orderbook_manager[iid].populate(
			bids=[
				(bid.price, bid.size) for bid in event.bids
			],
			asks=[
				(ask.price, ask.size) for ask in event.asks
			],
		)

		self.instruments[iid].is_tradable = True


	# Private methods
	def _throw_channel_error(self, msg: str):
		self.status = ChannelStatus.ERROR
		raise ChannelStateError(msg)


	def _add_new_instrument(self, iid: INSTRUMENT_ID):
		if self.status != ChannelStatus.INITIALIZED:
			msg = f"Instruments can only be added during initialisation phase. Current status={self.status}"
			self._throw_channel_error(msg)

		# Create an orderbook for this instrument
		self.orderbook_manager.create_orderbook(iid)

		# Subscribe to instrument in iml
		self.iml.subscribe(iid, self)

		self.instruments[iid] = InstrumentWrapper(iid, False)
		self.position_manager.add_position(iid, 0, 0)
	
	def _send_orders(self, orders: list[Order]):
		if self._order_handler is not None:
			for order in orders:
				self._order_handler(order)
