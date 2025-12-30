from pydantic import BaseModel
from typing import Literal
from datetime import datetime
from decimal import Decimal
from enum import Enum

from polybot.common.enums import Venue

class MarketEventType(Enum):
    PRICE_CHANGE = "PRICE_CHANGE"
    TRADE = "TRADE"
    ORDER_BOOK_SNAPSHOT = "ORDER_BOOK_SNAPSHOT"

class MarketEvent(BaseModel):
    venue: Venue
    instrument_id: str
    timestamp: datetime
    event_type: MarketEventType

class OrderbookLevel(BaseModel):
    price: Decimal
    size: Decimal

class PriceChangeEvent(BaseModel):
    event_type: MarketEventType.PRICE_CHANGE

    best_bid: Decimal               # top bid price
    best_bid_size: Decimal          # quantity available at top bid
    best_ask: Decimal               # top ask price
    best_ask_size: Decimal          # quantity available at top ask
    last_price: Decimal             # last traded price (if available)
    mid_price: Decimal              # optional, computed as (bid+ask)/2
    volume: Decimal                 # optional, total traded volume


class TradeEvent(MarketEvent):
    event_type: MarketEventType.TRADE
    
    trade_id: str                   # unique id for the trade
    side: Literal["BUY", "SELL"]    # aggressor side
    price: Decimal                  # executed price
    size: Decimal                   # executed size
    maker_order_id: str = None      # optional
    taker_order_id: str = None      # optional


class OrderbookSnapshotEvent(MarketEvent):
    event_type: MarketEventType.ORDER_BOOK_SNAPSHOT
    
    bids: list[OrderBookLevel]  # [(price, size), ...] descending
    asks: list[OrderBookLevel]  # [(price, size), ...] ascending

