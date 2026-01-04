from typing import Protocol, Union
from decimal import Decimal

from abc import ABC, abstractmethod
from dataclasses import dataclass

from polybot.common.enums import Side
from polybot.common.orderbook import OrderBook
from polybot.common.strategy_context import StrategyContext

from .metadata import StrategyMetaData
from .config import StrategyConfig

from polybot.common.types import INSTRUMENT_ID, Order

@dataclass(frozen=True)
class TradeData:
	instrument_id: INSTRUMENT_ID
	price: Union[float, Decimal]
	size: Union[float, Decimal]
	side: Side

class StrategyInterface(Protocol):
	def get_metadata(self) -> StrategyMetaData:
		...

	def on_trade(
		self,
		instrument_id: INSTRUMENT_ID,
		trade_data: TradeData,
		orderbook: OrderBook,
		context: StrategyContext,
	) -> list[Order]:
		"""
		Called when a trade event occurs
		"""
		...

	def on_order_book_change(
		self,
		instrument_id: INSTRUMENT_ID,
		orderbook: OrderBook,
		context: StrategyContext,
	) -> list[Order]:
		"""
		Called when the order book changes but a trade does not occur

		This includes:
		 - New order inserted
		 - Resting order cancelled
		"""
		...


class StrategyBase(ABC, StrategyInterface):
	def __init__(self):
		self._config = None

	@property
	def config(self) -> StrategyConfig:
		if self._config is None:
			raise ValueError("Strategy config not set. This strategy was not properly initialized by the factory.")
		return self._config

	@config.setter
	def config(self, value: StrategyConfig):
		self._config = value

	def get_metadata(self) -> StrategyMetaData:
		return StrategyMetaData(
			name=self.config.name,
			instruments=self.config.instrument_ids,
			enabled=self.config.enabled,
		)

	@abstractmethod
	def on_trade(
		self,
		instrument_id: INSTRUMENT_ID,
		trade_data: TradeData,
		orderbook: OrderBook,
		context: StrategyContext,
	) -> list[Order]:
		...

	@abstractmethod
	def on_order_book_change(
		self,
		instrument_id: INSTRUMENT_ID,
		orderbook: OrderBook,
		context: StrategyContext,
	) -> list[Order]:
		...

