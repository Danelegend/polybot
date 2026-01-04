from typing import Protocol

from polybot.common.types import FAILED_ORDER_ID, ORDER_ID
from polybot.common.types import Order
from polybot.limits import ILimitStore

from .interface import ExecLink

class EmlBase(ExecLink):
	def __init__(
		self,
		venue_impl: ExecLink,
		limit_store: ILimitStore,
	):
		self._venue_impl = venue_impl
		self._limit_store = limit_store

	def send_order(self, order: Order) -> ORDER_ID:
		limit_result = self._limit_store.try_reserve_capacity(
			order.instrument_id,
			order.side,
			order.quantity,
			order.price,
		)

		if not limit_result.allowed:
			return FAILED_ORDER_ID

		order_id = self._venue_impl.send_order(order)

		return order_id
	
	def cancel_order(self, order_id: ORDER_ID):
		self._venue_impl.cancel_order(order_id)