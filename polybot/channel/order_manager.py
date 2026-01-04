from typing import Protocol

from polybot.common.types import ORDER_ID, Order, INSTRUMENT_ID

class IOrderWriter(Protocol):
	def add_order(self, order: Order) -> ORDER_ID:
		...

class IOrderReader(Protocol):
	def get_orders(self, iid: INSTRUMENT_ID) -> list[Order]:
		...
