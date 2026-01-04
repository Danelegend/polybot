from dataclasses import dataclass
from decimal import Decimal
from pydantic import BaseModel
from pydantic import condecimal

from .enums import Side

# Re-export OrderBook from polybot.common for SDK use
from polybot.common.orderbook import OrderBook


@dataclass(frozen=True)
class TradeData:
	"""
	Information about a trade that occurred on the exchange.
	
	Attributes:
		instrument_id: The instrument the trade occurred on
		price: The price at which the trade occurred
		size: The size of the trade
		side: The side of the taker (BUY or SELL)
	"""
	instrument_id: str
	price: Decimal
	size: Decimal
	side: Side


class Order(BaseModel):
	"""
	An order is a request to buy or sell a specific instrument at a specific price.

	As of current, ONLY LIMIT ORDERS ARE SUPPORTED.
	The rationale is that with a market order, you do not know the price at which the order will be executed.
	"""
	instrument_id: str # The instrument for which the order is being placed for
	
	side: Side # Is this a buy or a sell order

	price: condecimal(gt=0) # The maximum price at which the order will be executed. Must be greater than 0.

	volume: condecimal(gt=0) # The number of units of the instrument to be traded. Must be greater than 0.

	


class InstrumentLimit(BaseModel):
	"""
	Limits to be applied to a specific instrument

	Position limit refers to the maximum number of units that can be held on the bid or ask side (sum of volumes).
	Nominal position limit refers to the maximum value that can be held on the bid or ask side (price * volume).
	
	Before placing an order, we validate that no limit is violated.
	"""
	instrument_id: str # The instrument for which the order is being placed

	max_position_bid: condecimal(gt=0) # The maximum number of units that can be held on the bid side. Must be greater than 0.
	max_position_ask: condecimal(gt=0) # The maximum number of units that can be held on the ask side. Must be greater than 0.
	
	max_nominal_position_bid: condecimal(gt=0) # The maximum value that can be held on the bid side. Must be greater than 0.
	max_nominal_position_ask: condecimal(gt=0) # The maximum value that can be held on the ask side. Must be greater than 0.
