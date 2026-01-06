from dataclasses import dataclass
from enum import Enum
from typing import Callable

from polybot.common.context_provider import ContextBuilder, ContextProvider
from polybot.ids.interface import IInstrumentDefintionStore
from polybot.common.types import INSTRUMENT_ID, OrderRequest
from polybot.common.exceptions import ChannelStateError
from polybot.strategy import StrategyInterface, TradeData
from polybot.iml.interface import MarketDataConsumer, MarketDataProvider
from polybot.iml.messages import (
	OrderBookUpdateEvent,
	TradeEvent,
	OrderBookSnapshotEvent,
)
from polybot.eml import ExecLink

from .channel_interface import ChannelInterface
from .strategy_router import StrategyRouter
from .order_book_manager import OrderBookManager

# Type alias for order handler callback
OrderHandler = Callable[[OrderRequest], None]

class ChannelStatus(Enum):
	"""Enum representing the lifecycle states of a Channel."""
	INITIALIZED = 0
	RUNNING = 1
	ERROR = 2
	STOPPED = 3


@dataclass
class InstrumentWrapper:
	"""Wrapper for instrument tracking within the channel."""
	instrument_id: INSTRUMENT_ID
	is_tradable: bool


class Channel(ChannelInterface, MarketDataConsumer):
	"""
	Channel coordinates market data consumption, strategy execution, and order routing.
	
	The Channel manages the lifecycle of strategies, maintains order books for subscribed
	instruments, and routes market data events to registered strategies.
	"""
	
	def __init__(
		self,
		ids: IInstrumentDefintionStore,
		iml: MarketDataProvider,
		eml: ExecLink,
		context_builder: ContextBuilder,
	):
		"""
		Initialize the Channel with required dependencies.
		
		Args:
			ids: Instrument definition store for looking up instrument metadata
			iml: Market data provider for subscribing to market data
			eml: Execution link for sending orders
			context_builder: Builder for creating strategy execution contexts
		"""
		# From parameters
		self.ids = ids
		self.iml = iml
		self.eml = eml
		self.context_builder = context_builder

		# Construct new data structures
		self.instruments: dict[INSTRUMENT_ID, InstrumentWrapper] = {}
		self.orderbook_manager = OrderBookManager()
		self.strategy_router = StrategyRouter()

		# State
		self.status = ChannelStatus.INITIALIZED


	def run(self) -> None:
		"""Start the channel, enabling market data processing."""
		self.status = ChannelStatus.RUNNING

	def stop(self) -> None:
		"""Stop the channel, disabling market data processing."""
		self.status = ChannelStatus.STOPPED

	def add_strategy(self, strategy: StrategyInterface) -> None:
		"""
		Register a strategy with the channel.
		
		This method:
		1. Validates the channel is in INITIALIZED state
		2. Ensures all required instruments are registered
		3. Adds the strategy to the routing table
		4. Provides the strategy with access to relevant orderbooks
		
		Args:
			strategy: The strategy to register
			
		Raises:
			ChannelStateError: If the channel is not in INITIALIZED state
		"""
		if self.status != ChannelStatus.INITIALIZED:
			msg = f"Strategy can only be added during initialisation phase. Current status={self.status}"
			self._throw_channel_error(msg)

		metadata = strategy.get_metadata()
		instruments = metadata.instruments

		# Ensure all instruments are added
		for iid in instruments:
			if iid not in self.instruments:
				self._add_new_instrument(iid)

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

		# Notify strategies and collect orders
		context = self._build_context()
		for strategy in self.strategy_router.get_strategies_to_run(iid):
			orders = strategy.on_order_book_change(iid, orderbook, context)
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

		# Notify strategies and collect orders
		context = self._build_context()
		for strategy in self.strategy_router.get_strategies_to_run(iid):
			orders = strategy.on_trade(iid, trade_data, orderbook, context)
			self._send_orders(orders)

	def on_order_book_snapshot_event(self, event: OrderBookSnapshotEvent):
		# Populate the orderbook
		iid = event.instrument_id
		
		# Populate the orderbook with snapshot data
		orderbook = self.orderbook_manager.get_orderbook(iid)
		orderbook.populate(
			bids=[(bid.price, bid.size) for bid in event.bids],
			asks=[(ask.price, ask.size) for ask in event.asks],
		)

		self.instruments[iid].is_tradable = True

		context = self._build_context()
		for strategy in self.strategy_router.get_strategies_to_run(iid):
			orders = strategy.on_order_book_change(iid, orderbook, context)
			self._send_orders(orders)


	# Private methods
	def _throw_channel_error(self, msg: str) -> None:
		"""
		Transition the channel to ERROR state and raise an exception.
		
		Args:
			msg: Error message describing the issue
			
		Raises:
			ChannelStateError: Always raised with the provided message
		"""
		self.status = ChannelStatus.ERROR
		raise ChannelStateError(msg)

	def _add_new_instrument(self, iid: INSTRUMENT_ID) -> None:
		"""
		Register a new instrument with the channel.
		
		This method:
		1. Validates the channel is in INITIALIZED state
		2. Creates an orderbook for the instrument
		3. Subscribes to market data for the instrument
		4. Tracks the instrument in the channel's registry
		
		Args:
			iid: Instrument ID to register
			
		Raises:
			ChannelStateError: If the channel is not in INITIALIZED state
		"""
		if self.status != ChannelStatus.INITIALIZED:
			msg = f"Instruments can only be added during initialisation phase. Current status={self.status}"
			self._throw_channel_error(msg)

		# Create an orderbook for this instrument
		self.orderbook_manager.create_orderbook(iid)

		# Subscribe to instrument in iml
		self.iml.subscribe(iid, self)

		# Track instrument (not yet tradable until we receive snapshot)
		self.instruments[iid] = InstrumentWrapper(iid, False)
	
	def _send_orders(self, orders: list[OrderRequest]) -> None:
		"""
		Send a batch of orders to the execution link.
		
		Args:
			orders: List of order requests to send
		"""
		if not orders:
			return
			
		for order in orders:
			try:
				self.eml.send_order(order)
			except Exception as e:
				raise e
	
	def _build_context(self) -> ContextProvider:
		"""
		Build a context object for strategy execution.
		
		Returns:
			ContextProvider instance for use by strategies
		"""
		return self.context_builder.build_context({})
