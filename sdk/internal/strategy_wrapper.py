from polybot.strategy import StrategyBase, TradeData as CoreTradeData
from polybot.common.types import OrderRequest as CoreOrder, INSTRUMENT_ID
from polybot.common.orderbook import OrderBook
from polybot.common.context_provider import ContextProvider
from polybot.common.enums import OrderType

from sdk.base_strategy import Strategy
from sdk.types import Order as SDKOrder, TradeData as SDKTradeData
from sdk.enums import Side as SDKSide

from typing import Type


class StrategyWrapper(StrategyBase):
	def __init__(self, strat_cls: Type[Strategy]):
		super().__init__()
		self._internal = strat_cls()

	def on_trade(
		self,
		instrument_id: INSTRUMENT_ID,
		trade_data: CoreTradeData,
		orderbook: OrderBook,
		context: ContextProvider,
	) -> list[CoreOrder]:
		# Convert core trade data to SDK trade data
		sdk_trade = SDKTradeData(
			instrument_id=str(instrument_id),
			price=trade_data.price,
			size=trade_data.size,
			side=SDKSide(trade_data.side.value),
		)
		
		return [
			_convert_sdk_order_to_core_order(order)
			for order in self._internal.on_trade(str(instrument_id), sdk_trade, orderbook)
		]

	def on_order_book_change(
		self,
		instrument_id: INSTRUMENT_ID,
		orderbook: OrderBook,
		context: ContextProvider,
	) -> list[CoreOrder]:
		return [
			_convert_sdk_order_to_core_order(order)
			for order in self._internal.on_order_book_change(str(instrument_id), orderbook)
		]
		

def _convert_sdk_order_to_core_order(order: SDKOrder) -> CoreOrder:
	"""Convert an SDK Order to a Core Order"""
	from polybot.common.enums import Side as CoreSide
	
	return CoreOrder(
		instrument_id=order.instrument_id,
		side=CoreSide(order.side.value),
		order_type=OrderType.LIMIT,
		price=float(order.price),
		quantity=float(order.volume),
	)
