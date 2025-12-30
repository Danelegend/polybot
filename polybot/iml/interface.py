from typing import Protocol

from .messages import (
    PriceChangeEvent,
    TradeEvent,
    OrderbookSnapshotEvent,
)

class MarketDataConsumer(Protocol):
    def on_price_change_event(self, event: PriceChangeEvent):
        ...

    def on_trade_event(self, event: TradeEvent):
        ...

    def on_order_book_snapshot_event(self, event: OrderbookSnapshotEvent):
        ...


class MarketDataProvider(Protocol):
    def subscribe(self, instrument_id: str, consumer: MarketDataConsumer):
        ...

