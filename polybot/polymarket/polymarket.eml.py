from polybot.eml import ExecLink
from polybot.common.types import ORDER_ID, Order

class PolymarketEml(ExecLink):
	def send_order(self, order: Order) -> ORDER_ID:
		...

	def cancel_order(self, order_id: ORDER_ID):
		...
