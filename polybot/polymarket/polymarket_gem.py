from polybot.common.types import OrderRequest
from polybot.eml import IGenericExchangeLink

from .credentials import PolymarketCredentials
from .credentials import to_clob_client

from .polymarket_clob_client import send_order


class PolymarketGem(IGenericExchangeLink):
	def __init__(self, credentials: PolymarketCredentials):
		self._clob_client = to_clob_client(credentials)
	
	def send_order(self, order: OrderRequest):
		send_order(self._clob_client, order.price, order.quantity, order.side, order.instrument_id)

	def cancel_order(self, exchange_order_id: str):
		pass