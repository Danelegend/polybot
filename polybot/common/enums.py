from enum import Enum

class Venue(Enum):
	POLYMARKET = "polymarket"

class Side(Enum):
	BUY = "buy"
	SELL = "sell"

class OrderType(Enum):
	LIMIT = "limit"
	MARKET = "market"
