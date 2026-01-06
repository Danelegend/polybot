import time

from typing import Protocol

from polybot.common.types import INSTRUMENT_ID, ORDER_ID, Order, OrderRequest, OrderStatus

from .order_id_generator import generate_order_id


ActiveOrderStatus = [OrderStatus.INFLIGHT, OrderStatus.ACTIVE, OrderStatus.INFLIGHT_CANCELLED]


class IOrderReader(Protocol):
	def get_active_orders(self, iid: INSTRUMENT_ID) -> list[Order]:
		"""
		Gets all active orders for a given instrument at a point in time.

		Orders are considered active if they are in any of the following states:
		 - INFLIGHT
		 - ACTIVE
		 - INFLIGHT_CANCELLEd
		"""
		...

	def get_all_active_orders(self) -> list[Order]:
		...


class IOrderManager(Protocol):
	def add_order(self, order: OrderRequest) -> ORDER_ID:
		...

	def add_exchange_order_id(self, order_id: ORDER_ID, exchange_order_id: str):
		...

	def get_order_id_from_exchange_order_id(self, exchange_order_id: str) -> ORDER_ID:
		...

	def get_exchange_order_id_from_order_id(self, order_id: ORDER_ID) -> str:
		...

	def add_fill_quantity(self, order_id: ORDER_ID, fill_quantity: float):
		...

	def cancel_requested(self, order_id: ORDER_ID):
		...

	def order_cancelled(self, order_id: ORDER_ID):
		...


class OrderManager(IOrderManager, IOrderReader):
	def __init__(self):
		self.orders: dict[ORDER_ID, Order] = {}
		self.exchange_order_ids: dict[str, ORDER_ID] = {}


	def add_order(self, order: OrderRequest) -> ORDER_ID:
		order_id = generate_order_id()

		self.orders[order_id] = Order(
			order_id=order_id,
			instrument_id=order.instrument_id,
			side=order.side,
			order_type=order.order_type,
			price=order.price,
			quantity=order.quantity,
			status=OrderStatus.INFLIGHT,
			filled_quantity=0,
			created_at=time.time(),
			updated_at=time.time(),
		)

		return order_id

	def add_exchange_order_id(self, order_id: ORDER_ID, exchange_order_id: str):
		order = self.orders[order_id]
		
		order.exchange_order_id = exchange_order_id
		order.status = OrderStatus.ACTIVE
		order.updated_at = time.time()

		self.exchange_order_ids[exchange_order_id] = order_id

	def get_order_id_from_exchange_order_id(self, exchange_order_id: str) -> ORDER_ID:
		return self.exchange_order_ids.get(exchange_order_id)

	def get_exchange_order_id_from_order_id(self, order_id: ORDER_ID) -> str:
		return self.orders[order_id].exchange_order_id

	def add_fill_quantity(self, order_id: ORDER_ID, fill_quantity: float):
		order = self.orders[order_id]
		
		order.filled_quantity += fill_quantity
		order.updated_at = time.time()

		if order.filled_quantity == order.quantity:
			order.status = OrderStatus.FILLED

	def cancel_requested(self, order_id: ORDER_ID):
		order = self.orders[order_id]
		order.status = OrderStatus.INFLIGHT_CANCELLED
		order.updated_at = time.time()

	def order_cancelled(self, order_id: ORDER_ID):
		order = self.orders[order_id]
		order.status = OrderStatus.CANCELLED
		order.updated_at = time.time()


	def get_active_orders(self, iid: INSTRUMENT_ID) -> list[Order]:
		return [order for order in self.orders.values() if order.instrument_id == iid and order.status in ActiveOrderStatus]

	def get_all_active_orders(self) -> list[Order]:
		return [order for order in self.orders.values() if order.status in ActiveOrderStatus]
