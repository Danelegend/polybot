from typing import Protocol

from polybot.common.types import ORDER_ID
from polybot.common.types import OrderRequest

class ExecLink(Protocol):
	def send_order(self, order: OrderRequest) -> ORDER_ID:
		...

	def cancel_order(self, order_id: ORDER_ID):
		...


class ExecLinkHandler(Protocol):
	def post_send_order(self, order: OrderRequest) -> ORDER_ID:
		...

	def post_cancel_order(self, order_id: ORDER_ID):
		...


class IGenericExchangeLink(Protocol):
	def send_order(self, order: OrderRequest):
		...

	def cancel_order(self, exchange_order_id: str):
		...

