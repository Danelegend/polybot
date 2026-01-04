from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import List
from polybot.common.enums import Side, Venue
from polybot.common.types import INSTRUMENT_ID

class MarketEventType(Enum):
	ORDER_BOOK_SNAPSHOT = "ORDER_BOOK_SNAPSHOT"
	ORDER_BOOK_UPDATE = "ORDER_BOOK_UPDATE"
	TRADE = "TRADE"

@dataclass(frozen=True)
class LevelDelta:
	price: Decimal
	size_delta: Decimal  # Positive for Add, Negative for Cancel
	side: Side

@dataclass(frozen=True)
class Level:
	price: Decimal
	size: Decimal

@dataclass(frozen=True)
class MarketEvent:
	venue: Venue
	instrument_id: INSTRUMENT_ID
	timestamp: int  # Use Unix ns or ms for faster comparisons than datetime objects

@dataclass(frozen=True)
class OrderBookSnapshotEvent(MarketEvent):
	bids: List[Level]
	asks: List[Level]
	event_type: MarketEventType = MarketEventType.ORDER_BOOK_SNAPSHOT

@dataclass(frozen=True)
class OrderBookUpdateEvent(MarketEvent):
	deltas: List[LevelDelta]
	event_type: MarketEventType = MarketEventType.ORDER_BOOK_UPDATE

@dataclass(frozen=True)
class TradeEvent(MarketEvent):
	price: Decimal
	size: Decimal
	side: Side  # The side of the Taker
	event_type: MarketEventType = MarketEventType.TRADE
