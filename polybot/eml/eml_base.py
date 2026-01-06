from polybot.common.types import FAILED_ORDER_ID, ORDER_ID
from polybot.common.types import OrderRequest
from polybot.limits import ILimitStore
from polybot.state import IOrderManager

from .interface import ExecLink, ExecLinkHandler, IGenericExchangeLink

class ExecutionLink(ExecLink, ExecLinkHandler):
	def __init__(
		self,
		venue_gem: IGenericExchangeLink,
		limit_store: ILimitStore,
		order_manager: IOrderManager,
	):
		self._handler: ExecLinkHandler = self
		self._gem = venue_gem
		self._limit_store = limit_store
		self._order_manager = order_manager
	
	# ExecLink Methods: These methods should be done as quickly as possible
	# since it is done in the critical path
	def send_order(self, order: OrderRequest) -> ORDER_ID:
		limit_result = self._limit_store.try_reserve_capacity(
			order.instrument_id,
			order.side,
			order.quantity,
			order.price,
		)

		if not limit_result.allowed:
			return FAILED_ORDER_ID

		self._gem.send_order(order)

		return self._handler.post_send_order(order)
	
	def cancel_order(self, order_id: ORDER_ID):
		exchange_order_id = self._order_manager.get_exchange_order_id_from_order_id(order_id)

		self._gem.cancel_order(exchange_order_id)

		self._handler.post_cancel_order(order_id)

	# ExecLinkHandler Methods: Orders have been sent, we are now out of the critical path
	def post_send_order(self, order: OrderRequest) -> ORDER_ID:
		order_id = self._order_manager.add_order(order)
		
		return order_id

	def post_cancel_order(self, order_id: ORDER_ID):
		self._order_manager.cancel_requested(order_id)