from .types import Order, TradeData, OrderBook

class Strategy:
	def on_trade(self, instrument_id: str, trade: TradeData, orderbook: OrderBook) -> list[Order]:
		"""
		Override this method to implement the logic for when a trade event occurs.
		
		Args:
			instrument_id: The instrument that the trade occurred on
			trade: Trade data containing price, size, and side
			orderbook: The current state of the orderbook for this instrument
		
		Returns:
			A list of orders to be sent to the exchange
		"""
		return []

	def on_order_book_change(self, instrument_id: str, orderbook: OrderBook) -> list[Order]:
		"""
		Override this method to implement the logic for when the order book changes.
		
		Args:
			instrument_id: The instrument that the orderbook changed for
			orderbook: The current state of the orderbook for this instrument
		
		Returns:
			A list of orders to be sent to the exchange
		"""
		return []

