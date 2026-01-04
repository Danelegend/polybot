from pydantic import BaseModel
from typing import Union

from .enums import Side, OrderType

# Instrument IDs can be integers or strings depending on the venue
# Polymarket uses string token IDs (e.g., "0x1234...")
INSTRUMENT_ID = Union[int, str]

ORDER_ID = int
FAILED_ORDER_ID = -1 # A special value to indicate that an order failed to be sent


class Order(BaseModel):
	instrument_id: INSTRUMENT_ID
	side: Side
	order_type: OrderType
	price: float
	quantity: float

