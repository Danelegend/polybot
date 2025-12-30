from polybot.iml import ImlBase, MarketDataConsumer
from polybot.iml import (
    OrderbookSnapshotEvent as ImlOrderbookSnapshotEvent,
    PriceChangeEvent as ImlPriceChangeEvent,
    OrderbookLevel as ImlOrderbookLevel,
)
from polybot.common.enums import Venue

from .interfaces import PolymarketMessageHandler
from .polymarket_ws import PolyMarketWebSocket
from .types.messages import (
    OrderBookSummaryEvent,
    PriceChangeEvent,
    TickSizeChangeEvent,
    LastTradePriceEvent,
    PriceChange,
)

from decimal import Decimal

class PolymarketIml(ImlBase, PolymarketMessageHandler):
    def __init__(self):
        super().__init__()

        self.ws = PolyMarketWebSocket(self)

    def subscribe(self, instrument_id: str, consumer: MarketDataConsumer):
        super().subscribe(instrument_id, consumer)

        self.ws.subscribe_to_market(instrument_id)
    
    def handle_order_book_summary_event(self, event: OrderBookSummaryEvent):
        self.emit_message(
            order_book_summary_event_to_market_event(
                event
            )
        )

    def handle_price_change_event(self, event: PriceChangeEvent):
        ...

    def handle_tick_size_change_event(self, event: TickSizeChangeEvent):
        return

    def handle_last_trade_price_event(self, event: LastTradePriceEvent):
        return


def order_book_summary_event_to_market_event(event: OrderBookSummaryEvent) -> OrderbookSnapshotEvent:
    return ImlOrderbookSnapshotEvent(
        venue=Venue.POLYMARKET,
        instrument_id=event.token_id,
        timestamp=event.timestamp,
        bids=[
            ImlOrderbookLevel(price=Decimal(order.price), size=Decimal(order.size))
            for order in event.bids
        ],
        asks=[
            ImlOrderbookLevel(price=Decimal(order.price), size=Decimal(order.size))
            for order in event.asks
        ],
    )

def price_change_event_to_price_change(price_change: PriceChange) -> ImlPriceChangeEvent:
    return ImlPriceChangeEvent(
        venue=Venue.POLYMARKET,
        instrument_id=price_change.token_id,
        timestamp=price_change.timestamp,
        best_bid=Decimal(price_change.best_bid),
        best_ask=Decimal(price_change.best_ask),
    )

