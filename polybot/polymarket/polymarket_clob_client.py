from typing import Literal

from polybot.common.enums import Side

from py_clob_client import ClobClient
from py_clob_client.clob_types import OrderType, OrderArgs
from py_clob_client.order_builder.constants import BUY, SELL

def send_order(clob_client: ClobClient, price: float, quantity: float, side: Side, token_id: str):
	clob_side = internal_side_to_clob_side(side)
	order_args = OrderArgs(
		token_id=token_id,
		price=price,
		size=quantity,
		side=clob_side,
	)

	signed_order = clob_client.create_order(order_args)
	result = clob_client.post_order(signed_order, OrderType.GTD)


def cancel_order(clob_client: ClobClient, exchange_order_id: str):
	clob_client.cancel(order_id=exchange_order_id)


def internal_side_to_clob_side(side: Side) -> Literal[BUY, SELL]:
	if side == Side.BUY:
		return BUY
	elif side == Side.SELL:
		return SELL
	else:
		raise ValueError(f"Invalid side: {side}")