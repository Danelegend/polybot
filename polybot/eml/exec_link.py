from typing import Protocol

from polybot.common.types import ORDER_ID, Order

class ExecLink(Protocol):
	def send_order(self, order: Order) -> ORDER_ID:
		...

	def cancel_order(self, order_id: ORDER_ID):
		...
