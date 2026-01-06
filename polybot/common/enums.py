from enum import Enum

class Venue(Enum):
	POLYMARKET = "polymarket"


class Side(Enum):
	BUY = "buy"
	SELL = "sell"


class OrderType(Enum):
	LIMIT = "limit"
	MARKET = "market"


class OrderStatus(Enum):
	INFLIGHT = "inflight_active"    				# Order has been sent to the exchange and is active
	ACTIVE = "active"        						# Order has been confirmed by the exchange and is active
	INFLIGHT_CANCELLED = "inflight_cancelled"    	# Order has been sent to the exchange but has not yet been confirmed
	CANCELLED = "cancelled"  						# Order has been cancelled by the user
	FILLED = "filled"        						# Order has been filled
	EXPIRED = "expired"      						# Order has expired

